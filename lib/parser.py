#!/usr/bin/env python3
"""
Filename parser for extracting film metadata from various filename patterns
"""

import re
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass, field

from lib.constants import FORMAT_SIGNALS, RELEASE_TAGS


@dataclass
class FilmMetadata:
    """Container for film metadata extracted from filename or API"""
    filename: str
    title: str
    year: Optional[int] = None
    director: Optional[str] = None
    edition: Optional[str] = None  # 35mm, Open Matte, Extended, etc.
    format_signals: List[str] = field(default_factory=list)


class FilenameParser:
    """Parse film metadata from various filename patterns"""

    # Common filename patterns - order matters!
    PATTERNS = [
        r'^(.+?)\s+-\s+(.+?)\s+\((\d{4})\)',        # Director - Film Title (Year)
        r'^(.+?)\s+-\s+(.+?)\s+(\d{4})',            # Director - Film Title Year
        r'^(\d{4})\s+-\s+(.+)',                     # Year - Film Title (Brazilian format)
        r'^(.+?)\s*\((\d{4})\)',                    # Film Title (Year)
        r'^(.+?)\s*\[(\d{4})\]',                    # Film Title [Year]
        r'^(.+?)\s+(\d{4})(?!\d)',                  # Film Title Year (not followed by more digits)
    ]

    # Note: FORMAT_SIGNALS and RELEASE_TAGS are now imported from lib.constants
    # to maintain single source of truth across all modules

    def _clean_title(self, title: str) -> str:
        """Clean and normalize title from various filename formats"""
        # Replace dots/underscores with spaces (scene release format)
        title = title.replace('.', ' ').replace('_', ' ')

        # Remove release group tags and quality indicators
        title_lower = title.lower()
        for tag in RELEASE_TAGS:  # Use imported constant
            # Find tag and remove everything after it
            idx = title_lower.find(tag)
            if idx != -1:
                title = title[:idx]
                title_lower = title_lower[:idx]

        # Clean up extra spaces
        title = ' '.join(title.split())

        # Strip and return
        title = title.strip()

        return title

    def _extract_year(self, name: str) -> Optional[Tuple[int, str]]:
        """Extract year from filename, returns (year, cleaned_name) or None"""
        # Try multiple year patterns in order of specificity
        year_patterns = [
            r'\((\d{4})\)',           # (1999)
            r'\[(\d{4})\]',           # [1969]
            r'[\.\s](\d{4})[\.\s]',   # .1984. or space-delimited
        ]

        for pattern in year_patterns:
            match = re.search(pattern, name)
            if match:
                year = int(match.group(1))
                # Validate year range (avoid matching resolutions like 1080, 2160)
                if 1920 <= year <= 2029:
                    # Remove the year from the name for cleaner title
                    # Add space when joining to prevent title concatenation
                    cleaned = name[:match.start()].strip() + ' ' + name[match.end():].strip()
                    cleaned = cleaned.strip()
                    return year, cleaned

        return None

    def parse(self, filename: str) -> FilmMetadata:
        """
        Extract metadata from filename

        CRITICAL FIX: Checks for parenthetical year FIRST before other patterns
        to avoid extracting leading digits as year (e.g., "2001 - A Space Odyssey (1968)")
        """
        # Remove file extension
        name = Path(filename).stem

        # Extract format signals (using imported constant)
        format_signals = []
        name_lower = name.lower()
        for signal in FORMAT_SIGNALS:
            if signal in name_lower:
                format_signals.append(signal)

        # === PRIORITY 1: Check for parenthetical year FIRST ===
        # This must come before Brazilian year-prefix to avoid "2001 - Film (1968)" bug
        paren_year_match = re.search(r'\((\d{4})\)', name)
        if paren_year_match:
            year = int(paren_year_match.group(1))
            if 1920 <= year <= 2029:
                # Remove (YEAR) from title for cleaner extraction
                # This prevents the year from appearing in the cleaned title
                title_without_year = re.sub(r'\s*\(\d{4}\)\s*', ' ', name)
                title = self._clean_title(title_without_year)

                # Check if this also matches director pattern
                # Pattern: "Director - Title (Year)"
                director_match = re.match(r'^(.+?)\s+-\s+(.+)', name)
                if director_match:
                    potential_director, potential_title = director_match.groups()

                    # Don't treat as director if it's a 4-digit number (year)
                    # Fixes: "2001 - A Space Odyssey (1968)" where "2001" is part of title, not director
                    if re.match(r'^\d{4}$', potential_director.strip()):
                        # This is a year, not a director - skip director extraction
                        pass
                    else:
                        # Clean the potential title (remove year from it)
                        potential_title = re.sub(r'\s*\(\d{4}\)\s*', ' ', potential_title)
                        potential_title = self._clean_title(potential_title)

                        # Only treat as director if it's short and clean
                        if len(potential_director.split()) <= 3 and not any(
                            tag in potential_director.lower() for tag in ['1080p', '720p', 'bluray', 'x264', 'x265']
                        ):
                            return FilmMetadata(
                                filename=filename,
                                title=potential_title,
                                year=year,
                                director=potential_director.strip(),
                                format_signals=format_signals
                            )

                return FilmMetadata(
                    filename=filename,
                    title=title,
                    year=year,
                    format_signals=format_signals
                )

        # === PRIORITY 2: Brazilian year-prefix format ===
        # Now safe to check: "1976 - Amadas e Violentadas"
        # (Won't match "2001 - Film (1968)" because parens were checked first)
        year_prefix_match = re.match(r'^(\d{4})\s+-\s+(.+)', name)
        if year_prefix_match:
            year_str, title = year_prefix_match.groups()
            year = int(year_str)
            if 1920 <= year <= 2029:
                return FilmMetadata(
                    filename=filename,
                    title=self._clean_title(title),
                    year=year,
                    format_signals=format_signals
                )

        # === PRIORITY 3: Structured patterns with director ===
        for i, pattern in enumerate(self.PATTERNS[:2]):  # First 2 are director patterns
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # (director, title, year)
                    director, title, year = groups
                    return FilmMetadata(
                        filename=filename,
                        title=self._clean_title(title),
                        year=int(year),
                        director=director.strip(),
                        format_signals=format_signals
                    )

        # === PRIORITY 4: Title + year patterns (bracket year) ===
        # Check [YEAR] format
        bracket_year_match = re.search(r'\[(\d{4})\]', name)
        if bracket_year_match:
            year = int(bracket_year_match.group(1))
            if 1920 <= year <= 2029:
                title_without_year = re.sub(r'\s*\[\d{4}\]\s*', ' ', name)
                title = self._clean_title(title_without_year)
                return FilmMetadata(
                    filename=filename,
                    title=title,
                    year=year,
                    format_signals=format_signals
                )

        # === PRIORITY 5: Fallback - extract year from anywhere ===
        year_result = self._extract_year(name)
        if year_result:
            year, cleaned_name = year_result
            title = self._clean_title(cleaned_name)
            return FilmMetadata(
                filename=filename,
                title=title,
                year=year,
                format_signals=format_signals
            )

        # === LAST RESORT: No year found ===
        return FilmMetadata(
            filename=filename,
            title=self._clean_title(name),
            format_signals=format_signals
        )
