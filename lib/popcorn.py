#!/usr/bin/env python3
"""
Popcorn tier classification via format signals + lookup
"""

import logging
from typing import Optional

from lib.constants import FORMAT_SIGNALS

logger = logging.getLogger(__name__)


class PopcornClassifier:
    """Classify Popcorn tier films based on format signals"""

    def __init__(self, lookup_db=None):
        # Use shared format signals from constants.py (single source of truth)
        self.format_signals = FORMAT_SIGNALS
        self.lookup_db = lookup_db

    def is_popcorn(self, metadata, year: Optional[int] = None) -> bool:
        """
        Check if film is Popcorn tier

        Args:
            metadata: FilmMetadata object with title, year, format_signals
            year: Optional override year (if not in metadata)

        Returns:
            True if film should be classified as Popcorn
        """
        # Get year from metadata or parameter
        film_year = getattr(metadata, 'year', None) or year

        # Check explicit lookup first (many Popcorn films in SORTING_DATABASE.md)
        if self.lookup_db and hasattr(metadata, 'title'):
            dest = self.lookup_db.lookup(metadata.title, film_year)
            if dest and 'Popcorn' in dest:
                logger.debug(f"Popcorn via explicit lookup: {metadata.title}")
                return True

        # Check format signals
        if hasattr(metadata, 'format_signals') and metadata.format_signals:
            for signal in self.format_signals:
                if signal.lower() in [s.lower() for s in metadata.format_signals]:
                    logger.debug(f"Popcorn via format signal '{signal}': {metadata.title}")
                    return True

        return False
