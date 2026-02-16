#!/usr/bin/env python3
"""Show what would be reclassified with new satellite categories"""

import sys
from pathlib import Path
import csv
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.parser import FilenameParser
from lib.core_directors import CoreDirectorDatabase
from lib.satellite import SatelliteClassifier
from classify import FilmClassifier

def load_manifest(manifest_path: str) -> List[Dict]:
    """Load sorting manifest"""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def compare_classifications(config_path: str, manifest_path: str):
    """Compare old vs new classifications"""

    # Load manifest
    films = load_manifest(manifest_path)

    # Create classifiers with new rules
    from classify import FilmClassifier
    classifier = FilmClassifier(config_path)  # WITH TMDb support to test satellite

    reclassifications = []

    print("Analyzing films for reclassification...")
    print("(This may take a minute as it checks satellite categories)\n")

    for i, film in enumerate(films):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(films)} films...")

        filename = film['filename']
        old_destination = film['destination']
        old_tier = film['tier']

        # Re-classify with new rules
        try:
            metadata = classifier.parser.parse(filename)

            # Use manifest data to enrich metadata
            if film.get('director'):
                metadata.director = film['director']
            if film.get('country'):
                metadata.country = film['country']
            if film.get('year'):
                try:
                    metadata.year = int(film['year'])
                except (ValueError, TypeError):
                    pass

            # Use the classifier's normal flow (will use TMDb cache)
            result = classifier.classify(metadata)
            new_destination = result.destination
            new_tier = result.tier

            # Check if changed
            if old_destination != new_destination:
                reclassifications.append({
                    'filename': filename,
                    'title': film.get('title', ''),
                    'year': film.get('year', ''),
                    'director': film.get('director', ''),
                    'old_tier': old_tier,
                    'old_dest': old_destination,
                    'new_tier': new_tier,
                    'new_dest': new_destination,
                    'reason': result.reason
                })
        except Exception as e:
            pass  # Skip problematic films

    print(f"  Processed {len(films)}/{len(films)} films.\n")

    # Display results
    if not reclassifications:
        print("✅ No reclassifications needed - all films correctly classified.\n")
        return

    print(f"🔄 Found {len(reclassifications)} films that would be reclassified:\n")
    print("=" * 100)

    # Group by type of change
    core_fixes = []
    fnw_additions = []
    other_changes = []

    for reclass in reclassifications:
        if reclass['new_tier'] == 'Core' and reclass['old_tier'] != 'Core':
            core_fixes.append(reclass)
        elif 'French New Wave' in reclass['new_dest']:
            fnw_additions.append(reclass)
        else:
            other_changes.append(reclass)

    # Show Core fixes (Issue #14)
    if core_fixes:
        print(f"\n📌 CORE DIRECTOR FIXES (Issue #14): {len(core_fixes)} films")
        print("-" * 100)
        for r in core_fixes:
            print(f"\n{r['title']} ({r['year']}) - {r['director']}")
            print(f"  FROM: {r['old_dest']}")
            print(f"  TO:   {r['new_dest']}")
            print(f"  WHY:  Core director was being misrouted to Satellite")

    # Show French New Wave additions
    if fnw_additions:
        print(f"\n🎬 FRENCH NEW WAVE CATEGORY: {len(fnw_additions)} films")
        print("-" * 100)
        for r in fnw_additions:
            print(f"\n{r['title']} ({r['year']}) - {r['director']}")
            print(f"  FROM: {r['old_dest']}")
            print(f"  TO:   {r['new_dest']}")
            print(f"  WHY:  Now routes to French New Wave instead of Sexploitation/Unsorted")

    # Show other changes
    if other_changes:
        print(f"\n🔧 OTHER RECLASSIFICATIONS: {len(other_changes)} films")
        print("-" * 100)
        for r in other_changes:
            print(f"\n{r['title']} ({r['year']}) - {r['director']}")
            print(f"  FROM: {r['old_dest']}")
            print(f"  TO:   {r['new_dest']}")

    print("\n" + "=" * 100)
    print(f"\nTotal reclassifications: {len(reclassifications)}")
    print("\nTo actually move these films, you'll need to:")
    print("  1. Update library_path in config.yaml to point to your organized library")
    print("  2. Run: python reclassify_moves.py --library /path/to/library --execute")

if __name__ == '__main__':
    config_path = Path('config_external.yaml')
    if not config_path.exists():
        config_path = Path('config.yaml')

    manifest_path = Path('output/sorting_manifest.csv')

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    compare_classifications(str(config_path), str(manifest_path))
