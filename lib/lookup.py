#!/usr/bin/env python3
"""
Explicit lookup table parser for SORTING_DATABASE.md

Parses hand-classified films and creates a lookup table for exact matches.
This bypasses all heuristics for ~277 known films.
"""

import re
import logging
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Tuple, List

from lib.normalization import normalize_for_lookup

logger = logging.getLogger(__name__)


class SortingDatabaseLookup:
    """Parse SORTING_DATABASE.md into title+year → destination lookup table"""

    def __init__(self, database_path: Path):
        self.lookup_table: Dict[Tuple[str, Optional[int]], str] = {}
        self.conflicts: List[Dict] = []  # Track films with multiple destinations
        self.entry_count = 0
        self._parse_database(database_path)

    # NOTE: Normalization methods removed - now using shared normalize_for_lookup()
    # from lib.normalization to ensure symmetric normalization between database
    # building and querying. This fixes the critical asymmetric normalization bug.

    def _parse_database(self, file_path: Path):
        """Parse SORTING_DATABASE.md"""
        if not file_path.exists():
            logger.warning(f"SORTING_DATABASE.md not found at {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Patterns for different entry formats
            # Standard: "- Title (Year) ... → Destination/"
            pattern_standard = r'^-\s+(.+?)\s+\((\d{4})\).*?→\s+(.+?)/?$'

            # Year prefix: "- Year - Title → Destination/"
            pattern_year_prefix = r'^-\s+(\d{4})\s+-\s+(.+?)\s+→\s+(.+?)/?$'

            # No year: "- Title → Destination/"
            pattern_no_year = r'^-\s+([^→]+?)\s+→\s+(.+?)/?$'

            for line in content.split('\n'):
                line = line.strip()

                # Skip empty lines, comments, headers, and notes
                if not line or not line.startswith('-'):
                    continue

                # Skip lines with notes/comments
                if '[NOTE' in line or '[BORDER' in line or '[Wrong' in line or '[OR ' in line:
                    continue

                # Try standard format first: "Title (Year) → Destination"
                match = re.match(pattern_standard, line)
                if match:
                    title_raw, year_str, dest = match.groups()
                    # Use shared normalization with format signal stripping
                    title = normalize_for_lookup(title_raw, strip_format_signals=True)
                    year = int(year_str)
                    dest = dest.strip()

                    if not self._is_valid_destination(dest):
                        logger.debug(f"Skipping invalid/ambiguous destination: {dest}")
                        continue

                    self._add_entry(title, year, dest, line)
                    continue

                # Try year-prefix format: "Year - Title → Destination"
                match = re.match(pattern_year_prefix, line)
                if match:
                    year_str, title_raw, dest = match.groups()
                    # Use shared normalization with format signal stripping
                    title = normalize_for_lookup(title_raw, strip_format_signals=True)
                    year = int(year_str)
                    dest = dest.strip()

                    if not self._is_valid_destination(dest):
                        logger.debug(f"Skipping invalid/ambiguous destination: {dest}")
                        continue

                    self._add_entry(title, year, dest, line)
                    continue

                # Try no-year format: "Title → Destination"
                match = re.match(pattern_no_year, line)
                if match:
                    title_raw, dest = match.groups()
                    # Use shared normalization with format signal stripping
                    title = normalize_for_lookup(title_raw, strip_format_signals=True)
                    dest = dest.strip()

                    if not self._is_valid_destination(dest):
                        logger.debug(f"Skipping invalid/ambiguous destination: {dest}")
                        continue

                    # Skip if destination contains year (likely parsing error)
                    if '(' in title_raw and ')' in title_raw:
                        continue

                    self._add_entry(title, None, dest, line)
                    continue

            logger.info(f"Loaded {self.entry_count} explicit film mappings from SORTING_DATABASE.md")

            if self.conflicts:
                logger.warning(f"Found {len(self.conflicts)} films with conflicting destinations")

        except Exception as e:
            logger.error(f"Error parsing SORTING_DATABASE.md: {e}")

    def _is_valid_destination(self, destination: str) -> bool:
        """
        Validate destination path from SORTING_DATABASE.md.

        Rejects unresolved alternatives like "Reference OR Popcorn?".
        """
        if not destination:
            return False

        normalized = destination.strip().strip('/')
        lowered = normalized.lower()

        if '?' in normalized or ' or ' in lowered:
            return False

        tier_first = re.match(
            r'^(Core|Reference|Satellite|Popcorn|Staging|Unsorted)(/[^/].*)?$',
            normalized
        )
        decade_first = re.match(
            r'^(19|20)\d{2}s/(Core|Reference|Satellite|Popcorn)(/[^/].*)?$',
            normalized
        )
        return bool(tier_first or decade_first)

    def _add_entry(self, title: str, year: Optional[int], destination: str, source_line: str):
        """Add entry to lookup table, track conflicts"""
        key = (title, year)

        # Check for duplicates
        if key in self.lookup_table:
            existing_dest = self.lookup_table[key]
            if existing_dest != destination:
                self.conflicts.append({
                    'title': title,
                    'year': year,
                    'dest1': existing_dest,
                    'dest2': destination,
                    'line': source_line
                })
                logger.warning(f"Conflict: '{title}' ({year}) → {existing_dest} vs {destination}")
            # Keep first occurrence
            return

        self.lookup_table[key] = destination
        self.entry_count += 1

    def lookup(self, title: str, year: Optional[int]) -> Optional[str]:
        """
        Look up destination for title+year

        CRITICAL: Uses identical normalization as database building (symmetric)
        This ensures format signals don't block lookup matches

        Returns destination path if found, None otherwise
        """
        # Use SAME normalization as database building (with format signal stripping)
        normalized = normalize_for_lookup(title, strip_format_signals=True)

        # Exact match with year
        key = (normalized, year)
        if key in self.lookup_table:
            logger.debug(f"Lookup hit: '{title}' ({year}) → normalized: '{normalized}'")
            return self.lookup_table[key]

        # Try without year if year was provided
        if year is not None:
            key_no_year = (normalized, None)
            if key_no_year in self.lookup_table:
                logger.debug(f"Lookup hit (no year): '{title}' → normalized: '{normalized}'")
                return self.lookup_table[key_no_year]

        # No match
        logger.debug(f"Lookup miss: '{title}' ({year}) → normalized: '{normalized}'")
        return None

    def get_stats(self) -> Dict:
        """Get lookup table statistics"""
        entries_with_year = sum(1 for k in self.lookup_table.keys() if k[1] is not None)
        entries_without_year = sum(1 for k in self.lookup_table.keys() if k[1] is None)

        return {
            'total_entries': self.entry_count,
            'entries_with_year': entries_with_year,
            'entries_without_year': entries_without_year,
            'conflicts': len(self.conflicts)
        }
