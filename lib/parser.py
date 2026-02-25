#!/usr/bin/env python3
"""
Filename parser for extracting film metadata from various filename patterns
"""

import re
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass, field

from lib.constants import (
    FORMAT_SIGNALS, RELEASE_TAGS, LANGUAGE_PATTERNS,
    LANGUAGE_TO_COUNTRY, SUBTITLE_KEYWORDS, NON_FILM_PREFIXES
)


@dataclass
class FilmMetadata:
    """Container for film metadata extracted from filename or API"""
    filename: str
    title: str
    year: Optional[int] = None
    director: Optional[str] = None
    edition: Optional[str] = None  # 35mm, Open Matte, Extended, etc.
    format_signals: List[str] = field(default_factory=list)
    language: Optional[str] = None  # ISO 639-1 code (e.g., 'pt', 'it', 'fr')
    country: Optional[str] = None   # ISO 3166-1 alpha-2 (e.g., 'BR', 'IT', 'FR')
    user_tag: Optional[str] = None  # Raw user tag content without brackets


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
        # Strip leading collection/archive tags like [AS3 Archive], [HKL], etc.
        # (Year-only brackets like [1969] are handled by PRIORITY 4 before we get here)
        title = re.sub(r'^\[[^\]]+\]\s*', '', title)

        # Remove Plex/Emby edition tags like {edition-Uncut} or {tmdb-12345}
        title = re.sub(r'\s*\{[^}]+\}', '', title)

        # Replace dots/underscores with spaces (scene release format)
        title = title.replace('.', ' ').replace('_', ' ')

        # Remove release group tags and quality indicators.
        # Use non-alphanumeric boundary matching so short tags like "nf", "hd", "aac"
        # don't truncate real words ("conformist", "shadow", "isaac", etc.)
        title_lower = title.lower()
        for tag in RELEASE_TAGS:  # Use imported constant
            pattern = r'(?<![a-zA-Z0-9])' + re.escape(tag) + r'(?![a-zA-Z0-9])'
            match = re.search(pattern, title_lower)
            if match:
                idx = match.start()
                title = title[:idx]
                title_lower = title_lower[:idx]

        # Strip long parenthetical blocks — AKA titles, format/quality metadata, etc.
        # e.g. "The Eroticist (Nonostante le apparenze... e purchè...)" → "The Eroticist"
        #      "Varsity Blues (1080p BluRay x265 10bit Tigole)" → "Varsity Blues"
        # Heuristic: parenthetical content > 15 chars is metadata, not part of core title.
        title = re.sub(r'\s*\([^)]{16,}\)', '', title)

        # Strip trailing open parenthetical fragments — happen when _extract_year truncates
        # a filename before the year inside a paren, e.g.:
        # "Assim Te Quero Meu Amor (I Like It Like That -" → "Assim Te Quero Meu Amor"
        title = re.sub(r'\s*\([^)]*$', '', title)

        # Strip any trailing bracket fragment left by RELEASE_TAGS truncation
        # e.g. "The Eroticist [" or "Title [720p" after tag match stripped content mid-bracket
        title = re.sub(r'\s*\[[^\]]*$', '', title)

        # Clean up extra spaces
        title = ' '.join(title.split())

        # Strip and return
        title = title.strip()

        return title

    def _extract_year(self, name: str) -> Optional[Tuple[int, str]]:
        """Extract year from filename, returns (year, cleaned_name) or None"""
        # Try multiple year patterns in order of specificity
        year_patterns = [
            r'\s+(\d{4})$',           # Issue #5 fix: Bare year at end (sermon to the fish 2022)
            r'\.(\d{4})$',            # .1972 at end of dotted filename (Black.Girl.1972)
            r'\((\d{4})\)',           # (1999)
            r'\[(\d{4})\]',           # [1969]
            r'[\.\s](\d{4})[\.\s]',   # .1984. or space-delimited
            r'\-(\d{4})\-',                   # -1984- hyphen-delimited (YTS/scene format)
        ]

        for pattern in year_patterns:
            match = re.search(pattern, name)
            if match:
                year = int(match.group(1))
                # Validate year range (avoid matching resolutions like 1080, 2160)
                if 1920 <= year <= 2029:
                    # Return only the pre-year portion as the title candidate.
                    # Scene-release filenames use Title.Year.TechSpecs — everything
                    # after the year is codec/language/resolution metadata (JAPANESE,
                    # VOSTFR, 576p, etc.) and must not appear in the extracted title.
                    cleaned = name[:match.start()].strip()
                    return year, cleaned

        return None

    def _extract_language(self, filename: str) -> Optional[str]:
        """Extract language from filename using LANGUAGE_PATTERNS"""
        filename_lower = filename.lower()
        for pattern, lang_code, country_code in LANGUAGE_PATTERNS:
            if re.search(pattern, filename_lower):
                return lang_code
        return None

    def _map_language_to_country(self, language: Optional[str]) -> Optional[str]:
        """Map language code to country code"""
        if not language:
            return None
        return LANGUAGE_TO_COUNTRY.get(language)

    def _extract_user_tag(self, filename: str) -> Optional[str]:
        """Extract user-applied classification tags like [Popcorn-1970s]"""
        match = re.search(r'\[([^\]]+)\]', filename)
        if match:
            tag_content = match.group(1)

            # Validate it's a classification tag
            valid_prefixes = ['Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted']
            if any(tag_content.startswith(prefix) for prefix in valid_prefixes):
                return tag_content
            # Also check for decade prefix like "1970s-Satellite"
            if re.match(r'(19|20)\d{2}s-', tag_content):
                return tag_content

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

        # Extract language and country
        language = self._extract_language(filename)
        country = self._map_language_to_country(language)

        # Extract user tag
        user_tag = self._extract_user_tag(filename)

        # Strip validated classification tags from name so they don't contaminate
        # title extraction (e.g., "[1970s-Core-Jean-Pierre Melville]" must not end up
        # in the title string that gets fed to the lookup table).
        if user_tag:
            name = re.sub(r'\s*\[[^\]]+\]', '', name).strip()

        # === PRIORITY 0: Check for (Director, Year) pattern FIRST ===
        # Bug 3 fix: "A Bay of Blood (Mario Bava, 1971).mkv"
        # This must come before standard parenthetical year to extract both director and year
        director_year_match = re.search(r'\(([A-Z][^,)]+),\s*(\d{4})\)', name)
        if director_year_match:
            director_name, year_str = director_year_match.groups()
            year = int(year_str)

            if 1920 <= year <= 2029:
                # Remove (Director, Year) from title — [^,)] prevents crossing paren boundaries
                title_part = re.sub(r'\s*\([^,)]+,\s*\d{4}\)', '', name)
                title = self._clean_title(title_part)

                return FilmMetadata(
                    filename=filename,
                    title=title,
                    year=year,
                    director=director_name.strip(),
                    format_signals=format_signals,
                    language=language,
                    country=country,
                    user_tag=user_tag
                )

        # === PRIORITY 0.5: Check for (Director YYYY) pattern (no comma) ===
        # Issue #5 fix: "Ed Wood (Tim Burton 1994)" should extract director and year
        # This pattern handles cases where director and year are in parentheses without a comma
        director_year_no_comma_match = re.search(r'\(([A-Z][^\d\)]+?)\s+(\d{4})\)', name)
        if director_year_no_comma_match:
            director_name, year_str = director_year_no_comma_match.groups()
            year = int(year_str)

            if 1920 <= year <= 2029:
                # Remove (Director Year) from title
                title_part = re.sub(r'\s*\([^\)]+\s+\d{4}\)', '', name)
                title = self._clean_title(title_part)

                return FilmMetadata(
                    filename=filename,
                    title=title,
                    year=year,
                    director=director_name.strip(),
                    format_signals=format_signals,
                    language=language,
                    country=country,
                    user_tag=user_tag
                )

        # === PRIORITY 1: Check for parenthetical year FIRST ===
        # This must come before Brazilian year-prefix to avoid "2001 - Film (1968)" bug
        #
        # Two sub-cases:
        #   Clean:  (YYYY)               — year alone, proceed with director extraction
        #   Messy:  (YYYY - extra text)  — year with quality/lang info, skip director extraction
        #
        paren_year_match = re.search(r'\((\d{4})[^)]*\)', name)
        if paren_year_match:
            year = int(paren_year_match.group(1))
            if 1920 <= year <= 2029:
                # Remove the whole parenthetical containing the year from title
                title_without_year = re.sub(r'\s*\(\d{4}[^)]*\)\s*', ' ', name)
                title = self._clean_title(title_without_year)

                # Only attempt director extraction for "clean" paren years — (YYYY) alone.
                # Messy parens like (1975 - 360p - Português) contain " - " inside the paren;
                # matching on the full name would mis-extract the quality tag as a title part.
                is_clean_paren = bool(re.search(r'\((\d{4})\)', name))

                # Check if this also matches director pattern
                # Pattern: "Director - Title (Year)"
                director_match = re.match(r'^(.+?)\s+-\s+(.+)', name) if is_clean_paren else None
                if director_match:
                    potential_director, potential_title = director_match.groups()

                    # Don't treat as director if it's a 4-digit number (year)
                    # Fixes: "2001 - A Space Odyssey (1968)" where "2001" is part of title, not director
                    if re.match(r'^\d{4}$', potential_director.strip()):
                        # This is a year, not a director - skip director extraction
                        pass
                    # Bug 1 fix: Don't treat as director if it contains (YYYY...)
                    # Fixes: "Casablanca (1942) - 4K" where "Casablanca (1942)" should be title
                    elif re.search(r'\(\d{4}[^)]*\)', potential_director):
                        # This contains a year in parens, it's the title not director
                        # Extract just the title part (potential_director without year)
                        title_only = re.sub(r'\s*\(\d{4}[^)]*\)\s*', '', potential_director)
                        title = self._clean_title(title_only)
                        pass
                    else:
                        # Clean the potential title (remove year from it)
                        potential_title = re.sub(r'\s*\(\d{4}[^)]*\)\s*', ' ', potential_title)
                        potential_title = self._clean_title(potential_title)

                        # Bug 2 fix: Check if potential_title looks like a subtitle
                        # Fixes: "Cinema Paradiso - Theatrical Cut (1988)" should NOT extract director
                        potential_title_lower = potential_title.lower()
                        is_subtitle = any(keyword in potential_title_lower for keyword in SUBTITLE_KEYWORDS)

                        if is_subtitle:
                            # This is "Title - Subtitle (Year)", not "Director - Title (Year)"
                            # Skip director extraction
                            pass
                        # Issue #20: Non-film content prefix gate
                        # "Interview - Rodney Hill (2014)" → prefix is content type, not director
                        elif potential_director.strip().lower() in NON_FILM_PREFIXES:
                            # Supplementary content — no director, title from right side
                            title = potential_title.strip()
                            # fall through to return without director
                        # Only treat as director if it's short and clean
                        elif len(potential_director.split()) <= 3 and not any(
                            tag in potential_director.lower() for tag in ['1080p', '720p', 'bluray', 'x264', 'x265']
                        ):
                            return FilmMetadata(
                                filename=filename,
                                title=potential_title,
                                year=year,
                                director=potential_director.strip(),
                                format_signals=format_signals,
                                language=language,
                                country=country,
                                user_tag=user_tag
                            )

                return FilmMetadata(
                    filename=filename,
                    title=title,
                    year=year,
                    format_signals=format_signals,
                    language=language,
                    country=country,
                    user_tag=user_tag
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
                    format_signals=format_signals,
                    language=language,
                    country=country,
                    user_tag=user_tag
                )

        # === PRIORITY 3: Structured patterns with director ===
        for i, pattern in enumerate(self.PATTERNS[:2]):  # First 2 are director patterns
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # (director, title, year)
                    director, title, year = groups
                    year_int = int(year)
                    # Validate year range — prevents resolution numbers like 1080 being
                    # captured as year (e.g. "Title - 1994 - 1080p" → year=1080 bug)
                    if not (1920 <= year_int <= 2029):
                        continue
                    # Validate director — collection tags like "[AS3 Archive]" are not directors
                    if re.search(r'[\[\]]', director):
                        continue
                    return FilmMetadata(
                        filename=filename,
                        title=self._clean_title(title),
                        year=year_int,
                        director=director.strip(),
                        format_signals=format_signals,
                        language=language,
                        country=country,
                        user_tag=user_tag
                    )

        # === PRIORITY 4: Title + year patterns (bracket year) ===
        # Check [YEAR] and [YEAR, ...] formats (e.g. [AS3 Archive] Lady Snowblood [1973, 1920x816p...])
        bracket_year_match = re.search(r'\[(\d{4})[\],]', name)
        if bracket_year_match:
            year = int(bracket_year_match.group(1))
            if 1920 <= year <= 2029:
                # Remove the entire bracket block containing the year (handles [YYYY] and [YYYY, extra])
                title_without_year = re.sub(r'\s*\[\d{4}[^\]]*\]\s*', ' ', name)
                title = self._clean_title(title_without_year)
                return FilmMetadata(
                    filename=filename,
                    title=title,
                    year=year,
                    format_signals=format_signals,
                    language=language,
                    country=country,
                    user_tag=user_tag
                )

        # === PRIORITY 5: Fallback - extract year from anywhere ===
        year_result = self._extract_year(name)
        if year_result:
            year, cleaned_name = year_result
            title = self._clean_title(cleaned_name)
            # Hyphen-delimited filenames (YTS/scene): replace hyphens with spaces in title
            # Safe here because PRIORITY 5 only fires after all structured patterns fail
            if '-' in title:
                title = ' '.join(title.replace('-', ' ').split())
            return FilmMetadata(
                filename=filename,
                title=title,
                year=year,
                format_signals=format_signals,
                language=language,
                country=country,
                user_tag=user_tag
            )

        # === LAST RESORT: No year found ===
        return FilmMetadata(
            filename=filename,
            title=self._clean_title(name),
            format_signals=format_signals,
            language=language,
            country=country,
            user_tag=user_tag
        )
