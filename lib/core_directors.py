#!/usr/bin/env python3
"""
Core director whitelist database with fuzzy matching
Extracted from film_sorter.py lines 194-288
"""

import re
import logging
from pathlib import Path
from typing import Set, List
from collections import defaultdict

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class CoreDirectorDatabase:
    """Load and query Core director whitelist"""

    def __init__(self, whitelist_file: Path):
        self.directors_by_decade = defaultdict(set)
        self.all_directors = set()
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

                # Detect decade headers
                if re.match(r'## \d{4}s CORE', line):
                    decade_match = re.search(r'(\d{4})s', line)
                    if decade_match:
                        current_decade = decade_match.group(1) + 's'
                        continue

                # Extract director names (bold text)
                director_match = re.match(r'\*\*([^*]+)\*\*', line)
                if director_match and current_decade:
                    director = director_match.group(1).strip()
                    self.directors_by_decade[current_decade].add(director)
                    self.all_directors.add(director)

            logger.info(f"Loaded {len(self.all_directors)} core directors across {len(self.directors_by_decade)} decades")

        except Exception as e:
            logger.error(f"Error loading core director whitelist: {e}")

    def is_core_director(self, director_name: str) -> bool:
        """Check if director is in Core whitelist (fuzzy matching)"""
        if not director_name:
            return False

        director_lower = director_name.lower().strip()

        # Exact match first
        for core_director in self.all_directors:
            if director_lower == core_director.lower():
                return True

        # Fuzzy matching for variations
        for core_director in self.all_directors:
            core_lower = core_director.lower()

            # High similarity match
            if fuzz.ratio(director_lower, core_lower) > 85:
                return True

            # Partial match for shortened names (e.g. "Godard" matches "Jean-Luc Godard")
            if len(director_lower) > 3 and director_lower in core_lower:
                return True

            # Check if last name matches
            core_parts = core_lower.split()
            director_parts = director_lower.split()

            if len(core_parts) > 1 and len(director_parts) > 0:
                if director_parts[-1] == core_parts[-1]:  # Last name match
                    return True

        return False

    def get_director_decades(self, director_name: str) -> List[str]:
        """Get decades where director appears in Core whitelist"""
        if not director_name:
            return []

        decades = []
        director_lower = director_name.lower().strip()

        for decade, directors in self.directors_by_decade.items():
            for core_director in directors:
                core_lower = core_director.lower()

                # Check multiple matching strategies
                if (director_lower == core_lower or
                    fuzz.ratio(director_lower, core_lower) > 85 or
                    (len(director_lower) > 3 and director_lower in core_lower) or
                    (len(director_lower.split()) > 0 and len(core_lower.split()) > 1 and
                     director_lower.split()[-1] == core_lower.split()[-1])):
                    decades.append(decade)
                    break

        return decades

    def get_canonical_director_name(self, director_name: str) -> str:
        """Get canonical director name from whitelist (for folder naming)"""
        if not director_name:
            return director_name

        director_lower = director_name.lower().strip()

        # Try exact match first
        for core_director in self.all_directors:
            if director_lower == core_director.lower():
                return core_director

        # Try fuzzy match
        for core_director in self.all_directors:
            core_lower = core_director.lower()

            if fuzz.ratio(director_lower, core_lower) > 85:
                return core_director

            if len(director_lower) > 3 and director_lower in core_lower:
                return core_director

            # Last name match
            core_parts = core_lower.split()
            director_parts = director_lower.split()
            if len(core_parts) > 1 and len(director_parts) > 0:
                if director_parts[-1] == core_parts[-1]:
                    return core_director

        # No match - return original
        return director_name
