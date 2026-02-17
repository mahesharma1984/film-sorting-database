#!/usr/bin/env python3
"""
Quality gates for classification pipeline handoffs.
External observer - reads data, never modifies pipeline.

Implements Theory of Constraints (TOC) + Kanban quality gates:
- Gate 1: Title cleaning validation (Parser → API Query)
- Gate 2: API enrichment validation (API Query → Classification)
- Gate 3: Routing success validation (Classification → Output)

Usage:
    This module provides HandoffGates class for integration into classify.py.
    Gates validate data survival at critical pipeline boundaries.
"""
import re
from typing import Dict, Optional, Any


class HandoffGates:
    """
    Validation gates at critical pipeline boundaries.

    Per constraint theory: Validate handoffs ($0) before running expensive stages ($$).
    """

    def __init__(self, release_tags=None):
        """
        Initialize handoff gates.

        Args:
            release_tags: List of release tag strings to check for. If None, imports from constants.
        """
        if release_tags is None:
            try:
                from lib.constants import RELEASE_TAGS
                self.release_tags = RELEASE_TAGS
            except ImportError:
                # Fallback if constants not available
                self.release_tags = ['bluray', 'web-dl', 'webrip', 'x264', 'x265', '1080p', '720p']
        else:
            self.release_tags = release_tags

    def gate_title_cleaning(self, original_title: str, cleaned_title: str) -> Dict[str, Any]:
        """
        Gate 1: Parser → API Query handoff
        Validates that RELEASE_TAGS tokens don't survive cleaning.

        Cost: $0 (regex check)
        Severity: HARD (stops API queries if fails)

        Args:
            original_title: Title before cleaning
            cleaned_title: Title after _clean_title_for_api()

        Returns:
            Dict with keys: gate, passed, severity, surviving_tags, message
        """
        cleaned_lower = cleaned_title.lower()
        surviving_tags = []

        for tag in self.release_tags:
            if tag in cleaned_lower:
                surviving_tags.append(tag)

        passed = len(surviving_tags) == 0

        return {
            'gate': 'title_cleaning',
            'passed': passed,
            'severity': 'HARD',
            'surviving_tags': surviving_tags,
            'original_title': original_title,
            'cleaned_title': cleaned_title,
            'message': f"⛔ {len(surviving_tags)} RELEASE_TAGS survived cleaning: {surviving_tags}" if not passed else "✓ Title clean"
        }

    def gate_api_enrichment(self, title: str, year: int, api_result: Optional[Dict]) -> Dict[str, Any]:
        """
        Gate 2: API Query → Classification handoff
        Validates that API enrichment produced minimum required data.

        Cost: $0 (reads cached result)
        Severity: SOFT (warns but continues - some films legitimately have no data)

        Args:
            title: Film title
            year: Film year
            api_result: Merged API result dict from _merge_api_results()

        Returns:
            Dict with keys: gate, passed, severity, has_director, has_country, message
        """
        if api_result is None:
            return {
                'gate': 'api_enrichment',
                'passed': False,
                'severity': 'SOFT',
                'has_director': False,
                'has_country': False,
                'title': title,
                'year': year,
                'message': f"⚠️  No API data for {title} ({year})"
            }

        has_director = bool(api_result.get('director'))
        has_country = bool(api_result.get('countries'))

        # Minimum viable enrichment: director OR country
        passed = has_director or has_country

        return {
            'gate': 'api_enrichment',
            'passed': passed,
            'severity': 'SOFT',
            'has_director': has_director,
            'has_country': has_country,
            'title': title,
            'year': year,
            'message': f"⚠️  No director or country for {title} ({year})" if not passed else "✓ API enriched"
        }

    def gate_routing_success(self, metadata: Dict, classification_result: Dict) -> Dict[str, Any]:
        """
        Gate 3: Classification → Output handoff
        Flags films with good metadata that went Unsorted (routing failure).

        Cost: $0 (reads classification result)
        Severity: SOFT (informational - helps identify routing gaps)

        Args:
            metadata: FilmMetadata dict or similar with director/country fields
            classification_result: ClassificationResult dict with tier field

        Returns:
            Dict with keys: gate, passed, severity, tier, has_metadata, message
        """
        has_director = bool(metadata.get('director'))
        has_country = bool(metadata.get('country'))
        tier = classification_result.get('tier')

        # Flag: Has enrichment but still Unsorted
        routing_failed = (has_director or has_country) and tier == 'Unsorted'

        title = metadata.get('title', 'Unknown')

        return {
            'gate': 'routing_success',
            'passed': not routing_failed,
            'severity': 'SOFT',
            'tier': tier,
            'has_metadata': has_director or has_country,
            'title': title,
            'message': f"⚠️  Enriched film went Unsorted: {title}" if routing_failed else "✓ Routed"
        }


# Example integration for classify.py:
#
# from scripts.validate_handoffs import HandoffGates
#
# class FilmClassifier:
#     def __init__(self, ...):
#         ...
#         self.gates = HandoffGates()
#
#     def _query_apis(self, metadata: FilmMetadata):
#         ...
#         clean_title = self._clean_title_for_api(metadata.title)
#
#         # Gate 1: Validate title cleaning BEFORE API query
#         gate1 = self.gates.gate_title_cleaning(metadata.title, clean_title)
#         if not gate1['passed'] and gate1['severity'] == 'HARD':
#             logger.warning(gate1['message'])
#             # Don't waste API call on dirty title
#             return {'tmdb': None, 'omdb': None}
#
#         # Query APIs...
#         results = {'tmdb': None, 'omdb': None}
#         if self.tmdb:
#             tmdb_data = self.tmdb.search_film(clean_title, metadata.year)
#             if tmdb_data:
#                 results['tmdb'] = tmdb_data
#
#         # Gate 2: Validate API enrichment AFTER query
#         merged = self._merge_api_results(results['tmdb'], results['omdb'], metadata)
#         gate2 = self.gates.gate_api_enrichment(metadata.title, metadata.year, merged)
#         if not gate2['passed']:
#             logger.info(gate2['message'])  # Informational, not blocking
#
#         return results
#
#     def classify_film(self, metadata: FilmMetadata):
#         ...
#         result = self._final_classification_logic(metadata)
#
#         # Gate 3: Track routing success
#         gate3 = self.gates.gate_routing_success(metadata.__dict__, result.__dict__)
#         if not gate3['passed']:
#             logger.info(gate3['message'])  # Track routing gaps for manual review
#
#         return result


if __name__ == '__main__':
    # Self-test demonstration
    print("HandoffGates Self-Test\n" + "="*60)

    gates = HandoffGates(release_tags=['bluray', 'web-dl', 'x264', '1080p'])

    # Test Gate 1: Title cleaning
    print("\n--- Gate 1: Title Cleaning ---")
    gate1_pass = gates.gate_title_cleaning(
        "A Man and a Woman [1966] Metro 1080p",
        "A Man and a Woman"
    )
    print(f"Clean title (should pass): {gate1_pass['message']}")

    gate1_fail = gates.gate_title_cleaning(
        "Breathless 1960 BluRay x264",
        "Breathless BluRay"  # BluRay survived
    )
    print(f"Dirty title (should fail): {gate1_fail['message']}")

    # Test Gate 2: API enrichment
    print("\n--- Gate 2: API Enrichment ---")
    gate2_pass = gates.gate_api_enrichment(
        "The 400 Blows", 1959,
        {'director': 'François Truffaut', 'countries': ['FR'], 'genres': ['Drama']}
    )
    print(f"Enriched (should pass): {gate2_pass['message']}")

    gate2_fail = gates.gate_api_enrichment(
        "Unknown Film", 1999,
        {'director': None, 'countries': []}
    )
    print(f"Not enriched (should warn): {gate2_fail['message']}")

    # Test Gate 3: Routing success
    print("\n--- Gate 3: Routing Success ---")
    gate3_pass = gates.gate_routing_success(
        {'title': 'Breathless', 'director': 'Jean-Luc Godard', 'country': 'FR'},
        {'tier': 'Core', 'destination': 'Core/1960s/Jean-Luc Godard/'}
    )
    print(f"Routed correctly (should pass): {gate3_pass['message']}")

    gate3_fail = gates.gate_routing_success(
        {'title': 'Mystery Film', 'director': 'Known Director', 'country': 'US'},
        {'tier': 'Unsorted', 'destination': 'Unsorted/'}
    )
    print(f"Routing failed (should warn): {gate3_fail['message']}")

    print("\n" + "="*60)
    print("✓ Self-test complete")
