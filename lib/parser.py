#!/usr/bin/env python3
"""
Filename parser for extracting film metadata from various filename patterns
"""

import re
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass, field


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

    # Format/edition signals that indicate special curation
    FORMAT_SIGNALS = [
        '35mm', 'open matte', 'extended', "director's cut", "editor's cut",
        'unrated', 'redux', 'final cut', 'theatrical', 'criterion',
        '4k', 'uhd', 'remux', 'commentary', 'special edition', '16mm', '2k',
        'remastered', 'restored', 'anniversary'
    ]

    # Release group tags to strip from titles
    RELEASE_TAGS = [
        'bluray', 'bdrip', 'brrip', 'web-dl', 'webrip', 'dvdrip', 'hdrip',
        'x264', 'x265', 'h264', 'h265', 'hevc', 'aac', 'ac3', 'dts',
        '1080p', '720p', '2160p', '4k', 'uhd', 'hd',
        'yify', 'rarbg', 'vxt', 'tigole', 'amzn', 'nf', 'hulu',
        'remastered', 'restored', 'anniversary', 'repack'
    ]

    def _clean_title(self, title: str) -> str:
        """Clean and normalize title from various filename formats"""
        # Replace dots/underscores with spaces (scene release format)
        title = title.replace('.', ' ').replace('_', ' ')

        # Remove release group tags and quality indicators
        title_lower = title.lower()
        for tag in self.RELEASE_TAGS:
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
        """Extract metadata from filename"""
        # Remove file extension
        name = Path(filename).stem

        # Extract format signals
        format_signals = []
        name_lower = name.lower()
        for signal in self.FORMAT_SIGNALS:
            if signal in name_lower:
                format_signals.append(signal)

        # Try Brazilian year-prefix format first: "1976 - Amadas e Violentadas"
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

        # Try structured patterns with director
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

        # Try title + year patterns
        for pattern in self.PATTERNS[3:]:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:  # (title, year)
                    title, year = groups
                    return FilmMetadata(
                        filename=filename,
                        title=self._clean_title(title),
                        year=int(year),
                        format_signals=format_signals
                    )

        # Fallback: try to extract year from anywhere in filename
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

        # Last resort: just use filename as title (year will be None)
        return FilmMetadata(
            filename=filename,
            title=self._clean_title(name),
            format_signals=format_signals
        )
