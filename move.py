#!/usr/bin/env python3
"""
move.py - Move classified films to destination directories (v1.0)

Pure PRECISION operation. Reads manifest CSV, moves files. Never classifies.

Safety:
- --dry-run is the DEFAULT (must pass --execute to actually move)
- Same-filesystem detection: os.rename() for instant moves
- Cross-filesystem: shutil.copy2() + verify + delete source
- Resumable: skips files already at destination
- Hard gate: source file must exist, destination parent must be writable
"""

import sys
import os
import csv
import shutil
import logging
import argparse
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def same_filesystem(path_a: Path, path_b: Path) -> bool:
    """Check if two paths are on the same filesystem"""
    try:
        return os.stat(path_a).st_dev == os.stat(path_b).st_dev
    except OSError:
        return False


def move_file(source: Path, dest: Path, use_rename: bool) -> bool:
    """
    Move a single file from source to dest.

    Args:
        source: Source file path
        dest: Destination file path
        use_rename: If True, use os.rename (same FS, instant).
                    If False, use shutil.copy2 + verify + delete (cross FS).

    Returns:
        True if successful, False otherwise
    """
    # Create destination directory
    dest.parent.mkdir(parents=True, exist_ok=True)

    if use_rename:
        os.rename(source, dest)
        return True
    else:
        # Cross-filesystem: copy, verify, delete
        shutil.copy2(str(source), str(dest))

        # Verify: destination exists and size matches
        if dest.exists() and dest.stat().st_size == source.stat().st_size:
            source.unlink()
            return True
        else:
            logger.error(f"Verification failed: {dest} (size mismatch or missing)")
            if dest.exists():
                dest.unlink()  # Clean up failed copy
            return False


def process_manifest(
    manifest_path: Path,
    source_base: Path,
    library_base: Path,
    dry_run: bool = True
) -> Dict[str, int]:
    """
    Process manifest and move (or dry-run) files.

    Args:
        manifest_path: Path to sorting_manifest.csv
        source_base: Base directory where source films are located
        library_base: Base directory for organized library
        dry_run: If True, only report what would happen

    Returns:
        Statistics dict
    """
    stats = {
        'total': 0,
        'moved': 0,
        'skipped_unsorted': 0,
        'skipped_exists': 0,
        'skipped_missing': 0,
        'errors': 0,
    }

    # Detect same-filesystem for optimization
    use_rename = False
    if not dry_run and source_base.exists() and library_base.exists():
        use_rename = same_filesystem(source_base, library_base)
        if use_rename:
            logger.info(f"Same filesystem detected — using os.rename() (instant)")
        else:
            logger.info(f"Cross-filesystem detected — using shutil.copy2() (slower)")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats['total'] += 1
            filename = row['filename']
            tier = row['tier']
            destination = row['destination']

            # Skip unsorted films
            if tier == 'Unsorted':
                stats['skipped_unsorted'] += 1
                continue

            # Build paths
            source_file = source_base / filename
            dest_dir = library_base / destination.strip('/')
            dest_file = dest_dir / Path(filename).name

            # Check if already at destination (resumable)
            if dest_file.exists():
                stats['skipped_exists'] += 1
                logger.debug(f"Already exists: {dest_file}")
                continue

            # Check source exists
            if not source_file.exists():
                stats['skipped_missing'] += 1
                logger.warning(f"Source not found: {source_file}")
                continue

            # Execute or dry-run
            if dry_run:
                print(f"[DRY RUN] {filename}")
                print(f"  -> {destination}")
                stats['moved'] += 1
            else:
                try:
                    success = move_file(source_file, dest_file, use_rename)
                    if success:
                        stats['moved'] += 1
                        logger.info(f"Moved: {filename} -> {destination}")
                    else:
                        stats['errors'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error moving {filename}: {e}")

    return stats


def print_stats(stats: Dict[str, int], dry_run: bool):
    """Print summary statistics"""
    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN SUMMARY (no files were moved)")
    else:
        print("MOVE SUMMARY")
    print("=" * 60)
    print(f"  Total in manifest:   {stats['total']:5d}")
    print(f"  {'Would move' if dry_run else 'Moved'}:          {stats['moved']:5d}")
    print(f"  Skipped (unsorted):  {stats['skipped_unsorted']:5d}")
    print(f"  Skipped (exists):    {stats['skipped_exists']:5d}")
    print(f"  Skipped (missing):   {stats['skipped_missing']:5d}")
    print(f"  Errors:              {stats['errors']:5d}")
    print("=" * 60)

    if dry_run:
        print("\nTo execute, run again with --execute")


def main():
    parser = argparse.ArgumentParser(
        description='Move classified films to destination directories (v1.0)',
        epilog="""
SAFETY: Defaults to --dry-run. You must pass --execute to actually move files.

Examples:
  python move.py                           # Dry run with defaults
  python move.py --execute                 # Actually move files
  python move.py --manifest output/sorting_manifest.csv --execute
        """
    )
    parser.add_argument('--manifest', '-m', type=Path,
                       default=Path('output/sorting_manifest.csv'),
                       help='Manifest CSV path (default: output/sorting_manifest.csv)')
    parser.add_argument('--source', '-s', type=Path, default=None,
                       help='Source directory (default: from config)')
    parser.add_argument('--library', '-l', type=Path, default=None,
                       help='Library base directory (default: from config)')
    parser.add_argument('--config', type=Path, default=Path('config_external.yaml'),
                       help='Configuration file (default: config_external.yaml)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually move files (default is dry-run)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Show what would be done without moving (default)')

    args = parser.parse_args()

    # If --execute is passed, disable dry-run
    dry_run = not args.execute

    # Check manifest exists
    if not args.manifest.exists():
        logger.error(f"Manifest not found: {args.manifest}")
        sys.exit(1)

    # Get paths from config if not provided
    source_base = args.source
    library_base = args.library

    if source_base is None or library_base is None:
        if not args.config.exists():
            logger.error(f"Config file not found: {args.config}")
            logger.error("Provide --source and --library, or a valid --config")
            sys.exit(1)

        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)

        if source_base is None:
            source_base = Path(config.get('source_path', ''))
        if library_base is None:
            library_base = Path(config.get('library_path', ''))

    # Hard gate: verify paths
    if not source_base.exists():
        logger.error(f"Source directory not found: {source_base}")
        sys.exit(1)

    if not library_base.exists():
        logger.error(f"Library directory not found: {library_base}")
        logger.error("Is the destination drive mounted?")
        sys.exit(1)

    # Execute
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN MODE — no files will be moved")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("EXECUTING MOVES")
        print(f"Source:  {source_base}")
        print(f"Library: {library_base}")
        print("=" * 60 + "\n")

    stats = process_manifest(args.manifest, source_base, library_base, dry_run)
    print_stats(stats, dry_run)

    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
