"""
lib/pipeline_types.py — Typed stage boundaries for the classification pipeline (Issue #54)

L3 enforcement layer: typed dataclasses that cross stage boundaries so that
contracts are mechanically enforced rather than described in documentation.

Two stage boundaries:
  EnrichedFilm  — output of ENRICH stage (API merge); input to RESOLVE stage
  Resolution    — output of any classification source; input to BUILD_RESULT

Usage:
  from lib.pipeline_types import EnrichedFilm, Resolution
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnrichedFilm:
    """Typed output of the ENRICH stage (API query + smart merge).

    Replaces the raw dict currently returned by _merge_api_results().
    Carries provenance so downstream stages know which API provided each field.

    Readiness levels (Rule 10):
      R0  no year (hard stop)
      R1  title + year only; no director AND no country
      R2  director OR country (not both)
      R3  director AND country AND genres — full data
    """
    # Core identity fields (may be None if API returned nothing)
    director: Optional[str]
    countries: List[str]
    genres: List[str]
    keywords: List[str]

    # Audit trail fields
    tmdb_id: Optional[int]
    tmdb_title: Optional[str]

    # Data readiness level assessed after merge
    readiness: str  # 'R0', 'R1', 'R2', 'R3'

    # Provenance: which API/source provided each field
    # e.g. {'director': 'omdb', 'countries': 'omdb', 'genres': 'tmdb'}
    sources: Dict[str, str] = field(default_factory=dict)

    # Full tmdb_data dict preserved for components that still consume it directly
    # (satellite routing, keyword checks). Retained during transition — remove in
    # a future issue once all consumers read from EnrichedFilm fields.
    raw: Optional[Dict] = None


@dataclass
class Resolution:
    """Typed output of any classification source in the RESOLVE priority chain.

    Each source (explicit_lookup, corpus, two-signal, user_tag, unsorted) returns
    Optional[Resolution]. The priority chain selects the first non-None winner;
    non-winners become the evidence trail naturally (no separate shadow pass needed).

    Source names (for evidence trail and debugging):
      'explicit_lookup'         P1 — human-curated SORTING_DATABASE
      'corpus_lookup'           P2 — scholarship-sourced ground truth
      'two_signal'              P3 — director + structural integration
      'user_tag_recovery'       P4 — filename user tag fallback
      'unsorted_no_year'        P5 — hard gate: no year
      'unsorted_insufficient_data'  P5 — R1: no director AND no country
      'unsorted_no_director'    P5 — year found, no director
      'unsorted_no_match'       P5 — year + director, no routing rule matched
      'non_film_supplement'     P0 — pre-stage: supplement/trailer/episode
    """
    tier: str                        # 'Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted', 'Non-Film'
    decade: Optional[str]            # e.g. '1970s'; None for Unsorted/Non-Film
    subdirectory: Optional[str]      # Core: director name; Satellite: category name; else None
    destination: str                 # Full path fragment, e.g. 'Satellite/Giallo/1970s/'
    confidence: float                # 0.0–1.0
    reason: str                      # Reason code (matches existing manifest codes)
    source_name: str                 # Which resolution source produced this
    explanation: str = ''            # Human-readable detail for diagnostics
