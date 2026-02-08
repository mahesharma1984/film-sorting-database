#!/usr/bin/env python3
"""
Core director whitelist database with EXACT matching only (v0.1 simplification)

Key changes from core_directors.py:
- NO fuzzy matching (no fuzz.ratio, no substring, no last-name matching)
- Exact case-insensitive string match only
- O(1) lookup performance with dictionary
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, Set

logger = logging.getLogger(__name__)


class CoreDirectorDatabase:
    """Load and query Core director whitelist - EXACT MATCH ONLY"""

    def __init__(self, whitelist_file: Path):
        # Structure: {'1960s': {'Jean-Luc Godard', 'Pier Paolo Pasolini', ...}, ...}
        self.directors_by_decade: Dict[str, Set[str]] = {}

        # All directors in lowercase for case-insensitive exact matching
        # Maps: lowercase name → canonical name
        self.director_lookup: Dict[str, str] = {}

        self._load_whitelist(whitelist_file)

    def _load_whitelist(self, file_path: Path):
        """Parse the Core director whitelist markdown file"""
        if not file_path.exists():
            logger.error(f"Core director whitelist not found: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            current_decade = None

            for line in content.split('\n'):
                line = line.strip()

                # Detect decade headers: "## 1960s CORE"
                if re.match(r'## \d{4}s CORE', line):
                    decade_match = re.search(r'(\d{4}s)', line)
                    if decade_match:
                        current_decade = decade_match.group(1)
                        if current_decade not in self.directors_by_decade:
                            self.directors_by_decade[current_decade] = set()
                        continue

                # Extract director names: "**Jean-Luc Godard**"
                director_match = re.match(r'\*\*([^*]+)\*\*', line)
                if director_match and current_decade:
                    director = director_match.group(1).strip()

                    # Add to decade set
                    self.directors_by_decade[current_decade].add(director)

                    # Build lowercase lookup (for exact case-insensitive matching)
                    director_key = director.lower().strip()
                    self.director_lookup[director_key] = director

            total = sum(len(d) for d in self.directors_by_decade.values())
            logger.info(f"Loaded {total} core directors across {len(self.directors_by_decade)} decades (exact match only)")

        except Exception as e:
            logger.error(f"Error loading core director whitelist: {e}")

    def is_core_director(self, director_name: str) -> bool:
        """
        Check if director is in Core whitelist - EXACT MATCH ONLY (case-insensitive)

        NO fuzzy matching, NO substring matching, NO last-name matching
        This is intentional to avoid false positives.
        """
        if not director_name:
            return False

        director_key = director_name.lower().strip()
        return director_key in self.director_lookup

    def get_canonical_name(self, director_name: str) -> Optional[str]:
        """
        Get canonical director name from whitelist (for folder naming)

        Returns the exact name as it appears in CORE_DIRECTOR_WHITELIST_FINAL.md
        """
        if not director_name:
            return None

        director_key = director_name.lower().strip()
        return self.director_lookup.get(director_key)

    def get_director_decade(self, director_name: str, film_year: int) -> Optional[str]:
        """
        Get decade folder for director based on film year

        Validates that:
        1. Director is in whitelist
        2. Director appears in the decade corresponding to film_year

        Returns decade string (e.g., "1960s") or None if validation fails
        """
        canonical = self.get_canonical_name(director_name)
        if not canonical:
            return None

        # Calculate decade from film year
        decade = f"{(film_year // 10) * 10}s"

        # Verify director appears in this decade's whitelist
        if decade in self.directors_by_decade and canonical in self.directors_by_decade[decade]:
            return decade

        # Director exists but not in this decade
        logger.debug(f"Director '{canonical}' not listed in {decade} (film year: {film_year})")
        return None
