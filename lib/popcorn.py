#!/usr/bin/env python3
"""Popcorn tier classification via format, cast, and popularity signals."""

import logging
from typing import Optional, Dict, Any

from lib.constants import (
    POPCORN_MAINSTREAM_COUNTRIES,
    POPCORN_MAINSTREAM_GENRES,
    POPCORN_STAR_ACTORS,
    POPCORN_STRONG_FORMAT_SIGNALS,
    EXPLOITATION_TITLE_KEYWORDS,
)

logger = logging.getLogger(__name__)


class PopcornClassifier:
    """Classify Popcorn films after Core/Reference/Satellite stages."""

    def __init__(self):
        self.mainstream_genres = set(POPCORN_MAINSTREAM_GENRES)
        self.mainstream_countries = set(POPCORN_MAINSTREAM_COUNTRIES)
        self.strong_format_signals = set(POPCORN_STRONG_FORMAT_SIGNALS)
        self.star_actors = set(POPCORN_STAR_ACTORS)
        self.min_popularity = 7.0  # Issue #16: lowered from 10.0 (collection skews niche, median popularity ~5-8)
        self.min_vote_count = 2000

    @staticmethod
    def _normalize_list(values):
        if not values:
            return []
        return [str(v).strip() for v in values if str(v).strip()]

    def classify_reason(self, metadata, api_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Return popcorn reason code when popcorn criteria are met, otherwise None.
        """
        film_year = getattr(metadata, 'year', None)
        if film_year is None:
            return None

        title_lower = (getattr(metadata, 'title', '') or '').lower()
        if any(keyword in title_lower for keyword in EXPLOITATION_TITLE_KEYWORDS):
            return None

        api_data = api_data or {}
        countries = set(self._normalize_list(api_data.get('countries')))
        genres = set(self._normalize_list(api_data.get('genres')))
        cast = [c.lower() for c in self._normalize_list(api_data.get('cast'))]
        popularity = api_data.get('popularity')
        vote_count = api_data.get('vote_count')

        format_signals = [s.lower() for s in self._normalize_list(getattr(metadata, 'format_signals', []))]
        has_strong_format = any(sig in self.strong_format_signals for sig in format_signals)
        has_mainstream_country = bool(countries & self.mainstream_countries)
        has_mainstream_genre = bool(genres & self.mainstream_genres)
        has_star_actor = any(actor in self.star_actors for actor in cast)
        has_popularity = (
            (isinstance(popularity, (int, float)) and popularity >= self.min_popularity) or
            (isinstance(vote_count, int) and vote_count >= self.min_vote_count)
        )

        if has_mainstream_country and has_mainstream_genre and (has_star_actor or has_popularity):
            return 'popcorn_cast_popularity'
        if has_mainstream_country and has_mainstream_genre and has_strong_format:
            return 'popcorn_format_mainstream'
        if has_strong_format and (has_star_actor or has_popularity):
            return 'popcorn_format_plus_popularity'

        return None

    def is_popcorn(self, metadata, year: Optional[int] = None) -> bool:
        """
        Backward-compatible boolean API.

        Args:
            metadata: FilmMetadata object with title, year, format_signals
            year: Optional override year (if not in metadata)

        Returns:
            True if film should be classified as Popcorn
        """
        if year is not None and getattr(metadata, 'year', None) is None:
            metadata.year = year
        return self.classify_reason(metadata, None) is not None
