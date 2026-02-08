#!/usr/bin/env python3
"""
Shared title normalization for film classification system

CRITICAL: This module provides symmetric normalization for the lookup system.
The same normalization MUST be used for:
1. Building the lookup database (intake)
2. Querying the lookup database (query)

If these differ, lookups will fail silently.
"""

import re
import unicodedata
from typing import List

from lib.constants import FORMAT_SIGNALS


def _strip_format_signals(title: str) -> str:
    """
    Strip format signals from title for cleaner matching

    Args:
        title: Raw title string

    Returns:
        Title with format signals removed
    """
    # Build regex patterns from canonical format signals list
    # Pattern examples: r'\s+35mm\s*', r'\s+open\s+matte\s*', r'\s+criterion\s*'
    for signal in FORMAT_SIGNALS:
        # Escape special regex characters in signal (e.g., "director's cut")
        signal_escaped = re.escape(signal)
        # Replace escaped spaces with flexible whitespace pattern
        signal_pattern = signal_escaped.replace(r'\ ', r'\s+')
        # Match with surrounding whitespace
        pattern = rf'\s+{signal_pattern}\s*'
        title = re.sub(pattern, ' ', title, flags=re.IGNORECASE)

    return title.strip()


def normalize_for_lookup(title: str, strip_format_signals: bool = True) -> str:
    """
    Normalize title for database lookup with symmetric guarantees

    This function MUST be used identically for:
    1. Building lookup database (intake)
    2. Querying lookup database (query)

    Normalization steps:
    1. Strip format signals (if enabled)
    2. Normalize Unicode (decompose accents)
    3. Remove diacritics/accents
    4. Lowercase
    5. Remove punctuation (keep only alphanumeric and spaces)
    6. Collapse whitespace

    Args:
        title: Raw title string
        strip_format_signals: If True, remove format signals before normalization

    Returns:
        Normalized title string

    Examples:
        >>> normalize_for_lookup("Dr. Strangelove Criterion", strip_format_signals=True)
        'dr strangelove'

        >>> normalize_for_lookup("The Shining 35mm Scan", strip_format_signals=True)
        'the shining scan'

        >>> normalize_for_lookup("À bout de souffle", strip_format_signals=False)
        'a bout de souffle'
    """
    # Step 1: Strip format signals (using canonical list from constants.py)
    if strip_format_signals:
        title = _strip_format_signals(title)

    # Step 2: Normalize Unicode - convert to NFD (decomposed) form
    # This separates base characters from combining marks (accents)
    title = unicodedata.normalize('NFD', title)

    # Step 3: Remove combining characters (accents/diacritics)
    # Category 'Mn' = Mark, nonspacing (accents, umlauts, etc.)
    title = ''.join(c for c in title if unicodedata.category(c) != 'Mn')

    # Step 4: Lowercase
    title = title.lower()

    # Step 5: Remove punctuation except spaces
    # Keep only word characters (letters, numbers, underscore) and spaces
    title = re.sub(r'[^\w\s]', '', title)

    # Step 6: Collapse whitespace
    title = ' '.join(title.split())

    return title.strip()


def normalize_title_list(titles: List[str], strip_format_signals: bool = True) -> List[str]:
    """
    Normalize a list of titles

    Args:
        titles: List of raw title strings
        strip_format_signals: If True, remove format signals before normalization

    Returns:
        List of normalized title strings
    """
    return [normalize_for_lookup(title, strip_format_signals) for title in titles]
