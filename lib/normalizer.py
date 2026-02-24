#!/usr/bin/env python3
"""
lib/normalizer.py — Filename normalization pre-stage (Issue #18)

Pure PRECISION filename cleaning. No tier assignment, no API calls,
no whitelist checks, no SORTING_DATABASE access.

Output feeds lib/parser.py unchanged — cleaned filenames must remain
valid parser input.

Rules are applied in strict order:
  1. nonfim detection (TV episodes, supplementary content) — flag only, no rename
  2. Strip [TAG] bracket prefix
  3. Strip leading NN - numbering (1-2 digit)
  4. Fix year-in-quality-parenthetical
  5. Fix multiple-year filenames (leading year == parenthetical year)
  6. Normalize edition markers → Plex {edition-NAME} format
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple


@dataclass
class NormalizationResult:
    """Output of a single filename normalization pass."""
    original_filename: str
    cleaned_filename: str
    change_type: str   # strip_junk | normalize_edition | fix_year | flag_nonfim | unchanged
    notes: str


class FilenameNormalizer:
    """
    Pure PRECISION filename normalizer.

    Applies cleaning rules sequentially.  Does not modify files — only
    produces NormalizationResult records for rename_manifest.csv.
    """

    # User classification tag prefixes — protect from bracket-stripping
    _USER_TAG_PREFIXES = ('Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted')
    _DECADE_TAG_RE = re.compile(r'^(19|20)\d{2}s-')

    # Edition marker names that appear as '- NAME' in title position
    EDITION_MARKERS = [
        'Uncut',
        'R-Rated Cut',
        'R Rated Cut',
        'Hong Kong Cut',
        'Theatrical Cut',
        "Director's Cut",
        'Directors Cut',
        'Extended Cut',
        'Extended Edition',
        'Unrated',
        'Final Cut',
        "Editor's Cut",
        'Editors Cut',
        'International Cut',
        'Redux',
    ]

    # Quality indicators that appear inside parentheticals alongside years
    _QUALITY_RE = re.compile(
        r'\b(?:480p|576p|720p|1080p|2160p|4k|uhd|bluray|blu-ray|bdrip|web-dl|webrip|'
        r'dvdrip|x264|x265|h\.?264|h\.?265|hevc|aac|dts|flac|hdr|dv|remux|hbo|broadcast)\b',
        re.IGNORECASE
    )

    # Supplementary-content prefix patterns (matched at start of stem with re.match)
    _SUPPLEMENTARY_PREFIXES = [
        r'Interview\s*[-–]',
        r'Documentary\s*[-–]',
        r'Essay [Ff]ilm\s*[-–]',
        r'Video [Ee]ssay\b',
        r'Audio [Ee]ssay\b',
        r'Deleted [Ss]cenes?\b',
        r'Deleted [Ff]ootage\b',
        r'Conversations?\s+with\b',
        r'A Conversation with\b',
        r'An [Ii]ntroduction (?:to|by)\b',
        r'Introduction by\b',
        r'On [Tt]he [Ss]et\b',
        # Trailers / promos
        r'Trailer\b',
        r'Theatrical [Tt]railer\b',
        r'Teaser\b',
        r'Promo\b',
        r'TV [Ss]pots?\b',
        r'Radio [Ss]pots?\b',
        # Blu-ray supplement types
        r'Featurette\b',
        r'Behind [Tt]he [Ss]cenes?\b',
        r'Commentary\b',
        r'Outtakes?\b',
        r'Audio [Oo]uttakes?\b',
        r'Q\s*&\s*A\b',
        r'Gallery\b',
        r'Photo\.?[Gg]allery\b',
        r'Restoration\b',
        r'Screen [Tt]ests?\b',
        r'Post [Pp]roduction\b',
        r'Selected [Ss]cene\b',
        r'Super-8 [Vv]ersion\b',
        r'Extended [Ss]cene\b',
        r'Extended [Cc]ut\s*[-–]',  # "Extended cut - Jade.mkv" (supplement, not edition)
    ]

    # Supplementary content detected anywhere in the stem (not just prefix)
    _SUPPLEMENTARY_SEARCH = [
        r' - (?:The )?[Mm]aking [Oo]f ',
        r' - Interview with\b',
        # Studio ident reels (appear as "Trailer | United Artists | 1970" in R2a)
        r'\b(?:20th Century Fox|Warner Brothers?|United Artists)\b',
    ]

    def normalize(self, filename: str) -> NormalizationResult:
        """
        Apply all normalization rules to a filename.

        Args:
            filename: Original filename (including extension)

        Returns:
            NormalizationResult with cleaned filename, change_type, and notes
        """
        stem = Path(filename).stem
        ext = Path(filename).suffix

        # Rules 1-2: nonfim detection — flag and stop (no renames for nonfim)
        nonfim_note = self._detect_nonfim(stem)
        if nonfim_note:
            return NormalizationResult(
                original_filename=filename,
                cleaned_filename=filename,
                change_type='flag_nonfim',
                notes=nonfim_note,
            )

        # Rules 3-7: sequential cleaning
        cleaned_stem, changes = self._apply_cleaning_rules(stem)

        if not changes:
            return NormalizationResult(
                original_filename=filename,
                cleaned_filename=filename,
                change_type='unchanged',
                notes='',
            )

        primary_change = changes[0][0]
        all_notes = '; '.join(note for _, note in changes)
        cleaned_filename = cleaned_stem + ext

        return NormalizationResult(
            original_filename=filename,
            cleaned_filename=cleaned_filename,
            change_type=primary_change,
            notes=all_notes,
        )

    # ── nonfim detection ────────────────────────────────────────────────────

    def _detect_nonfim(self, stem: str) -> Optional[str]:
        """
        Detect non-film content.  Returns a notes string if nonfim, else None.

        Does NOT rename — nonfim files are flagged for human review only.
        """
        # TV episode: standard SnnEnn pattern
        if re.search(r'\bS\d{1,2}E\d{1,2}\b', stem, re.IGNORECASE):
            return 'nonfim/tv: TV episode pattern (SnnEnn)'

        # Multi-part scene-release: War.and.Peace.Part.1.Andrey...
        if re.search(r'\.Part\.\d+\.', stem, re.IGNORECASE):
            return 'nonfim/tv: multi-part episode (.Part.N. dot-separated format)'

        # Supplementary prefix patterns (matched at start)
        for pattern in self._SUPPLEMENTARY_PREFIXES:
            if re.match(pattern, stem, re.IGNORECASE):
                return f'nonfim/supplementary: matched prefix "{pattern}"'

        # Supplementary patterns anywhere in the stem
        for pattern in self._SUPPLEMENTARY_SEARCH:
            if re.search(pattern, stem, re.IGNORECASE):
                return f'nonfim/supplementary: matched internal pattern "{pattern}"'

        return None

    # ── cleaning rules ──────────────────────────────────────────────────────

    # Tokens that identify a filename as torrent/rip-style (dot-separated junk)
    _JUNK_TOKENS: Set[str] = {
        # Resolution
        '480p', '576p', '720p', '1080p', '2160p', '4k', 'uhd', 'hd',
        # Source
        'bluray', 'blu-ray', 'bdrip', 'brrip', 'web-dl', 'webrip', 'web',
        'dvdrip', 'dvdscr', 'hdrip', 'hdtv', 'pdtv', 'tvrip', 'amzn', 'nf',
        # Codec
        'x264', 'x265', 'h264', 'h265', 'hevc', 'avc', 'xvid', 'divx',
        # Audio
        'aac', 'ac3', 'dts', 'flac', 'mp3', 'ddp', 'truehd', 'atmos',
        'dd2', 'dd5', 'eac3', 'ma',
        # Modifiers
        'repack', 'proper', 'remastered', 'remux', 'extended', 'theatrical',
        'internal', 'limited', 'multi', 'dual', 'hybrid', 'hdr', 'hdr10',
        # Language/country tokens used as junk in filenames
        'ita', 'eng', 'fre', 'ger', 'spa', 'por', 'jap', 'rus',
        'french', 'italian', 'german', 'spanish', 'japanese', 'portuguese',
        'english', 'usa',
        # Release group indicators
        'yify', 'rarbg', 'vxt', 'tigole', 'sartre', 'handjob',
    }

    def _is_junk_token(self, token: str) -> bool:
        """Return True if a dot-separated token is technical/release junk."""
        t = token.lower()
        if t in self._JUNK_TOKENS:
            return True
        # Pure digits or digits+letter like '4k', '5', '1' — but NOT 4-digit years
        if re.match(r'^\d+[a-z]?\d*$', t) and not re.match(r'^(19|20)\d{2}$', t):
            return True
        # Release group tag like 'YTS-MX', 'x264-HANDJOB', 'H264-CKTV'
        if re.match(r'^[a-z0-9]+-[A-Z0-9]+$', token):
            return True
        return False

    def _normalize_dot_separated(self, stem: str) -> Tuple[str, str]:
        """
        Rule 2: Convert torrent-style dot-separated filenames to space-separated.

        'Title.Words.Year.TechJunk' → 'Title Words (Year)'

        Only fires when:
        - No spaces in the stem (confirms dot-separated format)
        - At least 3 dots
        - At least one known junk token OR a year is present

        Preserves: filenames with spaces, filenames with no year and no junk.
        """
        if ' ' in stem or stem.count('.') < 3:
            return stem, ''

        parts = stem.split('.')

        # Find year (first 19xx or 20xx token)
        year: Optional[str] = None
        year_idx: Optional[int] = None
        for i, p in enumerate(parts):
            if re.match(r'^(19|20)\d{2}$', p):
                year, year_idx = p, i
                break

        # Require at least one junk token to confirm torrent-style.
        # Year alone is not enough — 'Raoul.Ruiz.2000.Comedy.of.Innocence'
        # has a year but no junk, so it could be Director.Year.Title format.
        has_junk = any(self._is_junk_token(p) for p in parts)
        if not has_junk:
            return stem, ''  # e.g. 'A.Gathering.of.Magic-Grym', 'Raoul.Ruiz.2000.Comedy...' — leave alone

        # Extract title parts
        if year_idx == 0:
            # Year at start: title is parts after year, up to first junk token
            rest = parts[1:]
            cut = next((i for i, p in enumerate(rest) if self._is_junk_token(p)), len(rest))
            title_parts = rest[:cut]
        elif year_idx is not None:
            title_parts = parts[:year_idx]
        else:
            # No year: find first junk token from the left — everything before it
            # is the title. This handles cases like 'The.Speed.of.Life.1080p.H.264-Koza'
            # where 'H' and '264-Koza' at the end would otherwise defeat a right-to-left scan.
            cut = next((i for i, p in enumerate(parts) if self._is_junk_token(p)), len(parts))
            title_parts = parts[:cut]

        # Build title string
        title = ' '.join(title_parts)

        # Strip AKA alternative title (keep primary language title only)
        title = re.sub(r'\s+(?:AKA|aka)\s+.*', '', title).strip()

        # Strip leading disc/numbering prefix like '2-'
        title = re.sub(r'^\d+-', '', title).strip()

        # Strip parenthetical fragments from dot-splitting (e.g. "(J-Luc" or "Godard)")
        title = re.sub(r'\s*\([^)]*\)?\s*', ' ', title).strip()
        title = re.sub(r'\s*\)?\s*$', '', title).strip()

        title = re.sub(r'\s+', ' ', title).strip()

        if not title:
            return stem, ''

        result = f'{title} ({year})' if year else title
        if result == stem:
            return stem, ''

        return result, f'converted dot-separated torrent filename'

    def _apply_cleaning_rules(
        self, stem: str
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Apply rules 2-7 sequentially.

        Returns:
            (cleaned_stem, [(change_type, note), ...])
            Empty list means no changes were made.
        """
        changes: List[Tuple[str, str]] = []
        current = stem

        # Rule 2: convert dot-separated torrent-style filenames (MUST run first)
        result, note = self._normalize_dot_separated(current)
        if result != current:
            changes.append(('strip_junk', note))
            current = result

        # Rule 3: strip [TAG] bracket prefix
        result, note = self._strip_bracket_prefix(current)
        if result != current:
            changes.append(('strip_junk', note))
            current = result

        # Rule 4: strip leading NN - numbering (1-2 digit only)
        result, note = self._strip_numeric_prefix(current)
        if result != current:
            changes.append(('strip_junk', note))
            current = result

        # Rule 5: fix year trapped in quality parenthetical
        result, note = self._fix_year_in_quality_paren(current)
        if result != current:
            changes.append(('fix_year', note))
            current = result

        # Rule 6: fix multiple-year filenames
        result, note = self._fix_multiple_years(current)
        if result != current:
            changes.append(('fix_year', note))
            current = result

        # Rule 7: normalize edition markers to Plex {edition-NAME}
        result, note = self._normalize_edition_markers(current)
        if result != current:
            changes.append(('normalize_edition', note))
            current = result

        return current, changes

    # ── individual rules ────────────────────────────────────────────────────

    def _is_user_classification_tag(self, tag_content: str) -> bool:
        """Return True if bracket content is a user classification tag (protect from stripping)."""
        if any(tag_content.startswith(prefix) for prefix in self._USER_TAG_PREFIXES):
            return True
        if self._DECADE_TAG_RE.match(tag_content):
            return True
        return False

    def _strip_bracket_prefix(self, stem: str) -> Tuple[str, str]:
        """
        Rule 3: strip leading [TAG] junk prefix.

        Protects:
        - User classification tags: [Core-1960s], [Reference-...], etc.
        - Year brackets at non-start positions (handled by parser)
        - Year-only brackets like [1960] at start (legitimate format)
        """
        match = re.match(r'^\[([^\]]*)\]', stem)
        if not match:
            return stem, ''

        tag_content = match.group(1)

        # Protect user classification tags
        if self._is_user_classification_tag(tag_content):
            return stem, ''

        # Protect bare year brackets like [1960]
        if re.match(r'^\d{4}$', tag_content.strip()):
            return stem, ''

        # Strip the bracket group and any leading punctuation/whitespace that follows
        remainder = stem[match.end():]
        remainder = re.sub(r'^[-_]+\s*', '', remainder).strip()

        return remainder, f'stripped leading bracket tag [{tag_content}]'

    def _strip_numeric_prefix(self, stem: str) -> Tuple[str, str]:
        """
        Rule 4: strip leading 1-2 digit numbering like '02 - ' or '2: '.

        Does NOT strip 4-digit year prefixes (handled by Rule 6 or the parser).
        """
        match = re.match(r'^(\d{1,2})\s*[-:]\s+', stem)
        if not match:
            return stem, ''

        number = match.group(1)
        remainder = stem[match.end():].strip()
        return remainder, f'stripped leading numbering prefix "{number} -"'

    def _fix_year_in_quality_paren(self, stem: str) -> Tuple[str, str]:
        """
        Rule 5: fix year trapped inside a quality-metadata parenthetical.

        Case A: (YYYY - quality...)  →  (YYYY)
          e.g. '(1978 - 480p - Áudio Original em Português)' → '(1978)'

        Case B: (YYYY) (quality...)  →  (YYYY)
          e.g. '(1971) (2160p BluRay x265 10bit DV HDR r00t)' → '(1971)'
        """
        changed = False
        current = stem

        # Case A: year + dash + quality in the same paren
        def _replace_year_quality(m: re.Match) -> str:
            nonlocal changed
            content = m.group(1)
            yr_match = re.match(r'^(\d{4})\s*[-–]\s*', content)
            if yr_match:
                year = int(yr_match.group(1))
                if 1920 <= year <= 2029:
                    remainder_text = content[yr_match.end():]
                    if self._QUALITY_RE.search(remainder_text):
                        changed = True
                        return f'({year})'
            return m.group(0)

        result = re.sub(r'\(([^)]+)\)', _replace_year_quality, current)
        if changed:
            current = re.sub(r'\s+', ' ', result).strip()
            return current, 'extracted year from quality parenthetical (Case A)'

        # Case B: standalone year paren followed by a quality-only paren
        all_parens = list(re.finditer(r'\(([^)]+)\)', current))
        if len(all_parens) >= 2:
            year_found = None
            quality_spans = []

            for m in all_parens:
                content = m.group(1).strip()
                # Is it a bare year?
                if re.match(r'^\d{4}$', content):
                    year = int(content)
                    if 1920 <= year <= 2029:
                        year_found = year
                        continue
                # Is it quality-only (contains a quality indicator)?
                if self._QUALITY_RE.search(content):
                    # Confirm it has NO standalone year of its own
                    if not re.search(r'\b(19|20)\d{2}\b', content):
                        quality_spans.append((m.start(), m.end()))

            if year_found and quality_spans:
                # Remove quality parens (right-to-left to preserve offsets)
                cleaned = current
                for start, end in reversed(quality_spans):
                    cleaned = cleaned[:start] + cleaned[end:]
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if cleaned != current:
                    return cleaned, 'removed quality-only parenthetical after year (Case B)'

        return current, ''

    def _fix_multiple_years(self, stem: str) -> Tuple[str, str]:
        """
        Rule 6: strip a redundant leading 4-digit year when a parenthetical
        year also exists and they match.

        '1992 Andrew Dice Clay For Ladies (1992 Hbo Broadcast)'
          → 'Andrew Dice Clay For Ladies (1992)'

        Does NOT strip when years differ:
          '2001 - A Space Odyssey (1968)' — different years, and ' - ' after
          the leading digits is the Brazilian format, which the parser already handles.
        """
        # Only match: leading 4-digit year followed by a space NOT followed by '- '
        # (i.e. NOT the Brazilian YYYY - Title format, which the parser handles)
        leading_match = re.match(r'^(\d{4})\s+(?!-\s)', stem)
        if not leading_match:
            return stem, ''

        leading_year = int(leading_match.group(1))
        if not (1920 <= leading_year <= 2029):
            return stem, ''

        # Find a parenthetical that starts with a valid year (possibly followed by text)
        paren_match = re.search(r'\((\d{4})(?:\s[^)]+)?\)', stem)
        if not paren_match:
            return stem, ''

        paren_year = int(paren_match.group(1))

        # Only strip if the leading year equals the parenthetical year
        if leading_year != paren_year:
            return stem, ''

        remainder = stem[leading_match.end():]

        # If the paren content has extra text (e.g. '1992 Hbo Broadcast'),
        # clean it to just (YYYY)
        remainder = re.sub(
            r'\((\d{4})\s[^)]+\)',
            lambda m: f'({m.group(1)})',
            remainder
        )
        remainder = re.sub(r'\s+', ' ', remainder).strip()

        return remainder, (
            f'stripped redundant leading year {leading_year} '
            f'(matches parenthetical year {paren_year})'
        )

    def _normalize_edition_markers(self, stem: str) -> Tuple[str, str]:
        """
        Rule 7: move edition markers from title position to Plex {edition-NAME}.

        'Braindead - Uncut (1992) - LaserDisc'
          → 'Braindead (1992) {edition-Uncut}'

        'Apocalypse Now - Director's Cut (1979)'
          → 'Apocalypse Now (1979) {edition-Director's Cut}'

        Format signals like 'LaserDisc' that remain after edition removal are
        left for lib/parser.py to strip (they are in FORMAT_SIGNALS).
        """
        # Build alternation pattern from EDITION_MARKERS (literal match)
        edition_alt = '|'.join(re.escape(m) for m in self.EDITION_MARKERS)

        # Match ' - EditionName' appearing before a year paren, bracket, or end-of-string
        match = re.search(
            rf'\s*[-–]\s*({edition_alt})\s*(?=\(|\[|$)',
            stem,
            re.IGNORECASE
        )
        if not match:
            return stem, ''

        edition_name = match.group(1).strip()

        # Avoid double-tagging: if {edition-NAME} is already present, skip
        if re.search(rf'\{{edition-{re.escape(edition_name)}\}}', stem, re.IGNORECASE):
            return stem, ''

        # Remove the ' - EditionName' from its current position
        cleaned = stem[:match.start()] + stem[match.end():]
        # Ensure there's a space before any opening paren (can get swallowed)
        cleaned = re.sub(r'\s*\(', ' (', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Insert {edition-NAME} after the year paren if present, else append
        year_paren = re.search(r'\(\d{4}\)', cleaned)
        if year_paren:
            insert_pos = year_paren.end()
            cleaned = (
                cleaned[:insert_pos]
                + f' {{edition-{edition_name}}}'
                + cleaned[insert_pos:]
            )
        else:
            cleaned = f'{cleaned} {{edition-{edition_name}}}'

        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned, (
            f'normalized edition marker "{edition_name}" '
            f'to Plex {{edition-{edition_name}}} format'
        )
