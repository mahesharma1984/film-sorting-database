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
from pathlib import Path
from typing import List, Dict
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.constants import SATELLITE_TENTPOLES
from lib.parser import FilmMetadata

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


def main():
    parser = argparse.ArgumentParser(
        description="Classify Satellite tentpole films"
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

    if not args.execute:
        print("\n" + "="*80)
        print("DRY RUN - No files moved")
        print("To actually move files, run with --execute flag")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("WARNING: --execute flag not yet implemented")
        print("This script currently only validates classifications")
        print("="*80)


if __name__ == '__main__':
    main()
