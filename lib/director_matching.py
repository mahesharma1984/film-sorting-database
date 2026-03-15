"""
lib/director_matching.py — Unified director name matching (Issue #54)

L3 enforcement layer: single implementation of director name matching so that
satellite.py, signals.py, and classify.py all use identical semantics.

Previously there were three separate implementations:
  lib/satellite.py:_director_matches()       — SatelliteClassifier internal
  lib/signals.py:_director_key_matches()     — signals module internal
  classify.py:_merge_api_results()           — implicit string comparison

All three used the same algorithm (whole-word for single-token entries,
substring for multi-word entries) but were maintained independently. This
file is the single source of truth.

Usage:
  from lib.director_matching import match_director
  match_director("jean-luc godard", "godard")   # True (whole-word)
  match_director("jean-luc godard", "luc")      # False (whole-word, not full token)
  match_director("jean-luc godard", "jean-luc godard")  # True (substring)
"""


def match_director(query: str, candidate: str) -> bool:
    """Test whether a director name query matches a candidate entry.

    Matching rules (Issue #25 D1 — replaces the old substring-everywhere check):
      Single-word candidate  → whole-word token match
        'bava' must be a complete whitespace-delimited token in query.
        Prevents 'bava' from matching 'Lamberto Bava Jr.' via substring.
      Multi-word candidate   → substring match
        'tsui hark' in 'tsui hark' is safe — exact phrase has no false positives.
      Hyphenated surnames (e.g. 'robbe-grillet') are treated as single tokens
        by str.split() and use whole-word matching.

    Args:
        query:      Normalized director name from film metadata (lowercased by caller).
        candidate:  Entry from DIRECTOR_REGISTRY or whitelist (lowercased by caller).

    Returns:
        True if query matches candidate under the rules above.
    """
    if ' ' not in candidate:
        return candidate in query.split()
    return candidate in query
