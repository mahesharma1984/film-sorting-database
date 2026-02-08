#!/usr/bin/env python3
"""
move.py - Move files based on sorting manifest

Pure PRECISION operation. Never classifies. Just reads manifest and moves.

Key features:
- Same-filesystem detection (os.rename vs shutil.copy2)
- Safety mechanisms (verify before delete, cleanup on failure)
- Dry-run mode (default)
- Resumability (skip files already at destination)
"""

import os
import sys
import csv
import shutil
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileMover:
    """File mover with same-filesystem optimization"""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.stats = {
            'success': 0,
            'error': 0,
            'skipped': 0,
            'renamed_moves': 0,
            'copied_moves': 0
        }

    def _is_same_filesystem(self, source: Path, dest: Path) -> bool:
        """
        Check if source and destination are on same filesystem

        Uses st_dev comparison - if device IDs match, it's the same filesystem
        and we can use os.rename() for instant moves.
        """
        try:
            # Ensure destination parent exists for stat
            if not dest.parent.exists():
                return False

            return source.stat().st_dev == dest.parent.stat().st_dev

        except Exception as e:
            logger.debug(f"Could not determine filesystem: {e}")
            return False  # Assume cross-filesystem for safety

    def move_file(self, source_file: Path, dest_file: Path) -> bool:
        """
        Move file using os.rename() or shutil.copy2() based on filesystem

        Returns True if successful, False otherwise
        """

        if self.dry_run:
            logger.info(f"DRY RUN: {source_file.name} → {dest_file}")
            return True

        # Validate source exists
        if not source_file.exists():
            logger.error(f"Source not found: {source_file}")
            return False

        # Create destination directory
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        # Handle duplicate filenames
        counter = 1
        original_dest = dest_file
        while dest_file.exists():
            # Check if it's the same file (resumability)
            if dest_file.stat().st_size == source_file.stat().st_size:
                logger.info(f"⊙ Already exists (skipping): {source_file.name}")
                self.stats['skipped'] += 1
                return True

            # Different file with same name - append counter
            stem = original_dest.stem
            suffix = original_dest.suffix
            dest_file = dest_file.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        try:
            if self._is_same_filesystem(source_file, dest_file):
                # FAST: Atomic rename (2-5 minutes for 1201 files)
                os.rename(str(source_file), str(dest_file))
                logger.info(f"✓ Renamed: {source_file.name}")
                self.stats['renamed_moves'] += 1

            else:
                # SAFE: Copy + verify + delete (60-80 hours for cross-device)
                shutil.copy2(str(source_file), str(dest_file))

                # Verify copy
                if dest_file.exists() and dest_file.stat().st_size == source_file.stat().st_size:
                    source_file.unlink()  # Delete original only after verification
                    logger.info(f"✓ Copied: {source_file.name}")
                    self.stats['copied_moves'] += 1
                else:
                    logger.error(f"Copy verification failed: {dest_file}")
                    if dest_file.exists():
                        dest_file.unlink()  # Clean up failed copy
                    return False

            return True

        except Exception as e:
            logger.error(f"Error moving {source_file}: {e}")
            return False

    def process_manifest(self, manifest_path: Path, source_dir: Path):
        """Read manifest and move all files"""

        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return False

        # Read manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        logger.info(f"Processing {len(entries)} entries from manifest")

        if self.dry_run:
            logger.info("=" * 60)
            logger.info("DRY RUN MODE - No files will be moved")
            logger.info("=" * 60)
        else:
            logger.warning("EXECUTE MODE - Files will be moved!")

        # Process each entry
        for i, entry in enumerate(entries, 1):
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(entries)}")

            filename = entry['filename']  # Now stores relative path from source_dir
            destination = entry['destination']

            source_file = source_dir / filename
            # Destination should use just the filename, not the full relative path
            dest_file = Path(destination) / Path(filename).name

            if self.move_file(source_file, dest_file):
                self.stats['success'] += 1
            else:
                self.stats['error'] += 1

        return True

    def print_statistics(self):
        """Print move statistics"""

        print("\n" + "=" * 60)
        print("MOVE STATISTICS")
        print("=" * 60)

        total = self.stats['success'] + self.stats['error']

        if self.dry_run:
            print(f"  Mode: DRY RUN (no files moved)")
        else:
            print(f"  Mode: EXECUTE")

        print(f"  Total entries: {total}")
        print(f"  Successful: {self.stats['success']}")
        print(f"  Errors: {self.stats['error']}")
        print(f"  Skipped (already at dest): {self.stats['skipped']}")

        if not self.dry_run:
            print(f"\n  Renamed (same-FS): {self.stats['renamed_moves']}")
            print(f"  Copied (cross-FS): {self.stats['copied_moves']}")

            if self.stats['renamed_moves'] > 0 and self.stats['copied_moves'] > 0:
                print(f"\n  Performance: Mix of instant renames and byte copies")
            elif self.stats['renamed_moves'] > 0:
                print(f"\n  Performance: All same-filesystem (instant renames)")
            elif self.stats['copied_moves'] > 0:
                print(f"\n  Performance: All cross-filesystem (byte copies)")

        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Move films using sorting manifest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default - no files moved)
  python move.py output/sorting_manifest.csv "/Volumes/One Touch/movies/unsorted"

  # Execute moves
  python move.py output/sorting_manifest.csv "/Volumes/One Touch/movies/unsorted" --execute

Performance:
  - Same filesystem: uses os.rename() for instant moves (2-5 minutes)
  - Cross filesystem: uses shutil.copy2() + verify + delete (60-80 hours)

Safety:
  - Verifies copies before deleting source
  - Cleans up failed copies
  - Skips files already at destination (resumable)
  - Dry-run mode by default
        """
    )
    parser.add_argument('manifest', help='Path to sorting_manifest.csv')
    parser.add_argument('source_dir', help='Source directory containing films')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview moves without executing (default)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually move files (overrides --dry-run)')

    args = parser.parse_args()

    # Determine mode
    dry_run = not args.execute

    # Check paths
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        sys.exit(1)

    source_path = Path(args.source_dir)
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_path}")
        sys.exit(1)

    # Initialize mover
    mover = FileMover(dry_run=dry_run)

    # Process manifest
    try:
        success = mover.process_manifest(manifest_path, source_path)

        # Print statistics
        mover.print_statistics()

        if success:
            if dry_run:
                logger.info("Dry run completed! Review above, then run with --execute to move files.")
            else:
                logger.info("Move completed!")
        else:
            logger.error("Move failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Move failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
