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
        # These caps bound auto-classification only. Human-curated (explicit lookup)
        # results are never blocked — increment_count() logs a warning if exceeded.
        # Cult Oddities: no SATELLITE_ROUTING_RULES entry → no auto-classification path.
        # Human-curated only; cap removed to avoid dead code confusion.
        self.caps = {
            'Giallo': 30,
            'Japanese New Wave': 15,      # Issue #33
            'Pinku Eiga': 35,
            'Japanese Exploitation': 25,  # Issue #6
            'Brazilian Exploitation': 45,
            'Hong Kong New Wave': 15,     # Issue #34
            'Hong Kong Category III': 10, # Issue #34
            'Hong Kong Action': 65,
            'American Exploitation': 80,
            'European Sexploitation': 25,
            'Blaxploitation': 20,
            'Music Films': 20,
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
        # When tmdb_data is absent but metadata has a director (parsed from filename),
        # construct a minimal dict for director-only routing rules (FNW, Indie Cinema
        # directors list, etc.).  Country/genre-based rules still won't fire because
        # countries=[] and genres=[] give no match — only director-match paths run.
        if not tmdb_data:
            if not (hasattr(metadata, 'director') and metadata.director):
                return None
            tmdb_data = {
                'director': metadata.director,
                'year': metadata.year,
                'countries': [],
                'genres': [],
                'cast': [],
                'keywords': [],
                'overview': '',
                'tagline': '',
                'plot': '',
            }

        # Issue #25: Core director guard removed. With Satellite routing before Core in the
        # pipeline (classify.py), Core directors now intentionally route to Satellite for
        # their movement-period films. The movement's decade gate is the natural boundary:
        # a director in the FNW list (1950s-1970s) routes to FNW for those decades, then
        # falls through to the Core director check for work outside the movement period.
        # Prestige films are pinned to Core via SORTING_DATABASE.md entries (Stage 2),
        # which fire before Satellite routing is ever reached.

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
                director_tokens = set(director_lower.split())
                if any(self._director_matches(director_lower, director_tokens, d)
                       for d in rules['directors']):
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

            # Issue #29 Tier A: country + decade + keyword hit (genre gate waived)
            # Fires when structural country match succeeded but genre tag is absent/wrong —
            # e.g. an Italian Drama 1970s with a "giallo" TMDb tag routes to Giallo
            # despite TMDb not filing it under Horror/Thriller.
            keyword_signals = rules.get('keyword_signals')
            if keyword_signals and country_match and not genre_match:
                hit, _ = self._keyword_hit(tmdb_data, keyword_signals)
                if hit:
                    return self._check_cap(category_name)

            # Issue #29 Tier B: TMDb keyword tag alone for movement categories.
            # Fires for director-only categories (French New Wave, American New Hollywood)
            # when no director match was found but a movement-specific TMDb tag is present.
            # Restricted to tmdb_tags only — text_terms are not precise enough without
            # structural corroboration.
            if rules.get('tier_b_eligible') and keyword_signals:
                tmdb_tags_lower = [k.lower() for k in tmdb_data.get('keywords', [])]
                if any(tag in tmdb_tags_lower
                       for tag in keyword_signals.get('tmdb_tags', [])):
                    return self._check_cap(category_name)

        return None

    @staticmethod
    def _director_matches(director_lower: str, director_tokens: set, entry: str) -> bool:
        """Whole-word match for single-word entries; substring for multi-word entries.

        Single-word entries (e.g. 'bava', 'malle', 'lenzi') require the entry to be a
        complete whitespace-delimited token in the director name. This prevents
        'malle' from matching a director called 'Pierre Mallette', for example.

        Multi-word entries (e.g. 'tsui hark', 'john woo', 'gordon parks') use substring
        matching, which is safe because an exact phrase won't produce false positives.
        Hyphenated surnames (e.g. 'robbe-grillet') are treated as single tokens by
        str.split() and therefore use whole-word matching.

        Issue #25 D1: replaces the previous `any(d in director_lower ...)` substring
        check, which violated the R/P split by allowing ambiguous partial matches.
        """
        if ' ' not in entry:
            return entry in director_tokens
        return entry in director_lower

    @staticmethod
    def _title_matches_keywords(title: str, keywords) -> bool:
        """Conservative title keyword gate for high-false-positive categories."""
        if not title:
            return False
        return any(keyword in title for keyword in keywords)

    @staticmethod
    def _keyword_hit(tmdb_data: Dict, signals: Dict):
        """Check TMDb keyword tags and text fields for keyword_signals matches.

        Returns (hit: bool, source: str | None).
        TMDb tags checked first (higher precision). Text terms scan overview, tagline, plot.
        """
        tmdb_tags_lower = [k.lower() for k in tmdb_data.get('keywords', [])]
        text_blob = ' '.join([
            tmdb_data.get('overview', '') or '',
            tmdb_data.get('tagline', '') or '',
            tmdb_data.get('plot', '') or '',
        ]).lower()

        for tag in signals.get('tmdb_tags', []):
            if tag.lower() in tmdb_tags_lower:
                return True, 'tmdb_tag'
        for term in signals.get('text_terms', []):
            if term.lower() in text_blob:
                return True, 'text_term'
        return False, None

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
