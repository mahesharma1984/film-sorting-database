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

    def __init__(self, categories_file=None):
        """
        Initialize classifier with category definitions and caps

        Note: categories_file parameter kept for compatibility but not used
        Issue #6: Added Japanese Exploitation category
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

    def classify(self, metadata, tmdb_data: Optional[Dict]) -> Optional[str]:
        """
        Classify using TMDb structured data + decade-bounded director rules

        CRITICAL FIX (Issue #6): Director routing now respects decade bounds
        Uses unified SATELLITE_ROUTING_RULES from constants.py

        Args:
            metadata: FilmMetadata object
            tmdb_data: TMDb data dict with keys: title, year, director, genres, countries

        Returns:
            Category name if classified, None otherwise
        """
        if not tmdb_data:
            return None

        # Extract structured data
        countries = tmdb_data.get('countries', [])
        genres = tmdb_data.get('genres', [])
        director = tmdb_data.get('director', '') or ''
        year = tmdb_data.get('year')
        director_lower = director.lower()

        # Calculate decade for validation
        decade = None
        if year:
            decade = f"{(year // 10) * 10}s"

        # Import routing rules (lazy import to avoid circular dependencies)
        from lib.constants import SATELLITE_ROUTING_RULES

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

            # Both must match (or be unrestricted via None)
            if country_match and genre_match:
                return self._check_cap(category_name)

        return None

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
        """Manually increment category count (for explicit lookups)"""
        self.counts[category] += 1

    def get_stats(self) -> Dict:
        """Get category classification statistics"""
        return {
            'counts': dict(self.counts),
            'caps': self.caps,
            'available': {cat: self.caps[cat] - self.counts[cat] for cat in self.caps}
        }
