#!/usr/bin/env python3
"""
Classify and move Satellite tentpole films

This script:
1. Loads tentpole films from SATELLITE_TENTPOLES
2. Classifies them using existing classification logic
3. Shows current vs. intended classification
4. Moves them with --execute flag

Use case: Validate that tentpole films are in correct locations
"""

import sys
import argparse
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import csv
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.constants import SATELLITE_TENTPOLES
from lib.parser import FilmMetadata
from lib.normalization import normalize_for_lookup

# Import FilmClassifier from classify.py
import classify
FilmClassifier = classify.FilmClassifier
ClassificationResult = classify.ClassificationResult


def create_tentpole_metadata() -> List[tuple]:
    """
    Convert SATELLITE_TENTPOLES to list of (FilmMetadata, intended_category)

    Returns:
        List of (metadata, category) tuples
    """
    tentpoles = []

    for category, films in SATELLITE_TENTPOLES.items():
        for title, year, director in films:
            # Create FilmMetadata for classification
            metadata = FilmMetadata(
                filename=f"{title} ({year}).mkv",  # Dummy filename
                title=title,
                year=year,
                director=director,
                # country and other fields will be enriched by API
            )
            tentpoles.append((metadata, category))

    return tentpoles


def classify_tentpoles(classifier: FilmClassifier, tentpoles: List[tuple]) -> List[Dict]:
    """
    Classify all tentpole films

    Args:
        classifier: FilmClassifier instance
        tentpoles: List of (FilmMetadata, intended_category) tuples

    Returns:
        List of classification results
    """
    results = []

    for metadata, intended_category in tentpoles:
        # Classify using existing logic
        result = classifier.classify(metadata)

        # Check if destination contains intended category
        # Handles both "Satellite/Giallo/1970s/" and "1970s/Satellite/Giallo/" formats
        is_satellite = 'Satellite' in result.destination or result.tier == 'Satellite'
        has_category = intended_category in result.destination
        match = is_satellite and has_category

        results.append({
            'title': metadata.title,
            'year': metadata.year,
            'director': metadata.director,
            'intended_category': intended_category,
            'classified_tier': result.tier,
            'classified_destination': result.destination,
            'confidence': result.confidence,
            'reason': result.reason,
            'match': match
        })

    return results


def print_report(results: List[Dict]):
    """Print classification report"""

    print("\n" + "="*80)
    print("TENTPOLE CLASSIFICATION REPORT")
    print("="*80 + "\n")

    # Group by match status
    matches = [r for r in results if r['match']]
    mismatches = [r for r in results if not r['match']]

    print(f"✓ Correct: {len(matches)}/{len(results)}")
    print(f"✗ Mismatches: {len(mismatches)}/{len(results)}\n")

    if mismatches:
        print("MISMATCHES:")
        print("-" * 80)
        for r in mismatches:
            print(f"\n{r['title']} ({r['year']}) — {r['director']}")
            print(f"  Intended: Satellite/{r['intended_category']}")
            print(f"  Classified: {r['classified_destination']}")
            print(f"  Reason: {r['reason']}")

    if matches:
        print("\n\nCORRECT CLASSIFICATIONS:")
        print("-" * 80)
        for r in matches:
            print(f"✓ {r['title']} ({r['year']}) → {r['classified_destination']}")


def save_manifest(results: List[Dict], output_path: Path):
    """Save results to CSV manifest"""

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'title', 'year', 'director', 'intended_category',
            'classified_tier', 'classified_destination',
            'confidence', 'reason', 'match'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✓ Manifest saved: {output_path}")


def find_film_in_directory(title: str, year: int, search_path: Path) -> Optional[Path]:
    """
    Find a film file in the search directory by title and year

    Args:
        title: Film title
        year: Film year
        search_path: Directory to search

    Returns:
        Path to film file if found, None otherwise
    """
    if not search_path.exists():
        return None

    # Normalize title for matching
    normalized_title = normalize_for_lookup(title).lower()

    # Search for video files
    video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.m4v']

    for file_path in search_path.rglob('*'):
        if file_path.suffix.lower() in video_extensions:
            # Check if filename contains title and year
            filename_lower = file_path.stem.lower()
            if str(year) in filename_lower:
                # Normalize filename for comparison
                normalized_filename = normalize_for_lookup(filename_lower)
                if normalized_title in normalized_filename:
                    return file_path

    return None


def same_filesystem(path_a: Path, path_b: Path) -> bool:
    """Check if two paths are on the same filesystem"""
    try:
        return os.stat(path_a).st_dev == os.stat(path_b).st_dev
    except OSError:
        return False


def move_file(source: Path, dest: Path, dry_run: bool = False) -> bool:
    """
    Move a single file from source to dest

    Args:
        source: Source file path
        dest: Destination file path
        dry_run: If True, don't actually move

    Returns:
        True if successful (or would be successful in dry-run)
    """
    if dry_run:
        print(f"  [DRY RUN] Would move: {source} → {dest}")
        return True

    # Create destination directory
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if same filesystem
    use_rename = same_filesystem(source, dest.parent)

    if use_rename:
        os.rename(source, dest)
        print(f"  ✓ Moved: {source.name} → {dest}")
        return True
    else:
        # Cross-filesystem: copy, verify, delete
        shutil.copy2(str(source), str(dest))

        # Verify
        if dest.exists() and dest.stat().st_size == source.stat().st_size:
            source.unlink()
            print(f"  ✓ Moved: {source.name} → {dest}")
            return True
        else:
            print(f"  ✗ Failed: {source.name} (verification failed)")
            if dest.exists():
                dest.unlink()
            return False


def move_tentpoles(results: List[Dict], source_path: Path, library_path: Path, dry_run: bool = False) -> Dict[str, int]:
    """
    Find and move tentpole films from source to library

    Args:
        results: Classification results
        source_path: Source directory to search
        library_path: Library base directory
        dry_run: If True, don't actually move files

    Returns:
        Statistics dict
    """
    stats = {
        'found': 0,
        'moved': 0,
        'not_found': 0,
        'errors': 0
    }

    print("\n" + "="*80)
    if dry_run:
        print("DRY RUN - Searching for tentpole films...")
    else:
        print("MOVING tentpole films...")
    print("="*80 + "\n")

    for result in results:
        title = result['title']
        year = result['year']
        destination = result['classified_destination']

        # Find film file
        film_path = find_film_in_directory(title, year, source_path)

        if not film_path:
            print(f"✗ Not found: {title} ({year})")
            stats['not_found'] += 1
            continue

        stats['found'] += 1

        # Build destination path
        dest_path = library_path / destination / film_path.name

        # Check if already at destination
        if film_path.resolve() == dest_path.resolve():
            print(f"  Already at destination: {title} ({year})")
            continue

        # Move file
        try:
            if move_file(film_path, dest_path, dry_run):
                stats['moved'] += 1
            else:
                stats['errors'] += 1
        except Exception as e:
            print(f"  ✗ Error moving {title} ({year}): {e}")
            stats['errors'] += 1

    # Print summary
    print("\n" + "="*80)
    print("MOVE SUMMARY")
    print("="*80)
    print(f"  Found: {stats['found']}/{len(results)}")
    print(f"  Moved: {stats['moved']}")
    print(f"  Not found: {stats['not_found']}")
    print(f"  Errors: {stats['errors']}")
    print("="*80)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Classify and move Satellite tentpole films"
    )
    parser.add_argument(
        'source',
        nargs='?',
        type=Path,
        help='Source directory to search for films (optional for validation-only)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config.yaml'),
        help='Configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually move files (default: dry-run only)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('output/tentpole_classification.csv'),
        help='Output manifest path'
    )

    args = parser.parse_args()

    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    # Load config for library path
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize classifier
    classifier = FilmClassifier(args.config)

    # Create tentpole metadata
    print("Loading tentpole films...")
    tentpoles = create_tentpole_metadata()
    print(f"Loaded {len(tentpoles)} tentpole films across {len(SATELLITE_TENTPOLES)} categories\n")

    # Classify all tentpoles
    print("Classifying tentpoles...")
    results = classify_tentpoles(classifier, tentpoles)

    # Print report
    print_report(results)

    # Save manifest
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_manifest(results, args.output)

    # Move files if source provided
    if args.source:
        if not args.source.exists():
            print(f"\nError: Source directory not found: {args.source}")
            sys.exit(1)

        library_path = Path(config['library_path'])
        move_tentpoles(results, args.source, library_path, dry_run=not args.execute)
    else:
        print("\n" + "="*80)
        print("VALIDATION ONLY - No source directory provided")
        print("To move files, run: python scripts/classify_tentpoles.py <source_dir> --execute")
        print("="*80)


if __name__ == '__main__':
    main()
