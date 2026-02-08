#!/usr/bin/env python3
"""
Reorganize films based on new (fixed) classifications
Moves files from incorrect locations to correct destinations
"""
import csv
import shutil
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    if shutdown_requested:
        logger.error("\nForced shutdown! May have left partial files.")
        sys.exit(1)
    shutdown_requested = True
    logger.warning("\n\nShutdown requested. Finishing current operation then exiting...")
    logger.warning("(Press Ctrl+C again to force immediate exit)\n")


def build_file_index(base_path: Path) -> Dict[str, Path]:
    """Build index of all video files in directory (scan once)"""
    import re

    logger.info("Building file index (scanning directory once)...")
    index = {}

    video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v'}

    for file_path in base_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            # Index by exact filename
            index[file_path.name] = file_path

            # Also index by cleaned stem (without tags)
            stem = file_path.stem
            stem_clean = re.sub(r'\s*\[.*?\]\s*', '', stem).strip()
            extension = file_path.suffix
            clean_name = f"{stem_clean}{extension}"
            if clean_name not in index:
                index[clean_name] = file_path

    logger.info(f"Indexed {len(index)} files")
    return index


def find_file_in_index(filename: str, file_index: Dict[str, Path]) -> Path | None:
    """Find a file using pre-built index (fast lookup)"""
    import re

    # Try exact match first
    if filename in file_index:
        return file_index[filename]

    # Try cleaned version (without tags)
    stem = Path(filename).stem
    stem_clean = re.sub(r'\s*\[.*?\]\s*', '', stem).strip()
    extension = Path(filename).suffix
    clean_name = f"{stem_clean}{extension}"

    if clean_name in file_index:
        return file_index[clean_name]

    return None


def move_file_safely(source_file: Path, dest_file: Path, dry_run: bool = False) -> bool:
    """Safely move file with copy+verify+delete"""

    if dry_run:
        logger.info(f"DRY RUN: Would move")
        logger.info(f"  FROM: {source_file}")
        logger.info(f"  TO:   {dest_file}")
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
        if counter > 1:
            logger.warning(f"Destination exists, using: {dest_file.name}")

    try:
        # Use shutil.move which will:
        # - Use os.rename() if same filesystem (instant)
        # - Fall back to copy+delete if cross-filesystem
        shutil.move(str(source_file), str(dest_file))

        logger.info(f"✓ Moved: {source_file.name}")
        logger.info(f"  TO:   {dest_file.relative_to(dest_file.parents[2])}")
        return True

    except Exception as e:
        logger.error(f"Error moving {source_file}: {e}")
        return False


def main():
    import argparse

    # Register signal handler for graceful Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description='Reorganize films based on fixed classification'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview moves without executing'
    )
    parser.add_argument(
        '--base-path',
        type=Path,
        default=Path('/Volumes/One Touch/movies/Organized'),
        help='Base path to Organized directory'
    )
    parser.add_argument(
        '--report',
        type=Path,
        default=Path('output/location_verification_report.csv'),
        help='Path to location verification report'
    )

    args = parser.parse_args()

    base_path = args.base_path
    report_path = args.report

    if not base_path.exists():
        logger.error(f"Base path not found: {base_path}")
        return 1

    if not report_path.exists():
        logger.error(f"Report not found: {report_path}")
        logger.error("Run verify_locations.py first to generate the report")
        return 1

    # Read verification report
    logger.info(f"Reading report: {report_path}")
    moves = []

    with open(report_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            moves.append(row)

    logger.info(f"Found {len(moves)} files to reorganize")

    if args.dry_run:
        logger.info("\n" + "="*70)
        logger.info("DRY RUN MODE - No files will be moved")
        logger.info("="*70 + "\n")

    # Group moves by type
    by_tier = {}
    for move in moves:
        tier = move['tier']
        if tier not in by_tier:
            by_tier[tier] = []
        by_tier[tier].append(move)

    logger.info("\nMoves by tier:")
    for tier, items in sorted(by_tier.items()):
        logger.info(f"  {tier}: {len(items)} files")

    # Build file index ONCE (major speedup)
    file_index = build_file_index(base_path)

    # Execute moves
    logger.info("\n" + "="*70)
    logger.info("Starting reorganization...")
    logger.info("="*70 + "\n")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, move in enumerate(moves, 1):
        # Check for shutdown request
        if shutdown_requested:
            logger.warning(f"\nShutdown requested after processing {i-1}/{len(moves)} files")
            break

        filename = move['filename']
        expected_dest = move['expected']

        if (i % 50 == 0) or (i == 1):
            logger.info(f"\nProcessing {i}/{len(moves)}...")

        # Find the file using pre-built index (fast)
        source_file = find_file_in_index(filename, file_index)

        if not source_file:
            logger.warning(f"File not found: {filename}")
            skip_count += 1
            continue

        # Build destination path
        dest_file = base_path / expected_dest / filename

        # Check if already in correct location
        if source_file.parent == dest_file.parent:
            logger.debug(f"Already in correct location: {filename}")
            skip_count += 1
            continue

        # Move the file
        if move_file_safely(source_file, dest_file, args.dry_run):
            success_count += 1
        else:
            fail_count += 1

    # Print summary
    logger.info("\n" + "="*70)
    logger.info("REORGANIZATION COMPLETE")
    logger.info("="*70)
    logger.info(f"✓ Successfully moved: {success_count}")
    logger.info(f"⊘ Skipped:           {skip_count}")
    logger.info(f"✗ Failed:            {fail_count}")
    logger.info(f"  TOTAL:             {len(moves)}")

    if args.dry_run:
        logger.info("\n" + "="*70)
        logger.info("This was a DRY RUN - no files were actually moved")
        logger.info("Remove --dry-run flag to execute the moves")
        logger.info("="*70)

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
