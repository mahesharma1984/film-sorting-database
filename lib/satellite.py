#!/usr/bin/env python3
"""
Satellite category classification using TMDb structured data

Issue #6 Update: Decade-validated director-based routing
- Replaces hardcoded director_mappings with SATELLITE_ROUTING_RULES from constants
- Adds decade validation to ALL director-based routing (critical bug fix)
- Adds 6 new directors and Japanese Exploitation category
"""

import logging
from typing import Optional, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class SatelliteClassifier:
    """Classify films into Satellite categories using TMDb structured data"""

    def __init__(self, categories_file=None, core_db=None):
        """
        Initialize classifier with category definitions and caps

        Note: categories_file parameter kept for compatibility but not used
        Issue #6: Added Japanese Exploitation category
        Issue #16: Added core_db for defensive Core director check
        """
        self.caps = {
            'Giallo': 30,
            'Pinku Eiga': 35,
            'Japanese Exploitation': 25,  # NEW: Issue #6
            'Brazilian Exploitation': 45,
            'Hong Kong Action': 65,
            'American Exploitation': 80,
            'European Sexploitation': 25,
            'Blaxploitation': 20,
            'Music Films': 20,
            'Cult Oddities': 50,
        }
        self.counts = defaultdict(int)  # Track category counts
        self.core_db = core_db  # Issue #16: optional CoreDirectorDatabase for defensive check

    def classify(self, metadata, tmdb_data: Optional[Dict]) -> Optional[str]:
        """
        Classify using TMDb structured data + decade-bounded director rules

        CRITICAL FIX (Issue #6): Director routing now respects decade bounds
        NEW (Issue #16): Core director defensive check prevents Satellite misrouting
        Uses unified SATELLITE_ROUTING_RULES from constants.py

        Args:
            metadata: FilmMetadata object
            tmdb_data: TMDb data dict with keys: title, year, director, genres, countries

        Returns:
            Category name if classified, None otherwise
        """
        if not tmdb_data:
            return None

        # NEW (Issue #16): Defensive gate - check if director is Core before Satellite routing
        # Prevents Core auteurs from being caught by Satellite director-based routing
        # Example: Dario Argento (if Core) shouldn't route to Giallo before Core check
        # core_db is passed in at init time from FilmClassifier (avoid circular import)
        director = tmdb_data.get('director', '') or ''
        if director and self.core_db:
            if self.core_db.is_core_director(director):
                # This is a Core auteur - must NOT route to Satellite
                # Return None so main classifier handles Core routing
                logger.debug(f"Skipping Satellite routing for Core director: {director}")
                return None

        # Extract structured data
        countries = tmdb_data.get('countries', [])
        genres = tmdb_data.get('genres', [])
        director = tmdb_data.get('director', '') or ''
        year = tmdb_data.get('year')
        title = (tmdb_data.get('title') or getattr(metadata, 'title', '') or '').lower()
        director_lower = director.lower()

        # Calculate decade for validation
        decade = None
        if year:
            decade = f"{(year // 10) * 10}s"

        # Import routing rules (lazy import to avoid circular dependencies)
        from lib.constants import (
            SATELLITE_ROUTING_RULES,
            AMERICAN_EXPLOITATION_TITLE_KEYWORDS,
            BLAXPLOITATION_TITLE_KEYWORDS,
        )

        # Check each category's rules (first match wins)
        for category_name, rules in SATELLITE_ROUTING_RULES.items():
            # Skip if decade-bounded and film is outside valid decades
            # Note: None means no decade restriction (e.g., Music Films)
            if rules['decades'] is not None and decade not in rules['decades']:
                continue

            # Check director match (highest confidence signal)
            if rules['directors'] and director:
                if any(d in director_lower for d in rules['directors']):
                    return self._check_cap(category_name)

            # Check country + genre match (fallback)
            # Handle None for country_codes or genres (means no restriction)
            country_match = True  # Default to True if no country restriction
            if rules['country_codes'] is not None:
                country_match = any(c in countries for c in rules['country_codes'])

            genre_match = True  # Default to True if no genre restriction
            if rules['genres'] is not None:
                genre_match = any(g in genres for g in rules['genres'])

            # Tighten fallback for categories that were producing mainstream false positives.
            # Director match above still takes priority and remains permissive.
            if category_name == 'American Exploitation':
                if not self._title_matches_keywords(title, AMERICAN_EXPLOITATION_TITLE_KEYWORDS):
                    continue
            if category_name == 'Blaxploitation':
                if not self._title_matches_keywords(title, BLAXPLOITATION_TITLE_KEYWORDS):
                    continue

            # Both must match
            if country_match and genre_match:
                return self._check_cap(category_name)

        return None

    @staticmethod
    def _title_matches_keywords(title: str, keywords) -> bool:
        """Conservative title keyword gate for high-false-positive categories."""
        if not title:
            return False
        return any(keyword in title for keyword in keywords)

    def _check_cap(self, category: str) -> Optional[str]:
        """Check if category has reached cap"""
        if category not in self.caps:
            return category

        if self.counts[category] >= self.caps[category]:
            logger.warning(f"Category '{category}' at cap ({self.caps[category]})")
            return None

        self.counts[category] += 1
        return category

    def increment_count(self, category: str):
        """Increment count for explicit lookup results (Issue #25 D7).

        Explicit lookup entries are NOT blocked by the cap — human curation
        overrides auto-classification limits. A warning is logged when the cap
        is exceeded so the collection can be audited.
        """
        self.counts[category] += 1
        if category in self.caps and self.counts[category] > self.caps[category]:
            logger.warning(
                "Satellite category '%s' has %d entries, exceeding auto-classification "
                "cap of %d. These are explicit lookup entries — not blocked, but worth auditing.",
                category, self.counts[category], self.caps[category]
            )

    def get_stats(self) -> Dict:
        """Get category classification statistics"""
        return {
            'counts': dict(self.counts),
            'caps': self.caps,
            'available': {cat: self.caps[cat] - self.counts[cat] for cat in self.caps}
        }
