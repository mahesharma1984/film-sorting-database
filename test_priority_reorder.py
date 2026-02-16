#!/usr/bin/env python3
"""Test priority reordering: Popcorn/Indie BEFORE Satellite

Shows current vs proposed classification for films that should NOT be in
American Exploitation (1980s+).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.parser import FilmMetadata
from lib.popcorn import PopcornClassifier
from lib.satellite import SatelliteClassifier
from lib.core_directors import CoreDirectorDatabase
from lib.constants import REFERENCE_CANON

# Test films that are currently misclassified in American Exploitation
TEST_FILMS = [
    FilmMetadata(
        filename="Dead.Poets.Society.1989.mkv",
        title="Dead Poets Society",
        year=1989,
        director="Peter Weir",
        country="US"
    ),
    FilmMetadata(
        filename="Miracle.Mile.1988.mkv",
        title="Miracle Mile",
        year=1988,
        director="Steve De Jarnatt",
        country="US"
    ),
    FilmMetadata(
        filename="Pleasantville.1998.mkv",
        title="Pleasantville",
        year=1998,
        director="Gary Ross",
        country="US"
    ),
    FilmMetadata(
        filename="High.Art.1998.mkv",
        title="High Art",
        year=1998,
        director="Lisa Cholodenko",
        country="US"
    ),
    FilmMetadata(
        filename="Re-Animator.1985.mkv",
        title="Re-Animator",
        year=1985,
        director="Stuart Gordon",
        country="US"
    ),
]

def simulate_current_order(meta: FilmMetadata, tmdb_data=None) -> tuple:
    """Current order: Satellite BEFORE Popcorn"""
    whitelist_path = Path(__file__).parent / 'docs' / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
    core_db = CoreDirectorDatabase(whitelist_path)
    satellite = SatelliteClassifier()
    popcorn = PopcornClassifier()

    # Check Core (would be Stage 1-3)
    if meta.director and core_db.is_core_director(meta.director):
        return "Core", "core_director"

    # Check Reference (would be Stage 4)
    # (skipped for simplicity)

    # CURRENT STAGE 6: Satellite routing
    if tmdb_data:
        sat_cat = satellite.classify(meta, tmdb_data)
        if sat_cat:
            return "Satellite", f"tmdb_satellite ({sat_cat})"

    # CURRENT STAGE 7: Popcorn
    if tmdb_data:
        pop_reason = popcorn.classify_reason(meta, tmdb_data)
        if pop_reason:
            return "Popcorn", pop_reason

    return "Unsorted", "unsorted_no_match"

def simulate_proposed_order(meta: FilmMetadata, tmdb_data=None) -> tuple:
    """Proposed order: Popcorn/Indie BEFORE Satellite"""
    whitelist_path = Path(__file__).parent / 'docs' / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
    core_db = CoreDirectorDatabase(whitelist_path)
    satellite = SatelliteClassifier()
    popcorn = PopcornClassifier()

    # Check Core (would be Stage 1-3)
    if meta.director and core_db.is_core_director(meta.director):
        return "Core", "core_director"

    # Check Reference (would be Stage 4)
    # (skipped for simplicity)

    # PROPOSED STAGE 6: Popcorn (moved UP)
    if tmdb_data:
        pop_reason = popcorn.classify_reason(meta, tmdb_data)
        if pop_reason:
            return "Popcorn", pop_reason

    # PROPOSED STAGE 7: Indie Cinema (NEW check for post-1980)
    if meta.year and meta.year >= 1980:
        if tmdb_data and meta.country:
            # Check if it matches Indie Cinema criteria
            from lib.constants import SATELLITE_ROUTING_RULES
            indie_rules = SATELLITE_ROUTING_RULES.get('Indie Cinema', {})

            if meta.country in indie_rules.get('country_codes', []):
                genres = tmdb_data.get('genres', [])
                indie_genres = indie_rules.get('genres', [])
                if any(g in genres for g in indie_genres):
                    return "Satellite", "indie_cinema"

    # PROPOSED STAGE 8: Satellite (moved DOWN, only for pre-1980 exploitation)
    if tmdb_data:
        sat_cat = satellite.classify(meta, tmdb_data)
        if sat_cat:
            return "Satellite", f"tmdb_satellite ({sat_cat})"

    return "Unsorted", "unsorted_no_match"

def main():
    print("=" * 100)
    print("PRIORITY ORDER TEST: Popcorn/Indie BEFORE Satellite")
    print("=" * 100)
    print()

    # Simulate TMDb data for each film
    tmdb_mock = {
        "Dead Poets Society": {
            'genres': ['Drama'],
            'cast_popularity': 8.5,
            'countries': ['US']
        },
        "Miracle Mile": {
            'genres': ['Drama', 'Thriller'],
            'cast_popularity': 5.0,
            'countries': ['US']
        },
        "Pleasantville": {
            'genres': ['Drama', 'Comedy'],
            'cast_popularity': 7.0,
            'countries': ['US']
        },
        "High Art": {
            'genres': ['Drama', 'Romance'],
            'cast_popularity': 4.0,
            'countries': ['US']
        },
        "Re-Animator": {
            'genres': ['Horror', 'Comedy'],
            'cast_popularity': 6.5,
            'countries': ['US']
        },
    }

    for meta in TEST_FILMS:
        tmdb_data = tmdb_mock.get(meta.title)

        current_tier, current_reason = simulate_current_order(meta, tmdb_data)
        proposed_tier, proposed_reason = simulate_proposed_order(meta, tmdb_data)

        print(f"📽️  {meta.title} ({meta.year})")
        print(f"   Director: {meta.director}")
        print()
        print(f"   CURRENT:  {current_tier:<12} ({current_reason})")
        print(f"   PROPOSED: {proposed_tier:<12} ({proposed_reason})")

        if current_tier != proposed_tier:
            print(f"   ⚠️  WOULD CHANGE: {current_tier} → {proposed_tier}")
        else:
            print(f"   ✅ No change")

        print()
        print("-" * 100)
        print()

    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print()
    print("The proposed priority order would:")
    print("  1. Check Popcorn BEFORE Satellite")
    print("  2. Check Indie Cinema BEFORE Satellite (for 1980+ films)")
    print("  3. Only route to Satellite for true exploitation films")
    print()
    print("Expected impact:")
    print("  - Dead Poets Society: Satellite → Popcorn (mainstream prestige)")
    print("  - Pleasantville: Satellite → Popcorn (mainstream indie)")
    print("  - High Art: Satellite → Indie Cinema (true indie)")
    print("  - Re-Animator: Stays Satellite OR moves to Popcorn (cult classic)")
    print()

if __name__ == '__main__':
    main()
