"""
lib/signals.py — Unified Two-Signal Classification Architecture (Issue #42)

Two scoring functions produce evidence vectors; one integration function
combines them into a single classification decision with a named reason code.

Signal 1: Director Identity — score_director()
  Checks DIRECTOR_REGISTRY (Satellite categories) and CoreDirectorDatabase.
  Returns all matching DirectorMatch objects (never exits early, no caps).

Signal 2: Structural Triangulation — score_structure()
  Checks Reference canon, COUNTRY_TO_WAVE, SATELLITE_ROUTING_RULES structural
  gates (country+genre+keywords), and Popcorn threshold.
  Returns all matching StructuralMatch objects (never exits early, no caps).

Integration: integrate_signals()
  Applies priority decision table from Issue #42 §5.
  Returns IntegrationResult with tier, destination, confidence, and reason code.
  Cap enforcement is the caller's responsibility (applied after integration).

Reason codes produced (replaces core_director / tmdb_satellite / country_satellite):
  both_agree          — director + structure both matched same Satellite category
  director_signal     — director identity matched (structure absent or different tier)
  structural_signal   — structural triangulation matched (director absent)
  review_flagged      — signals conflict or structural match is ambiguous (low confidence)
  # Note: director_disambiguates removed (Issue #51) — conflicting signals produce
  # review_flagged instead of forcing a director-wins resolution (52.9% accuracy).

Preserved reason codes (unchanged):
  reference_canon     — structural match in Reference canon
  user_tag_recovery   — user tag fallback (applied by caller after integration)
  explicit_lookup     — SORTING_DATABASE (Stages 1-2, caller, unchanged)
  corpus_lookup       — scholarship corpus (Stage 2.5, caller, unchanged)
  unsorted_*          — no signal matched (Stage 9, caller)
  popcorn_*           — Popcorn structural signal (sub-reason codes preserved)
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from lib.director_matching import match_director

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DirectorMatch:
    """One director identity match from DIRECTOR_REGISTRY or CoreDirectorDatabase."""
    tier: str                    # 'Satellite' or 'Core'
    category: str                # e.g. 'French New Wave', or 'Core'
    canonical_name: Optional[str]  # Core canonical folder name (Core only)
    source: str                  # 'satellite_rules' or 'core_whitelist'
    decade_valid: bool           # True if film year within declared decade bounds
                                 # Always True for Core and tradition categories


@dataclass
class StructuralMatch:
    """One structural triangulation match."""
    tier: str                    # 'Reference', 'Satellite', or 'Popcorn'
    category: Optional[str]      # Satellite category name; None for Reference/Popcorn
    match_type: str              # 'reference_canon', 'country_wave', 'country_genre',
                                 # 'keyword_tier_a', 'keyword_tier_b', 'partial_structural',
                                 # or popcorn reason
    uncertainty: float = 0.0     # Issue #56: 0.0 = all gates tested and pass;
                                 # 0.5 = genre gate untestable (data absent, not failing)


@dataclass
class IntegrationResult:
    """Output of integrate_signals() — a fully resolved classification decision."""
    tier: str
    category: Optional[str]      # Satellite subdirectory name; None for Core/Reference/Popcorn
    decade: Optional[str]        # Film decade string, e.g. '1970s'
    destination: str             # Full path fragment, e.g. 'Satellite/Giallo/1970s/'
    confidence: float
    reason: str                  # One of the reason codes documented above
    explanation: str             # Human-readable detail for diagnostics


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _director_key_matches(director_lower: str, director_tokens: set, key: str) -> bool:
    """Thin wrapper — delegates to lib.director_matching.match_director (Issue #54).

    Signature preserved for call-site compatibility. director_tokens is unused
    (match_director splits internally), retained to avoid changing all callers.
    """
    return match_director(director_lower, key)


def _decade_of(year: Optional[int]) -> Optional[str]:
    if year is None:
        return None
    return f"{(year // 10) * 10}s"


# ---------------------------------------------------------------------------
# Signal 1: Director Identity
# ---------------------------------------------------------------------------

def score_director(
    director_name: Optional[str],
    year: Optional[int],
    core_db,
    contract: str = 'legacy',
) -> List[DirectorMatch]:
    """Compute director identity signal for a film.

    Returns all matches from DIRECTOR_REGISTRY (Satellite) and CoreDirectorDatabase.
    Never exits early. Does NOT enforce caps — caller applies cap after integration.

    Decade validity:
      Tradition categories (country_codes populated): decade_valid=True always.
        Director identity persists across eras (Ferrara 1998 → American Exploitation).
      Movement categories (country_codes=[]): decade_valid only if film decade in declared list.
        Era-appropriate movement routing (Godard 1990 → FNW decade_valid=False).

    contract='scholarship_only': Core whitelist emission suppressed.
      Core directors still contribute their Satellite memberships (if any).
      P6 (Core routing) is disabled because core_dir list will be empty.
    """
    from lib.constants import DIRECTOR_REGISTRY

    if not director_name:
        return []

    director_lower = director_name.lower().strip()
    director_tokens = set(director_lower.split())
    film_decade = _decade_of(year)
    results: List[DirectorMatch] = []

    # Check Satellite director lists via DIRECTOR_REGISTRY
    for key, entries in DIRECTOR_REGISTRY.items():
        if _director_key_matches(director_lower, director_tokens, key):
            for entry in entries:
                if entry.is_tradition:
                    # Tradition: director identity bypasses decade restriction
                    decade_valid = True
                else:
                    # Movement: must be within declared decade bounds
                    decade_valid = (
                        film_decade is not None
                        and (entry.decades is None or film_decade in entry.decades)
                    )
                results.append(DirectorMatch(
                    tier='Satellite',
                    category=entry.category,
                    canonical_name=None,
                    source='satellite_rules',
                    decade_valid=decade_valid,
                ))

    # Check Core whitelist — suppressed under scholarship_only contract
    if contract != 'scholarship_only' and core_db and core_db.is_core_director(director_name):
        canonical = core_db.get_canonical_name(director_name)
        results.append(DirectorMatch(
            tier='Core',
            category='Core',
            canonical_name=canonical,
            source='core_whitelist',
            decade_valid=True,  # Core valid across all decades
        ))

    return results


# ---------------------------------------------------------------------------
# Signal 2: Structural Triangulation
# ---------------------------------------------------------------------------

def score_structure(
    metadata,
    tmdb_data: Optional[dict],
    satellite_classifier,
    contract: str = 'legacy',
) -> List[StructuralMatch]:
    """Compute structural triangulation signal for a film (Issue #55 — narrowed scope).

    Checks COUNTRY_TO_WAVE and SATELLITE_ROUTING_RULES structural gates
    (country+genre+keywords). Returns ALL matching StructuralMatch objects.
    Never exits early. Does NOT enforce caps.

    Reference canon and Popcorn are no longer handled here — they are
    standalone resolvers (_resolve_reference, _resolve_popcorn) in the
    classify.py resolve chain (Issue #55).

    contract='scholarship_only': no effect on structural matching (Reference
      suppression is now handled by _resolve_reference in the caller).
    """
    from lib.constants import COUNTRY_TO_WAVE

    results: List[StructuralMatch] = []
    year = getattr(metadata, 'year', None)
    decade = _decade_of(year)

    # --- COUNTRY_TO_WAVE (simple country + decade structural match) ---
    country = getattr(metadata, 'country', None)
    if country and decade:
        wave_cfg = COUNTRY_TO_WAVE.get(country)
        if wave_cfg and decade in wave_cfg['decades']:
            results.append(StructuralMatch(
                tier='Satellite',
                category=wave_cfg['category'],
                match_type='country_wave',
            ))

    # --- SATELLITE_ROUTING_RULES structural matching (via satellite_classifier) ---
    for category_name, match_type in satellite_classifier.classify_structural(metadata, tmdb_data):
        # Issue #56: partial_structural = genre gate untestable (data absent, not failing).
        # uncertainty=0.5 means one tested gate (genre) is untestable — confidence capped downstream.
        uncertainty = 0.5 if match_type == 'partial_structural' else 0.0
        results.append(StructuralMatch(
            tier='Satellite',
            category=category_name,
            match_type=match_type,
            uncertainty=uncertainty,
        ))

    return results


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

def integrate_signals(
    director_matches: List[DirectorMatch],
    structural_matches: List[StructuralMatch],
    decade: Optional[str],
    readiness: str,
) -> IntegrationResult:
    """Integrate director and structural signals into a single classification decision.

    Issue #55: narrowed to actual two-signal combinations only.
    Reference canon → _resolve_reference() in classify.py (fires at P3, before here).
    Popcorn → _resolve_popcorn() in classify.py (fires at P5, after here).

    Priority order (director × structure combinations only):
      P1. Director Satellite + Structure same cat  → both_agree (Satellite)
      P2. Director Satellite (decade_valid) + Structure different cat → review_flagged (conflict)
      P3. Director Satellite (decade_valid), no structural Satellite  → director_signal
      P4. Director Core + structural Satellite      → structural_signal (Issue #25: Satellite wins)
      P5. Director Core, no structural Satellite    → director_signal (Core)
      P6. Structural Satellite (unique)             → structural_signal
      P7. Structural Satellite (ambiguous/multiple) → review_flagged
      P8. No signal                                → Unsorted (caller falls through to _resolve_popcorn)

    R2 readiness cap: confidence capped at 0.6 when readiness == 'R2'.
    """

    def _cap(conf: float) -> float:
        return min(conf, 0.6) if readiness == 'R2' else conf

    def _unsorted(explanation: str = 'no signal matched') -> IntegrationResult:
        return IntegrationResult(
            tier='Unsorted', category=None, decade=decade,
            destination='Unsorted/', confidence=0.0,
            reason='unsorted_no_match', explanation=explanation,
        )

    # Partition matches by tier and validity
    sat_struct_all = [m for m in structural_matches if m.tier == 'Satellite']

    # Issue #56: separate full matches (all gates tested+passed) from partial (genre untestable)
    sat_struct_full    = [m for m in sat_struct_all if m.uncertainty == 0.0]
    sat_struct_partial = [m for m in sat_struct_all if m.uncertainty > 0.0]

    sat_dir_valid = [m for m in director_matches if m.tier == 'Satellite' and m.decade_valid]
    core_dir      = [m for m in director_matches if m.tier == 'Core']

    # Deduplicate Satellite categories (preserve SATELLITE_ROUTING_RULES order)
    sat_struct_full_cats: List[str] = list(dict.fromkeys(
        m.category for m in sat_struct_full if m.category
    ))
    sat_struct_partial_cats: List[str] = list(dict.fromkeys(
        m.category for m in sat_struct_partial if m.category
    ))

    # === P1 + P2 + P3 + P3.5: Director Satellite with decade_valid ===
    if sat_dir_valid:
        dm = sat_dir_valid[0]  # first match (SATELLITE_ROUTING_RULES order preserved)
        structural_same = any(sm.category == dm.category for sm in sat_struct_full)
        structural_diff = sat_struct_full_cats and not structural_same

        if structural_same:
            # P1: both signals fully agree
            reason = 'both_agree'
            conf = _cap(0.85)
            explanation = f'director + structure both matched {dm.category}'
        elif structural_diff:
            # P2: director and full structural conflict — flag for review (Issue #51)
            # Previously director_disambiguates at 0.75, but accuracy was 52.9%.
            # Conflicting signals are ambiguity, not a case for director override.
            reason = 'review_flagged'
            conf = _cap(0.4)
            explanation = (
                f'director matched {dm.category}, '
                f'structure matched {sat_struct_full_cats} — signals conflict, needs review'
            )
        elif any(sm.category == dm.category for sm in sat_struct_partial):
            # P3.5 (Issue #56): director + partial structural agree — genre data absent
            # Confidence reduced proportionally to uncertainty (0.85 * 0.5 = ~0.43)
            sm_partial = next(s for s in sat_struct_partial if s.category == dm.category)
            reason = 'both_agree'
            conf = _cap(round(0.85 * (1.0 - sm_partial.uncertainty), 2))
            explanation = (
                f'director + partial structural match {dm.category} '
                f'(genre data absent — confidence reduced)'
            )
        else:
            # P3: director signal only
            reason = 'director_signal'
            conf = _cap(0.65)
            explanation = f'director identity matched {dm.category} ({dm.source})'

        return IntegrationResult(
            tier='Satellite', category=dm.category, decade=decade,
            destination=f'Satellite/{dm.category}/{decade}/',
            confidence=conf, reason=reason, explanation=explanation,
        )

    # === P4: Director Core + full structural Satellite → Satellite wins (Issue #25) ===
    if core_dir and sat_struct_full_cats:
        sat_cat = sat_struct_full_cats[0]
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(0.65), reason='structural_signal',
            explanation=(
                f'structural match {sat_cat} overrides Core director '
                f'(Satellite-before-Core, Issue #25)'
            ),
        )

    # === P5: Director Core, no full structural Satellite ===
    if core_dir:
        dm = core_dir[0]
        canonical = dm.canonical_name or dm.category
        return IntegrationResult(
            tier='Core', category=canonical, decade=decade,
            destination=f'Core/{decade}/{canonical}/',
            confidence=_cap(1.0), reason='director_signal',
            explanation='Core director whitelist match',
        )

    # === P6: Full structural Satellite, unique category ===
    if len(sat_struct_full_cats) == 1:
        sat_cat = sat_struct_full_cats[0]
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(0.65), reason='structural_signal',
            explanation=f'structural match {sat_cat}',
        )

    # === P7: Full structural Satellite, multiple ambiguous categories ===
    if len(sat_struct_full_cats) > 1:
        sat_cat = sat_struct_full_cats[0]  # highest-priority by SATELLITE_ROUTING_RULES order
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(0.4), reason='review_flagged',
            explanation=f'ambiguous structural match: {sat_struct_full_cats} — routed to {sat_cat}',
        )

    # === P7.5 (Issue #56): Partial structural only — no director, no full structural ===
    # Provisional routing: country+decade match confirmed, genre data absent.
    # Routes to review queue (confidence < REVIEW_CONFIDENCE_THRESHOLD) with evidence.
    if sat_struct_partial_cats:
        sat_cat = sat_struct_partial_cats[0]
        sm_partial = next(s for s in sat_struct_partial if s.category == sat_cat)
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(round(0.4 * (1.0 - sm_partial.uncertainty), 2)),
            reason='review_flagged',
            explanation=(
                f'partial structural match {sat_cat} '
                f'(country+decade match; genre data absent — needs curator review)'
            ),
        )

    # === P8: No signal — caller falls through to _resolve_popcorn ===
    return _unsorted()
