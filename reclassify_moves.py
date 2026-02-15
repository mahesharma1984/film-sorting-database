#!/usr/bin/env python3
"""
reclassify_moves.py - Move already-organized films to new classifications

Handles the case where films are already in the library structure and need to be
reclassified and moved to new destinations based on improved metadata.

Unlike move.py, this script:
- Searches recursively for files in the library structure
- Compares current location with new destination
- Only moves files that need reclassification
"""

import sys
import csv
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_file_in_tree(filename: str, search_root: Path) -> Optional[Path]:
    """
    Recursively search for a filename in directory tree

    Args:
        filename: Name of file to find (just the filename, not path)
        search_root: Root directory to search from

    Returns:
        Path to file if found, None otherwise
    """
    # Use Path.rglob for recursive search
    matches = list(search_root.rglob(filename))

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0]
    else:
        # Multiple matches - return first one and warn
        logger.warning(f"Multiple matches for {filename}, using first: {matches[0]}")
        return matches[0]


def process_reclassification(
    manifest_path: Path,
    library_base: Path,
    dry_run: bool = True
) -> Dict[str, int]:
    """
    Process manifest and move films that need reclassification

    Args:
        manifest_path: Path to classification manifest CSV
        library_base: Base directory for organized library
        dry_run: If True, only report what would happen

    Returns:
        Statistics dict
    """
    stats = {
        'total': 0,
        'skipped_unsorted': 0,
        'skipped_same_location': 0,
        'skipped_not_found': 0,
        'would_move': 0,
        'moved': 0,
        'errors': 0,
    }

    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats['total'] += 1
            filename = row['filename']
            tier = row['tier']
            new_destination = row['destination']

            # Skip unsorted films
            if tier == 'Unsorted':
                stats['skipped_unsorted'] += 1
                continue

            # Find current location
            current_path = find_file_in_tree(filename, library_base)

            if not current_path:
                stats['skipped_not_found'] += 1
                logger.warning(f"Not found: {filename}")
                continue

            # Build new destination path
            new_dest_dir = library_base / new_destination.strip('/')
            new_dest_path = new_dest_dir / filename

            # Get relative paths for comparison
            current_rel = current_path.relative_to(library_base)
            new_rel = new_dest_path.relative_to(library_base)

            # Check if already at correct location
            if current_path == new_dest_path:
                stats['skipped_same_location'] += 1
                continue

            # File needs to move
            if dry_run:
                print(f"\n[WOULD MOVE] {filename}")
                print(f"  FROM: {current_rel}")
                print(f"  TO:   {new_rel}")
                stats['would_move'] += 1
            else:
                try:
                    # Create destination directory
                    new_dest_dir.mkdir(parents=True, exist_ok=True)

                    # Move file
                    shutil.move(str(current_path), str(new_dest_path))

                    stats['moved'] += 1
                    logger.info(f"Moved: {filename}")
                    logger.info(f"  FROM: {current_rel}")
                    logger.info(f"  TO:   {new_rel}")

                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error moving {filename}: {e}")

    return stats


def print_stats(stats: Dict[str, int], dry_run: bool):
    """Print summary statistics"""
    print("\n" + "=" * 70)
    if dry_run:
        print("DRY RUN SUMMARY (no files were moved)")
    else:
        print("RECLASSIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Total in manifest:         {stats['total']:5d}")
    print(f"  Skipped (unsorted):        {stats['skipped_unsorted']:5d}")
    print(f"  Skipped (same location):   {stats['skipped_same_location']:5d}")
    print(f"  Skipped (not found):       {stats['skipped_not_found']:5d}")

    if dry_run:
        print(f"  Would move:                {stats['would_move']:5d}")
    else:
        print(f"  Moved:                     {stats['moved']:5d}")
        print(f"  Errors:                    {stats['errors']:5d}")

    print("=" * 70)

    if dry_run and stats['would_move'] > 0:
        print(f"\n{stats['would_move']} films would be reclassified")
        print("To execute, run: python reclassify_moves.py --execute")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Move already-organized films to new classifications',
        epilog='SAFETY: Defaults to --dry-run. Pass --execute to actually move files.'
    )
    parser.add_argument('--manifest', type=Path,
                       default=Path('output/full_collection_manifest.csv'),
                       help='Manifest CSV path')
    parser.add_argument('--library', type=Path,
                       default=Path('/Volumes/One Touch/movies/Organized'),
                       help='Library base directory')
    parser.add_argument('--execute', action='store_true',
                       help='Actually move files (default is dry-run)')

    args = parser.parse_args()
    dry_run = not args.execute

    # Verify paths
    if not args.manifest.exists():
        logger.error(f"Manifest not found: {args.manifest}")
        sys.exit(1)

    if not args.library.exists():
        logger.error(f"Library directory not found: {args.library}")
        sys.exit(1)

    # Execute
    if dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN MODE — no files will be moved")
        print("=" * 70 + "\n")
    else:
        print("\n" + "=" * 70)
        print("EXECUTING RECLASSIFICATION MOVES")
        print(f"Library: {args.library}")
        print("=" * 70 + "\n")

    stats = process_reclassification(args.manifest, args.library, dry_run)
    print_stats(stats, dry_run)

    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
