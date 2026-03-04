#!/usr/bin/env python3
"""
scripts/audit_lookup_coverage.py

Re-classifies films currently in explicit_lookup using only the signals layer
(skipping SORTING_DATABASE and corpus lookup), to identify which manual pins
the pipeline would now get right automatically.

Output: output/lookup_coverage.csv
Columns: filename, title, year, director, explicit_destination,
         signal_destination, signal_reason, signal_confidence, verdict

Verdict values:
  AGREE     — signal routes to same destination as explicit_lookup
  DISAGREE  — signal routes to a different destination
  UNSORTED  — signal cannot classify (would remain Unsorted)

AGREE films are candidates to retire from SORTING_DATABASE.md.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from classify import FilmClassifier, get_decade
from lib.parser import FilmMetadata
from lib.signals import score_director, score_structure, integrate_signals


MANIFEST_PATH = Path('output/sorting_manifest.csv')
OUTPUT_PATH   = Path('output/lookup_coverage.csv')
CONFIG_PATH   = Path('config.yaml')

FIELDNAMES = [
    'filename', 'title', 'year', 'director',
    'explicit_destination', 'signal_destination',
    'signal_reason', 'signal_confidence', 'verdict',
]


def normalize_dest(dest: str) -> str:
    """Normalize destination for comparison (strip trailing slash, lowercase)."""
    return dest.strip('/').lower()


def main():
    if not MANIFEST_PATH.exists():
        print(f"Error: {MANIFEST_PATH} not found. Run classify.py first.")
        sys.exit(1)

    # Load explicit_lookup rows from manifest
    explicit_films = []
    with open(MANIFEST_PATH, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('reason') == 'explicit_lookup':
                explicit_films.append(row)

    if not explicit_films:
        print("No explicit_lookup films found in manifest.")
        sys.exit(0)

    print(f"Found {len(explicit_films)} explicit_lookup films to audit.")
    print("Loading classifier components (uses cached API data)...")

    classifier = FilmClassifier(CONFIG_PATH)

    results  = []
    verdicts = defaultdict(int)

    for i, row in enumerate(explicit_films, 1):
        title    = row.get('title', '') or ''
        year_str = row.get('year', '') or ''
        director = row.get('director', '') or None
        country  = row.get('country', '') or None
        explicit_dest = row.get('destination', '') or ''
        filename = row.get('filename', '') or ''

        try:
            year = int(year_str) if year_str else None
        except ValueError:
            year = None

        if not year:
            verdicts['UNSORTED'] += 1
            results.append({
                'filename': filename, 'title': title, 'year': year_str,
                'director': director or '',
                'explicit_destination': explicit_dest,
                'signal_destination': 'Unsorted/',
                'signal_reason': 'unsorted_no_year',
                'signal_confidence': 0.0,
                'verdict': 'UNSORTED',
            })
            continue

        decade = get_decade(year)

        # Reconstruct FilmMetadata so we can call the existing API + merge pipeline
        metadata = FilmMetadata(
            filename=filename,
            title=title,
            year=year,
            director=director,
            language=row.get('language') or None,
            country=country,
            user_tag=None,
        )

        # Query API caches (no new API calls for previously-seen films)
        api_results = classifier._query_apis(metadata)
        tmdb_data   = classifier._merge_api_results(
            api_results.get('tmdb'),
            api_results.get('omdb'),
            metadata,
        )

        readiness = classifier._assess_readiness(metadata, tmdb_data)

        # Run signals (skip explicit_lookup and corpus_lookup)
        director_matches   = score_director(metadata.director, year, classifier.core_db)
        structural_matches = score_structure(
            metadata=metadata,
            tmdb_data=tmdb_data,
            satellite_classifier=classifier.satellite_classifier,
            popcorn_classifier=classifier.popcorn_classifier,
        )
        integration = integrate_signals(
            director_matches=director_matches,
            structural_matches=structural_matches,
            decade=decade,
            readiness=readiness,
        )

        if integration.tier == 'Unsorted':
            verdict       = 'UNSORTED'
            signal_dest   = 'Unsorted/'
            signal_reason = integration.reason
            signal_conf   = 0.0
        elif normalize_dest(integration.destination) == normalize_dest(explicit_dest):
            verdict       = 'AGREE'
            signal_dest   = integration.destination
            signal_reason = integration.reason
            signal_conf   = integration.confidence
        else:
            verdict       = 'DISAGREE'
            signal_dest   = integration.destination
            signal_reason = integration.reason
            signal_conf   = integration.confidence

        verdicts[verdict] += 1
        results.append({
            'filename':             filename,
            'title':                title,
            'year':                 year,
            'director':             metadata.director or '',
            'explicit_destination': explicit_dest,
            'signal_destination':   signal_dest,
            'signal_reason':        signal_reason,
            'signal_confidence':    round(signal_conf, 2),
            'verdict':              verdict,
        })

        if i % 50 == 0:
            print(f"  {i}/{len(explicit_films)} processed...")

    # Write CSV
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)

    total   = len(results)
    agree   = verdicts['AGREE']
    disagree= verdicts['DISAGREE']
    unsorted= verdicts['UNSORTED']

    print(f"\nResults written to {OUTPUT_PATH}")
    print(f"\nSummary ({total} films):")
    print(f"  AGREE    : {agree:>4}  ({agree/total*100:.1f}%)  — signal matches manual destination")
    print(f"  DISAGREE : {disagree:>4}  ({disagree/total*100:.1f}%)  — signal routes differently")
    print(f"  UNSORTED : {unsorted:>4}  ({unsorted/total*100:.1f}%)  — signal cannot classify")
    print(f"\nAGREE films are candidates to retire from SORTING_DATABASE.md.")
    if disagree:
        print(f"Review DISAGREE films before removing their pins.")


if __name__ == '__main__':
    main()
