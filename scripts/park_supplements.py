#!/usr/bin/env python3
"""
scripts/park_supplements.py — Move identified non-film files to a Supplements folder.

Reads a source directory, detects supplements/trailers/TV episodes by filename
pattern (using lib/normalizer.py FilenameNormalizer._detect_nonfim()), and moves
them to a designated holding folder.

Dry-run by default — safe to run at any time. Pass --execute to move files.

Usage:
    python scripts/park_supplements.py <source_dir>
    python scripts/park_supplements.py <source_dir> --execute
    python scripts/park_supplements.py <source_dir> --dest /path/to/Supplements
    python scripts/park_supplements.py <source_dir> --execute --dest /path/to/Supplements

Output:
    Dry-run: table of detected non-films grouped by type + counts
    Execute: moves files, reports success/failure per file
"""

import sys
import os
import re
import shutil
import argparse
import logging
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.normalizer import FilenameNormalizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg',
                    '.mpeg', '.wmv', '.ts', '.m2ts'}

# Map nonfim note prefixes to human-readable category names for folder structure
def _nonfim_category(note: str) -> str:
    """Return a folder-name category from the nonfim detection note."""
    if 'nonfim/tv' in note:
        return 'TV Episodes'
    if 'Trailer' in note or 'Teaser' in note or 'Promo' in note or 'TV Spots' in note or 'Radio Spots' in note:
        return 'Trailers'
    return 'Supplements'


def scan_directory(source_dir: Path, normalizer: FilenameNormalizer):
    """
    Walk source_dir and return list of (file_path, nonfim_note) for non-film files.
    """
    detections = []
    for file_path in sorted(source_dir.rglob('*')):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if file_path.name.startswith('._'):
            continue
        stem = file_path.stem
        note = normalizer._detect_nonfim(stem)
        if note:
            detections.append((file_path, note))
    return detections


def print_dry_run(detections, source_dir: Path, dest_root: Path):
    """Print a grouped dry-run report."""
    by_category = defaultdict(list)
    for file_path, note in detections:
        cat = _nonfim_category(note)
        by_category[cat].append((file_path, note))

    total = len(detections)
    print(f"\n{'='*60}")
    print(f"PARK SUPPLEMENTS — DRY RUN")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_root}")
    print(f"Non-film files detected: {total}\n")

    for cat in ['TV Episodes', 'Trailers', 'Supplements']:
        items = by_category.get(cat, [])
        if not items:
            continue
        print(f"  {cat} ({len(items)}):")
        for file_path, note in items:
            rel = file_path.relative_to(source_dir) if file_path.is_relative_to(source_dir) else file_path.name
            print(f"    {rel}")
        print()

    print(f"Run with --execute to move {total} files to {dest_root}")
    print(f"{'='*60}\n")


def execute_moves(detections, source_dir: Path, dest_root: Path):
    """Move detected non-film files to categorised subfolders under dest_root."""
    moved = 0
    failed = 0

    for file_path, note in detections:
        cat = _nonfim_category(note)
        dest_dir = dest_root / cat
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / file_path.name

        # Skip if already at destination
        if dest_path.exists():
            logger.info(f"Already exists at destination, skipping: {file_path.name}")
            continue

        try:
            # Same filesystem: os.rename for instant move; cross-FS: shutil.move
            try:
                if os.stat(file_path).st_dev == os.stat(dest_dir).st_dev:
                    os.rename(file_path, dest_path)
                else:
                    shutil.move(str(file_path), str(dest_path))
            except OSError:
                shutil.move(str(file_path), str(dest_path))

            logger.info(f"Moved [{cat}]: {file_path.name}")
            moved += 1
        except Exception as e:
            logger.error(f"Failed to move {file_path.name}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"PARK SUPPLEMENTS — COMPLETE")
    print(f"{'='*60}")
    print(f"Moved:  {moved}")
    print(f"Failed: {failed}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Detect and park non-film files (supplements, trailers, TV episodes)',
        epilog="""
Dry-run by default. Pass --execute to move files.

Examples:
  python scripts/park_supplements.py /path/to/Unsorted
  python scripts/park_supplements.py /path/to/Unsorted --execute
  python scripts/park_supplements.py /path/to/Unsorted --execute --dest /path/to/Supplements
"""
    )
    parser.add_argument('source_dir', type=Path, help='Directory to scan')
    parser.add_argument('--execute', action='store_true',
                        help='Move files (default: dry-run only)')
    parser.add_argument('--dest', type=Path, default=None,
                        help='Destination root for non-film files '
                             '(default: <source_dir>/Supplements)')
    args = parser.parse_args()

    source_dir = args.source_dir.resolve()
    if not source_dir.is_dir():
        print(f"Error: source directory not found: {source_dir}")
        sys.exit(1)

    dest_root = args.dest.resolve() if args.dest else source_dir / 'Supplements'

    normalizer = FilenameNormalizer()

    print(f"Scanning {source_dir} ...")
    detections = scan_directory(source_dir, normalizer)

    if not detections:
        print("No non-film files detected.")
        return

    if args.execute:
        execute_moves(detections, source_dir, dest_root)
    else:
        print_dry_run(detections, source_dir, dest_root)


if __name__ == '__main__':
    main()
