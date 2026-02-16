#!/usr/bin/env python3
"""
migrate_structure.py - Migrate films from decade-first to tier-first structure

OLD (decade-first):
  1960s/Core/Jean-Luc Godard/film.mkv
  1960s/Reference/film.mkv
  1960s/Popcorn/film.mkv

NEW (tier-first):
  Core/1960s/Jean-Luc Godard/film.mkv
  Reference/1960s/film.mkv
  Popcorn/1960s/film.mkv

NOTE: Satellite is already tier-first, so no migration needed.
"""

import sys
import os
import shutil
import logging
import argparse
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_decade_folder(name: str) -> bool:
    """Check if folder name is a decade (e.g., '1960s')"""
    return name.endswith('s') and len(name) == 5 and name[:-1].isdigit()


def find_files_to_migrate(library_path: Path) -> List[Tuple[Path, Path]]:
    """
    Find all files in decade-first structure and determine new tier-first paths.

    Returns:
        List of (source_path, dest_path) tuples
    """
    migrations = []

    # Look for decade folders at root level
    for item in library_path.iterdir():
        if not item.is_dir():
            continue

        if not is_decade_folder(item.name):
            continue

        decade = item.name
        logger.info(f"Scanning decade folder: {decade}")

        # Look for tier folders within decade
        for tier_dir in item.iterdir():
            if not tier_dir.is_dir():
                continue

            tier = tier_dir.name

            # Migrate Core, Reference, Popcorn, and Satellite
            if tier not in ('Core', 'Reference', 'Popcorn', 'Satellite'):
                continue

            # Find all files in this tier/decade combo
            for file_path in tier_dir.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('._'):
                    # Calculate relative path within tier directory
                    rel_path = file_path.relative_to(tier_dir)

                    # For Satellite: Decade/Satellite/Category/file → Satellite/Category/Decade/file
                    if tier == 'Satellite':
                        # rel_path is Category/file
                        parts = rel_path.parts
                        if len(parts) >= 2:
                            category = parts[0]
                            rest = Path(*parts[1:])
                            new_path = library_path / 'Satellite' / category / decade / rest
                        else:
                            # Fallback for unexpected structure
                            new_path = library_path / tier / decade / rel_path
                    else:
                        # For Core, Reference, Popcorn: Tier/Decade/[subdirectories]/file
                        new_path = library_path / tier / decade / rel_path

                    migrations.append((file_path, new_path))

    return migrations


def migrate_file(source: Path, dest: Path, dry_run: bool = True) -> bool:
    """
    Migrate a single file from source to dest.

    Args:
        source: Source file path
        dest: Destination file path
        dry_run: If True, only show what would happen

    Returns:
        True if successful (or would be successful in dry-run)
    """
    if dry_run:
        print(f"[DRY RUN] Would move:")
        print(f"  FROM: {source.relative_to(source.parents[4])}")
        print(f"  TO:   {dest.relative_to(dest.parents[3])}")
        return True
    else:
        try:
            # Create destination directory
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source), str(dest))
            logger.info(f"Moved: {source.name} -> {dest.relative_to(dest.parents[3])}")
            return True
        except Exception as e:
            logger.error(f"Error migrating {source.name}: {e}")
            return False


def cleanup_empty_dirs(library_path: Path, dry_run: bool = True):
    """Remove empty decade-first directories after migration"""
    for item in library_path.iterdir():
        if not item.is_dir():
            continue

        if not is_decade_folder(item.name):
            continue

        # Check if decade folder is empty (or only contains tier folders that are empty)
        try:
            # Try to remove decade folder (will only succeed if empty)
            if not dry_run:
                # Remove empty subdirectories first
                for root, dirs, files in os.walk(item, topdown=False):
                    for dir_name in dirs:
                        dir_path = Path(root) / dir_name
                        try:
                            dir_path.rmdir()  # Only removes if empty
                            logger.info(f"Removed empty directory: {dir_path.relative_to(library_path)}")
                        except OSError:
                            pass  # Not empty, skip

                # Try to remove decade folder
                item.rmdir()
                logger.info(f"Removed empty decade folder: {item.name}")
            else:
                # Check if it would be empty
                has_files = any(item.rglob('*'))
                if not has_files:
                    print(f"[DRY RUN] Would remove empty folder: {item.name}")
        except OSError:
            pass  # Not empty, that's fine


def main():
    parser = argparse.ArgumentParser(
        description='Migrate films from decade-first to tier-first structure',
        epilog="""
SAFETY: Defaults to --dry-run. You must pass --execute to actually move files.

Examples:
  python migrate_structure.py /Volumes/One\ Touch/Movies/Organized
  python migrate_structure.py /Volumes/One\ Touch/Movies/Organized --execute
        """
    )
    parser.add_argument('library_path', type=Path,
                       help='Path to organized library (e.g., /Volumes/One Touch/Movies/Organized)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually move files (default is dry-run)')

    args = parser.parse_args()

    # Validate library path
    if not args.library_path.exists():
        logger.error(f"Library path not found: {args.library_path}")
        sys.exit(1)

    dry_run = not args.execute

    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN MODE — no files will be moved")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("EXECUTING MIGRATION")
        print(f"Library: {args.library_path}")
        print("=" * 60 + "\n")

    # Find all files to migrate
    logger.info("Scanning for files to migrate...")
    migrations = find_files_to_migrate(args.library_path)

    if not migrations:
        print("\n✅ No files to migrate! Structure is already tier-first.")
        return 0

    print(f"\nFound {len(migrations)} files to migrate\n")

    # Migrate files
    success_count = 0
    error_count = 0

    for source, dest in migrations:
        if migrate_file(source, dest, dry_run):
            success_count += 1
        else:
            error_count += 1

    # Cleanup empty directories
    if success_count > 0:
        logger.info("Cleaning up empty directories...")
        cleanup_empty_dirs(args.library_path, dry_run)

    # Print summary
    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN SUMMARY")
    else:
        print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"  Files to migrate:    {len(migrations):5d}")
    print(f"  {'Would migrate' if dry_run else 'Migrated'}:        {success_count:5d}")
    print(f"  Errors:              {error_count:5d}")
    print("=" * 60)

    if dry_run:
        print("\nTo execute migration, run again with --execute")
    else:
        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("  1. Re-run classification to generate new manifest")
        print("  2. Run move.py --execute for any new files")

    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
