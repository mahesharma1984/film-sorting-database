#!/usr/bin/env python3
"""
audit.py - Library Audit: Walk organized library and generate inventory CSV

Pure PRECISION. Zero reasoning. Read-only. Never moves files.

Walks the organized library folder structure and generates a manifest CSV
compatible with dashboard.py. Derives tier/decade/subdirectory from the
folder path — no classification logic, no API calls.

Output: output/library_audit.csv
Load in dashboard by selecting library_audit.csv from the manifest picker.

Usage:
    python audit.py                           # uses config_external.yaml
    python audit.py --library /path/to/lib   # explicit library path
    python audit.py --output output/my.csv   # custom output path
"""

import sys
import csv
import re
import argparse
import yaml
from pathlib import Path

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg', '.mpeg', '.wmv', '.ts'}

DECADE_RE = re.compile(r'^\d{4}s$')
YEAR_RE = re.compile(r'\((\d{4})\)')

# Folders to skip entirely (no films here)
SKIP_FOLDERS = {'Out', '.Trash', '.Spotlight-V100', '.fseventsd', '.TemporaryItems'}

# Decision-pending curator folders → treat as Staging
DECISION_PENDING = {'Core (Gallo) OR Popcorn?', 'Reference OR Popcorn?'}

FIELDNAMES = [
    'filename', 'title', 'year', 'director', 'language', 'country',
    'user_tag', 'tier', 'decade', 'subdirectory', 'destination',
    'confidence', 'reason',
]


def is_video_file(path: Path) -> bool:
    return (
        path.suffix.lower() in VIDEO_EXTENSIONS
        and not path.name.startswith('._')
    )


def extract_year(filename: str) -> str:
    """Best-effort year extraction from (YYYY) parenthetical."""
    m = YEAR_RE.search(filename)
    if m:
        year = int(m.group(1))
        if 1920 <= year <= 2029:
            return str(year)
    return ''


def derive_row(file_path: Path, library_base: Path) -> dict | None:
    """
    Derive manifest row from filesystem path. Returns None to skip.

    Path conventions:
      Core/{decade}/{director}/file
      Reference/{decade}/file
      Satellite/{category}/{decade}/file
      Popcorn/{decade}/file
      Unsorted/file
      Staging/{subfolder}/file
    """
    rel = file_path.relative_to(library_base)
    parts = rel.parts
    if not parts:
        return None

    top = parts[0]
    filename = file_path.name

    # --- Skip ---
    if top in SKIP_FOLDERS:
        return None

    # --- Out/Cut: archived, not part of active library ---
    if top == 'Out':
        return None

    # --- Decision-pending folders → Staging ---
    if top in DECISION_PENDING:
        return {
            'filename': filename,
            'tier': 'Staging',
            'decade': '',
            'subdirectory': top,
            'destination': str(rel.parent).replace('\\', '/') + '/',
            'reason': 'audit_decision_pending',
            'confidence': '0.5',
        }

    # --- Staging/{subfolder}/file ---
    if top == 'Staging':
        subfolder = parts[1] if len(parts) > 2 else ''
        return {
            'filename': filename,
            'tier': 'Staging',
            'decade': '',
            'subdirectory': subfolder,
            'destination': str(rel.parent).replace('\\', '/') + '/',
            'reason': 'audit_staging',
            'confidence': '0.5',
        }

    # --- Unsorted/file ---
    if top == 'Unsorted':
        return {
            'filename': filename,
            'tier': 'Unsorted',
            'decade': '',
            'subdirectory': '',
            'destination': 'Unsorted/',
            'reason': 'audit_unsorted',
            'confidence': '0.0',
        }

    # --- Core/{decade}/{director}/file ---
    if top == 'Core':
        decade = parts[1] if len(parts) > 2 and DECADE_RE.match(parts[1]) else ''
        director = parts[2] if len(parts) > 3 else ''
        destination = f'Core/{decade}/{director}/' if director else f'Core/{decade}/'
        return {
            'filename': filename,
            'tier': 'Core',
            'decade': decade,
            'subdirectory': director,
            'destination': destination,
            'reason': 'audit_filesystem',
            'confidence': '1.0',
        }

    # --- Reference/{decade}/file ---
    if top == 'Reference':
        decade = parts[1] if len(parts) > 2 and DECADE_RE.match(parts[1]) else ''
        return {
            'filename': filename,
            'tier': 'Reference',
            'decade': decade,
            'subdirectory': '',
            'destination': f'Reference/{decade}/',
            'reason': 'audit_filesystem',
            'confidence': '1.0',
        }

    # --- Satellite/{category}/{decade}/file ---
    if top == 'Satellite':
        category = parts[1] if len(parts) > 2 else ''
        decade = parts[2] if len(parts) > 3 and DECADE_RE.match(parts[2]) else ''
        destination = f'Satellite/{category}/{decade}/' if decade else f'Satellite/{category}/'
        return {
            'filename': filename,
            'tier': 'Satellite',
            'decade': decade,
            'subdirectory': category,
            'destination': destination,
            'reason': 'audit_filesystem',
            'confidence': '1.0',
        }

    # --- Popcorn/{decade}/file ---
    if top == 'Popcorn':
        decade = parts[1] if len(parts) > 2 and DECADE_RE.match(parts[1]) else ''
        return {
            'filename': filename,
            'tier': 'Popcorn',
            'decade': decade,
            'subdirectory': '',
            'destination': f'Popcorn/{decade}/',
            'reason': 'audit_filesystem',
            'confidence': '1.0',
        }

    # --- Unknown top-level folder → Staging ---
    return {
        'filename': filename,
        'tier': 'Staging',
        'decade': '',
        'subdirectory': top,
        'destination': str(rel.parent).replace('\\', '/') + '/',
        'reason': 'audit_unknown_folder',
        'confidence': '0.5',
    }


def main():
    parser = argparse.ArgumentParser(
        description='Walk organized library and generate inventory CSV for dashboard',
        epilog='Output: output/library_audit.csv\n'
               'Load in dashboard by selecting library_audit.csv from the manifest picker.'
    )
    parser.add_argument('--library', '-l', type=Path, default=None,
                        help='Library base path (default: from config)')
    parser.add_argument('--output', '-o', type=Path,
                        default=Path('output/library_audit.csv'),
                        help='Output CSV path (default: output/library_audit.csv)')
    parser.add_argument('--config', type=Path, default=Path('config_external.yaml'),
                        help='Config file (default: config_external.yaml)')
    args = parser.parse_args()

    # Resolve library path from config if not provided
    library_base = args.library
    if library_base is None:
        if args.config.exists():
            with open(args.config) as f:
                config = yaml.safe_load(f)
            library_base = Path(config.get('library_path', ''))
        if not library_base or not library_base.exists():
            print(f"Error: library path not found. Pass --library or check {args.config}")
            sys.exit(1)

    if not library_base.exists():
        print(f"Error: library not found: {library_base}")
        sys.exit(1)

    print(f"Auditing library: {library_base}")
    print("Scanning files...")

    rows = []
    skipped_out = 0

    for file_path in sorted(library_base.rglob('*')):
        if not file_path.is_file():
            continue
        if not is_video_file(file_path):
            continue

        row = derive_row(file_path, library_base)
        if row is None:
            skipped_out += 1
            continue

        row['year'] = extract_year(file_path.name)

        # Fill dashboard-required columns with empty strings
        for col in FIELDNAMES:
            row.setdefault(col, '')

        rows.append(row)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, fieldnames=FIELDNAMES,
            quoting=csv.QUOTE_ALL,
            extrasaction='ignore',
        )
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    tier_counts = {}
    for row in rows:
        t = row['tier']
        tier_counts[t] = tier_counts.get(t, 0) + 1

    total = len(rows)
    classified = sum(v for k, v in tier_counts.items() if k not in ('Unsorted', 'Staging'))
    classified_pct = classified / total * 100 if total else 0

    print(f"\n{'=' * 50}")
    print(f"LIBRARY AUDIT COMPLETE")
    print(f"{'=' * 50}")
    for tier in ['Core', 'Reference', 'Satellite', 'Popcorn', 'Staging', 'Unsorted']:
        count = tier_counts.get(tier, 0)
        print(f"  {tier:<14} {count:5d}")
    print(f"  {'TOTAL':<14} {total:5d}")
    print(f"\n  Classified:     {classified_pct:.1f}%  ({classified}/{total})")
    if skipped_out:
        print(f"  Skipped (Out):  {skipped_out}")
    print(f"\nOutput: {args.output}")
    print("Load in dashboard: select library_audit.csv from the manifest picker.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
