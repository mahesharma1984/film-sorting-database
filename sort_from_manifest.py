#!/usr/bin/env python3
"""
Sort films based on an existing manifest CSV
Avoids re-running API calls by using pre-computed sorting decisions
"""

import sys
import csv
import shutil
import logging
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_manifest(manifest_path: Path) -> list:
    """Read sorting manifest CSV"""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def move_file_safely(source_file: Path, dest_file: Path, dry_run: bool = False) -> bool:
    """Safely move file with copy+verify+delete for external drives"""

    if dry_run:
        logger.info(f"DRY RUN: Would move {source_file} -> {dest_file}")
        return True

    # Check source exists
    if not source_file.exists():
        logger.error(f"Source file not found: {source_file}")
        return False

    # Create destination directory
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    # Handle duplicate filenames
    counter = 1
    original_dest = dest_file
    while dest_file.exists():
        stem = original_dest.stem
        suffix = original_dest.suffix
        dest_file = dest_file.parent / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        # Copy file
        shutil.copy2(str(source_file), str(dest_file))

        # Verify copy succeeded
        if dest_file.exists() and dest_file.stat().st_size == source_file.stat().st_size:
            # Delete original only after successful copy
            source_file.unlink()
            logger.info(f"✓ Moved {source_file.name} -> {dest_file}")
            return True
        else:
            logger.error(f"Copy verification failed: {dest_file}")
            if dest_file.exists():
                dest_file.unlink()  # Clean up failed copy
            return False

    except Exception as e:
        logger.error(f"Error moving {source_file}: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sort films using manifest CSV')
    parser.add_argument('manifest', help='Path to sorting_manifest.csv')
    parser.add_argument('source_dir', help='Source directory with unsorted films')
    parser.add_argument('--dry-run', action='store_true', help='Preview moves without executing')

    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    source_dir = Path(args.source_dir)

    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        sys.exit(1)

    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        sys.exit(1)

    # Read manifest
    logger.info(f"Reading manifest: {manifest_path}")
    entries = read_manifest(manifest_path)
    logger.info(f"Found {len(entries)} entries in manifest")

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be moved")

    # Process each entry
    success_count = 0
    error_count = 0

    for entry in entries:
        filename = entry['filename']
        destination = entry['destination']

        source_file = source_dir / filename
        dest_file = Path(destination) / filename

        if move_file_safely(source_file, dest_file, args.dry_run):
            success_count += 1
        else:
            error_count += 1

    # Summary
    logger.info("=" * 60)
    logger.info(f"COMPLETE - Successfully moved: {success_count}, Errors: {error_count}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
