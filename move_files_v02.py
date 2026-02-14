#!/usr/bin/env python3
"""
Move classified films to their destination directories based on v0.2 manifest
"""

import csv
import shutil
from pathlib import Path
from typing import Dict, List


def move_classified_films(
    manifest_path: str,
    source_base: str,
    library_base: str,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Move films from source to library based on classification manifest

    Args:
        manifest_path: Path to sorting_manifest_v02.csv
        source_base: Base directory where source films are located
        library_base: Base directory for organized library
        dry_run: If True, only print what would be done without moving files

    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_processed': 0,
        'moved': 0,
        'skipped_unsorted': 0,
        'skipped_missing': 0,
        'errors': 0
    }

    source_base_path = Path(source_base)
    library_base_path = Path(library_base)

    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats['total_processed'] += 1

            original_filename = row['original_filename']
            tier = row['tier']
            destination = row['destination']
            reason = row['reason']

            # Skip unsorted films
            if tier == 'Unknown' or destination == 'Unknown':
                stats['skipped_unsorted'] += 1
                continue

            # Build source and destination paths
            source_file = source_base_path / original_filename
            dest_dir = library_base_path / destination
            dest_file = dest_dir / original_filename

            # Check if source exists
            if not source_file.exists():
                print(f"⚠️  Source not found: {source_file}")
                stats['skipped_missing'] += 1
                continue

            # Perform move
            try:
                if dry_run:
                    print(f"[DRY RUN] Would move:")
                    print(f"  From: {source_file}")
                    print(f"  To:   {dest_file}")
                    print(f"  Tier: {tier} | Reason: {reason}")
                    stats['moved'] += 1
                else:
                    # Create destination directory if needed
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    # Move the file
                    shutil.move(str(source_file), str(dest_file))

                    print(f"✓ Moved: {original_filename}")
                    print(f"  → {destination}")
                    stats['moved'] += 1

            except Exception as e:
                print(f"✗ Error moving {original_filename}: {e}")
                stats['errors'] += 1

    return stats


def print_stats(stats: Dict[str, int]):
    """Print summary statistics"""
    print("\n" + "=" * 60)
    print("MOVE SUMMARY")
    print("=" * 60)
    print(f"Total processed:     {stats['total_processed']:4d}")
    print(f"Files moved:         {stats['moved']:4d}")
    print(f"Skipped (unsorted):  {stats['skipped_unsorted']:4d}")
    print(f"Skipped (missing):   {stats['skipped_missing']:4d}")
    print(f"Errors:              {stats['errors']:4d}")
    print("=" * 60)


def main():
    """Main entry point"""
    import sys

    # Configuration
    manifest_path = "output/sorting_manifest_v02.csv"
    source_base = "/Volumes/One Touch/Movies/Organized/Unsorted"
    library_base = "/Volumes/One Touch/Movies/Organized"

    # Check if dry-run mode
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN MODE - No files will be moved")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("MOVING FILES - This will reorganize your collection")
        print("=" * 60 + "\n")

        # Confirm before proceeding
        response = input("Proceed with file moves? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            return 1

    # Execute moves
    stats = move_classified_films(
        manifest_path=manifest_path,
        source_base=source_base,
        library_base=library_base,
        dry_run=dry_run
    )

    # Print summary
    print_stats(stats)

    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
