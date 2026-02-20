#!/usr/bin/env python3
"""
normalize.py — Filename normalization pre-stage (Issue #18)

Pure PRECISION operation.  Cleans dirty filenames before classify.py runs.
Never assigns tiers, calls APIs, or modifies SORTING_DATABASE.md.

Pipeline position:
  scaffold.py  →  normalize.py  →  classify.py  →  move.py

Safety:
  - Dry-run is the DEFAULT.  Pass --execute to apply renames.
  - Hard gate: source directory must exist (drive must be mounted).
  - Only renames files whose change_type != 'unchanged' and != 'flag_nonfim'.
  - nonfim files are flagged in the manifest but NEVER renamed.
  - Human review of rename_manifest.csv is expected before --execute.

Usage:
  python normalize.py <source_dir>                     # dry-run, write manifest
  python normalize.py <source_dir> --execute           # apply renames
  python normalize.py <source_dir> --nonfim-only       # show nonfim flags only
  python normalize.py <source_dir> --output PATH       # custom manifest path
"""

import sys
import os
import csv
import logging
import argparse
from collections import Counter
from pathlib import Path

from lib.normalizer import FilenameNormalizer, NormalizationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.wmv', '.flv', '.ts', '.m2ts'}


def scan_directory(source_dir: Path) -> list[Path]:
    """Return all video files in source_dir (non-recursive)."""
    return sorted(
        f for f in source_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() in VIDEO_EXTENSIONS
        and not f.name.startswith('._')  # skip macOS resource fork sidecars
    )


def run_normalize(
    source_dir: Path,
    output_path: Path,
    dry_run: bool = True,
    nonfim_only: bool = False,
) -> Counter:
    """
    Scan source_dir, normalize all filenames, write rename_manifest.csv.

    Args:
        source_dir:  Directory containing source video files
        output_path: Path to write rename_manifest.csv
        dry_run:     If True, report only (no renames applied)
        nonfim_only: If True, only output flag_nonfim rows to manifest

    Returns:
        Counter of change_type values across all files
    """
    normalizer = FilenameNormalizer()
    files = scan_directory(source_dir)
    stats: Counter = Counter()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=['original_filename', 'cleaned_filename', 'change_type', 'notes']
        )
        writer.writeheader()

        for file_path in files:
            result = normalizer.normalize(file_path.name)
            stats[result.change_type] += 1

            # Filter rows for --nonfim-only mode
            if nonfim_only and result.change_type != 'flag_nonfim':
                continue

            writer.writerow({
                'original_filename': result.original_filename,
                'cleaned_filename': result.cleaned_filename,
                'change_type': result.change_type,
                'notes': result.notes,
            })

            # Apply rename if --execute and file actually needs renaming
            if (
                not dry_run
                and result.change_type not in ('unchanged', 'flag_nonfim')
                and result.cleaned_filename != result.original_filename
            ):
                old_path = source_dir / result.original_filename
                new_path = source_dir / result.cleaned_filename

                if new_path.exists() and new_path != old_path:
                    logger.warning(
                        f"SKIP (dest exists): {result.original_filename} → {result.cleaned_filename}"
                    )
                    stats['skipped_dest_exists'] += 1
                    continue

                try:
                    os.rename(old_path, new_path)
                    logger.info(f"RENAMED: {result.original_filename} → {result.cleaned_filename}")
                    stats['renamed'] += 1
                except OSError as e:
                    logger.error(f"FAILED rename {result.original_filename}: {e}")
                    stats['errors'] += 1

    return stats


def print_summary(stats: Counter, dry_run: bool, output_path: Path, nonfim_only: bool) -> None:
    """Print a human-readable summary of normalization results."""
    print()
    print("=" * 60)
    if dry_run:
        print("DRY RUN — no files were renamed")
    else:
        print("NORMALIZATION COMPLETE")
    print("=" * 60)

    total = sum(v for k, v in stats.items() if k in (
        'unchanged', 'strip_junk', 'normalize_edition', 'fix_year', 'flag_nonfim'
    ))
    print(f"\nFiles scanned:       {total}")
    print(f"  unchanged:         {stats['unchanged']}")
    print(f"  strip_junk:        {stats['strip_junk']}")
    print(f"  fix_year:          {stats['fix_year']}")
    print(f"  normalize_edition: {stats['normalize_edition']}")
    print(f"  flag_nonfim:       {stats['flag_nonfim']}")

    changes = stats['strip_junk'] + stats['fix_year'] + stats['normalize_edition']
    if changes > 0:
        print(f"\nTotal files to rename: {changes}")

    if not dry_run:
        print(f"  renamed:           {stats.get('renamed', 0)}")
        print(f"  skipped:           {stats.get('skipped_dest_exists', 0)}")
        print(f"  errors:            {stats.get('errors', 0)}")

    if nonfim_only:
        print(f"\nManifest (nonfim only): {output_path}")
    else:
        print(f"\nManifest written to:  {output_path}")

    if dry_run and changes > 0:
        print("\nReview the manifest, then run with --execute to apply renames.")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Normalize film filenames before classification (dry-run by default)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'source_dir',
        type=Path,
        help='Directory containing source video files to normalize',
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        default=False,
        help='Apply renames (default: dry-run only)',
    )
    parser.add_argument(
        '--nonfim-only',
        action='store_true',
        default=False,
        dest='nonfim_only',
        help='Write only flag_nonfim rows to the manifest',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('output/rename_manifest.csv'),
        help='Output path for rename_manifest.csv (default: output/rename_manifest.csv)',
    )

    args = parser.parse_args()
    dry_run = not args.execute

    # Hard gate: source directory must exist (drive must be mounted)
    if not args.source_dir.exists():
        logger.error(f"Source directory not found: {args.source_dir}")
        logger.error("Is the source drive mounted?")
        return 1

    if not args.source_dir.is_dir():
        logger.error(f"Not a directory: {args.source_dir}")
        return 1

    if dry_run:
        print()
        print("=" * 60)
        print("DRY RUN MODE — no files will be renamed")
        print(f"Source:   {args.source_dir}")
        print(f"Manifest: {args.output}")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("EXECUTING RENAMES")
        print(f"Source:   {args.source_dir}")
        print(f"Manifest: {args.output}")
        print("=" * 60)

    stats = run_normalize(
        source_dir=args.source_dir,
        output_path=args.output,
        dry_run=dry_run,
        nonfim_only=args.nonfim_only,
    )

    print_summary(stats, dry_run, args.output, args.nonfim_only)

    return 0 if stats.get('errors', 0) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
