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
  director_disambiguates — director resolved conflict between two structural matches
  review_flagged      — ambiguous structural match, no director signal (low confidence)

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
                                 # 'keyword_tier_a', 'keyword_tier_b', or popcorn reason


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
    """Match a DIRECTOR_REGISTRY key against a normalized director name.

    Mirrors satellite.py._director_matches() exactly:
      Single-word keys: whole-word token match (prevents 'bava' matching 'lamberto bava jr.')
      Multi-word keys:  substring match (e.g. 'abel ferrara' in 'abel ferrara')
    """
    if ' ' not in key:
        return key in director_tokens
    return key in director_lower


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
    popcorn_classifier,
    contract: str = 'legacy',
) -> List[StructuralMatch]:
    """Compute structural triangulation signal for a film.

    Checks (in order): Reference canon, COUNTRY_TO_WAVE, SATELLITE_ROUTING_RULES
    structural gates (country+genre+keywords), and Popcorn threshold.
    Returns ALL matching StructuralMatch objects — never exits early.
    Does NOT enforce caps — caller applies cap after integration selects a winner.

    contract='scholarship_only': Reference canon emission suppressed.
      P1 (reference_canon routing) is disabled because ref_matches list will be empty.
    """
    from lib.constants import REFERENCE_CANON, COUNTRY_TO_WAVE
    from lib.normalization import normalize_for_lookup

    results: List[StructuralMatch] = []
    year = getattr(metadata, 'year', None)
    decade = _decade_of(year)

    # --- Reference canon (title + year lookup) — suppressed under scholarship_only contract ---
    title = getattr(metadata, 'title', None)
    if contract != 'scholarship_only' and title and year:
        normalized_title = normalize_for_lookup(title, strip_format_signals=True)
        if (normalized_title, year) in REFERENCE_CANON:
            results.append(StructuralMatch(
                tier='Reference', category=None, match_type='reference_canon'
            ))

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
        results.append(StructuralMatch(
            tier='Satellite',
            category=category_name,
            match_type=match_type,
        ))

    # --- Popcorn threshold ---
    popcorn_reason = popcorn_classifier.classify_reason(metadata, tmdb_data)
    if popcorn_reason:
        results.append(StructuralMatch(
            tier='Popcorn', category=None, match_type=popcorn_reason
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

    Priority order (mirrors current stage ordering, preserves Issue #25):
      P1. Structure → Reference                    → reference_canon
      P2. Director Satellite + Structure same cat  → both_agree (Satellite)
      P3. Director Satellite (decade_valid) + Structure different cat → director_disambiguates
      P4. Director Satellite (decade_valid), no structural Satellite  → director_signal
      P5. Director Core + structural Satellite      → structural_signal (Issue #25: Satellite wins)
      P6. Director Core, no structural Satellite    → director_signal (Core)
      P7. Structural Satellite (unique)             → structural_signal
      P8. Structural Satellite (ambiguous/multiple) → review_flagged
      P9. Structural Popcorn, no Satellite/Core     → structural_signal (popcorn sub-reason)
      P10. No signal                                → Unsorted

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
    ref_matches = [m for m in structural_matches if m.tier == 'Reference']
    sat_struct   = [m for m in structural_matches if m.tier == 'Satellite']
    pop_matches  = [m for m in structural_matches if m.tier == 'Popcorn']

    sat_dir_valid   = [m for m in director_matches if m.tier == 'Satellite' and m.decade_valid]
    core_dir        = [m for m in director_matches if m.tier == 'Core']

    # Deduplicate structural Satellite categories (preserve SATELLITE_ROUTING_RULES order)
    sat_struct_cats: List[str] = list(dict.fromkeys(
        m.category for m in sat_struct if m.category
    ))

    # === P1: Reference canon (structural wins unconditionally) ===
    if ref_matches:
        return IntegrationResult(
            tier='Reference', category=None, decade=decade,
            destination=f'Reference/{decade}/',
            confidence=_cap(1.0), reason='reference_canon',
            explanation='Reference canon title+year match',
        )

    # === P2 + P3 + P4: Director Satellite with decade_valid ===
    if sat_dir_valid:
        dm = sat_dir_valid[0]  # first match (SATELLITE_ROUTING_RULES order preserved)
        structural_same = any(sm.category == dm.category for sm in sat_struct)
        structural_diff = sat_struct_cats and not structural_same

        if structural_same:
            # P2: both signals agree
            reason = 'both_agree'
            conf = _cap(0.85)
            explanation = f'director + structure both matched {dm.category}'
        elif structural_diff:
            # P3: director resolves conflict between structural candidates
            reason = 'director_disambiguates'
            conf = _cap(0.75)
            explanation = (
                f'director matched {dm.category}, '
                f'structure matched {sat_struct_cats} (director wins)'
            )
        else:
            # P4: director signal only
            reason = 'director_signal'
            conf = _cap(0.65)
            explanation = f'director identity matched {dm.category} ({dm.source})'

        return IntegrationResult(
            tier='Satellite', category=dm.category, decade=decade,
            destination=f'Satellite/{dm.category}/{decade}/',
            confidence=conf, reason=reason, explanation=explanation,
        )

    # === P5: Director Core + structural Satellite → Satellite wins (Issue #25) ===
    if core_dir and sat_struct_cats:
        sat_cat = sat_struct_cats[0]
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(0.65), reason='structural_signal',
            explanation=(
                f'structural match {sat_cat} overrides Core director '
                f'(Satellite-before-Core, Issue #25)'
            ),
        )

    # === P6: Director Core, no structural Satellite ===
    if core_dir:
        dm = core_dir[0]
        canonical = dm.canonical_name or dm.category
        return IntegrationResult(
            tier='Core', category=canonical, decade=decade,
            destination=f'Core/{decade}/{canonical}/',
            confidence=_cap(1.0), reason='director_signal',
            explanation='Core director whitelist match',
        )

    # === P7: Structural Satellite, unique category ===
    if len(sat_struct_cats) == 1:
        sat_cat = sat_struct_cats[0]
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(0.65), reason='structural_signal',
            explanation=f'structural match {sat_cat}',
        )

    # === P8: Structural Satellite, multiple ambiguous categories ===
    if len(sat_struct_cats) > 1:
        sat_cat = sat_struct_cats[0]  # highest-priority by SATELLITE_ROUTING_RULES order
        return IntegrationResult(
            tier='Satellite', category=sat_cat, decade=decade,
            destination=f'Satellite/{sat_cat}/{decade}/',
            confidence=_cap(0.4), reason='review_flagged',
            explanation=f'ambiguous structural match: {sat_struct_cats} — routed to {sat_cat}',
        )

    # === P9: Popcorn ===
    if pop_matches:
        popcorn_reason = pop_matches[0].match_type  # 'popcorn_cast_popularity' etc.
        return IntegrationResult(
            tier='Popcorn', category=None, decade=decade,
            destination=f'Popcorn/{decade}/',
            confidence=_cap(0.65), reason=popcorn_reason,
            explanation='Popcorn structural signal',
        )

    # === P10: No signal ===
    return _unsorted()
