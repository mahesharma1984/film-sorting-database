#!/usr/bin/env python3
"""
Satellite category classification using TMDb structured data

Issue #6 Update: Decade-validated director-based routing
- Replaces hardcoded director_mappings with SATELLITE_ROUTING_RULES from constants
- Adds decade validation to ALL director-based routing (critical bug fix)
- Adds 6 new directors and Japanese Exploitation category
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from lib.director_matching import match_director

logger = logging.getLogger(__name__)


class SatelliteClassifier:
    """Classify films into Satellite categories using TMDb structured data"""

    def __init__(self, categories_file=None, core_db=None):
        """
        Initialize classifier with category definitions and caps

        Note: categories_file parameter kept for compatibility but not used
        Issue #6: Added Japanese Exploitation category
        Issue #16: Added core_db for defensive Core director check
        """
        # These caps bound auto-classification only. Human-curated (explicit lookup)
        # results are never blocked — increment_count() logs a warning if exceeded.
        # Cult Oddities: no SATELLITE_ROUTING_RULES entry → no auto-classification path.
        # Human-curated only; cap removed to avoid dead code confusion.
        self.caps = {
            'Giallo': 30,
            'Japanese New Wave': 15,      # Issue #33
            'Pinku Eiga': 35,
            'Japanese Exploitation': 25,  # Issue #6
            'Brazilian Exploitation': 45,
            'Hong Kong New Wave': 15,     # Issue #34
            'Hong Kong Category III': 10, # Issue #34
            'Hong Kong Action': 65,
            'American Exploitation': 80,
            'European Sexploitation': 25,
            'Blaxploitation': 20,
            'Music Films': 35,
        }
        self.counts = defaultdict(int)  # Track category counts
        self.core_db = core_db  # Issue #16: optional CoreDirectorDatabase for defensive check

    def classify(self, metadata, tmdb_data: Optional[Dict]) -> Optional[str]:
        """Thin wrapper around evaluate_category() — director-inclusive routing (Issue #54).

        Iterates SATELLITE_ROUTING_RULES with include_director=True (classify() mode).
        Returns the first matching category name after cap enforcement, or None.

        When tmdb_data is absent but metadata has a director, constructs a minimal dict
        so director-only routing rules (FNW, JNW, etc.) can still fire.
        Country/genre-based rules won't fire because countries=[] and genres=[] give no match.
        """
        if not tmdb_data:
            if not (hasattr(metadata, 'director') and metadata.director):
                return None
            tmdb_data = {
                'director': metadata.director,
                'year': metadata.year,
                'countries': [],
                'genres': [],
                'cast': [],
                'keywords': [],
                'overview': '',
                'tagline': '',
                'plot': '',
            }

        from lib.constants import SATELLITE_ROUTING_RULES

        director = tmdb_data.get('director', '') or ''
        year = tmdb_data.get('year')
        director_lower = director.lower()
        film_data = {
            'director_lower': director_lower,
            'director_tokens': set(director_lower.split()) if director else set(),
            'decade': f"{(year // 10) * 10}s" if year else None,
            'countries': tmdb_data.get('countries', []),
            'genres': tmdb_data.get('genres', []),
            'title': (tmdb_data.get('title') or getattr(metadata, 'title', '') or '').lower(),
            'tmdb_data': tmdb_data,
        }

        for category_name, rules in SATELLITE_ROUTING_RULES.items():
            match_type = self.evaluate_category(film_data, category_name, rules, include_director=True)
            if match_type is not None:
                return self._check_cap(category_name)

        return None

    def evidence_classify(self, metadata, tmdb_data: Optional[Dict]) -> 'SatelliteEvidence':
        """Read-only evidence-producing twin of classify().

        Runs the same gate logic as classify() but:
        - Returns SatelliteEvidence instead of Optional[str]
        - Uses three-valued gate logic: pass / fail / untestable
        - Never calls _check_cap() or increments self.counts
        - Records evidence for every category, including ones that fail early

        Issue #35: Used by _gather_evidence() in classify.py (shadow pass).
        """
        from lib.constants import (
            SATELLITE_ROUTING_RULES,
            AMERICAN_EXPLOITATION_TITLE_KEYWORDS,
            BLAXPLOITATION_TITLE_KEYWORDS,
            GateResult, CategoryEvidence, SatelliteEvidence,
        )

        per_category: Dict[str, CategoryEvidence] = {}

        # Construct minimal dict when tmdb_data absent (mirrors classify() behaviour)
        if not tmdb_data:
            if not (hasattr(metadata, 'director') and metadata.director):
                return SatelliteEvidence(matched_category=None, per_category={})
            tmdb_data = {
                'director': metadata.director,
                'year': metadata.year,
                'countries': [],
                'genres': [],
                'cast': [],
                'keywords': [],
                'overview': '',
                'tagline': '',
                'plot': '',
            }

        countries = tmdb_data.get('countries', [])
        genres = tmdb_data.get('genres', [])
        director = tmdb_data.get('director', '') or ''
        year = tmdb_data.get('year')
        title = (tmdb_data.get('title') or getattr(metadata, 'title', '') or '').lower()
        director_lower = director.lower()
        director_tokens = set(director_lower.split())

        decade = None
        if year:
            decade = f"{(year // 10) * 10}s"

        matched_category = None

        for category_name, rules in SATELLITE_ROUTING_RULES.items():
            ev = CategoryEvidence()

            # Issue #40 Phase 2: tradition categories evaluate director gate BEFORE the decade
            # gate, mirroring the new logic in classify(). This makes evidence trails accurate —
            # a Ferrara 1998 film now correctly shows director_gate=pass for American Exploitation
            # instead of decade_gate=fail (which previously hid the director signal entirely).
            is_tradition = rules.get('is_tradition', bool(rules['country_codes']))

            # --- Director gate (tradition categories: fires before decade gate) ---
            if is_tradition and rules['directors']:
                if director:
                    matched_dir = next(
                        (d for d in rules['directors']
                         if self._director_matches(director_lower, director_tokens, d)),
                        None,
                    )
                    if matched_dir:
                        ev.director_gate = GateResult('pass', value=matched_dir)
                        ev.matched = True
                        per_category[category_name] = ev
                        if matched_category is None:
                            matched_category = category_name
                        continue  # director match wins — skip decade/country/genre path
                    else:
                        ev.director_gate = GateResult('fail', reason=f'{director!r} not in directors list')
                else:
                    ev.director_gate = GateResult('untestable', reason='no director data')

            # --- Decade gate ---
            if rules['decades'] is not None:
                if decade and decade in rules['decades']:
                    ev.decade_gate = GateResult('pass', value=decade)
                elif not decade:
                    ev.decade_gate = GateResult('untestable', reason='year absent — decade unknown')
                else:
                    ev.decade_gate = GateResult('fail', reason=f'{decade} not in {rules["decades"]}')
                    per_category[category_name] = ev
                    continue  # decade-bounded and out of range — skip remaining gates
            # else: no decade restriction → leave as 'not_applicable'

            # --- Director gate (movement categories: fires after decade gate) ---
            if not is_tradition and rules['directors']:
                if director:
                    matched_dir = next(
                        (d for d in rules['directors']
                         if self._director_matches(director_lower, director_tokens, d)),
                        None,
                    )
                    if matched_dir:
                        ev.director_gate = GateResult('pass', value=matched_dir)
                        ev.matched = True
                        per_category[category_name] = ev
                        if matched_category is None:
                            matched_category = category_name
                        continue  # director match wins — skip country/genre path
                    else:
                        ev.director_gate = GateResult('fail', reason=f'{director!r} not in directors list')
                else:
                    ev.director_gate = GateResult('untestable', reason='no director data')

            # --- Country gate ---
            if rules['country_codes'] is not None:
                if countries:
                    matched_country = next(
                        (c for c in rules['country_codes'] if c in countries), None
                    )
                    if matched_country:
                        ev.country_gate = GateResult('pass', value=matched_country)
                    else:
                        ev.country_gate = GateResult(
                            'fail',
                            reason=f'{countries} ∩ {rules["country_codes"]} = ∅',
                        )
                else:
                    ev.country_gate = GateResult('untestable', reason='countries=[] — no country data')
            # else: no country restriction → leave as 'not_applicable'

            # --- Genre gate ---
            if rules['genres'] is not None:
                if genres:
                    matched_genre = next(
                        (g for g in rules['genres'] if g in genres), None
                    )
                    if matched_genre:
                        ev.genre_gate = GateResult('pass', value=matched_genre)
                    else:
                        ev.genre_gate = GateResult(
                            'fail',
                            reason=f'genres={genres} ∩ {rules["genres"]} = ∅',
                        )
                else:
                    ev.genre_gate = GateResult('untestable', reason='genres=[] — no genre data from API')
            # else: no genre restriction → leave as 'not_applicable'

            # --- Title keyword gate (American Exploitation, Blaxploitation) ---
            if category_name == 'American Exploitation':
                if self._title_matches_keywords(title, AMERICAN_EXPLOITATION_TITLE_KEYWORDS):
                    ev.title_kw_gate = GateResult('pass')
                else:
                    ev.title_kw_gate = GateResult('fail', reason='title keyword gate')
            elif category_name == 'Blaxploitation':
                if self._title_matches_keywords(title, BLAXPLOITATION_TITLE_KEYWORDS):
                    ev.title_kw_gate = GateResult('pass')
                else:
                    ev.title_kw_gate = GateResult('fail', reason='title keyword gate')

            # --- Determine match via country + genre path ---
            country_passes = ev.country_gate.status == 'pass'
            genre_passes = ev.genre_gate.status == 'pass'
            title_kw_passes = ev.title_kw_gate.status in ('pass', 'not_applicable')

            if country_passes and genre_passes and title_kw_passes:
                ev.matched = True
                per_category[category_name] = ev
                if matched_category is None:
                    matched_category = category_name
                continue

            # --- Keyword gate (Tier A: country + keyword waives genre) ---
            keyword_signals = rules.get('keyword_signals')
            if keyword_signals and country_passes and not genre_passes:
                hit, source = self._keyword_hit(tmdb_data, keyword_signals)
                if hit:
                    ev.keyword_gate = GateResult('pass', value=source)
                    ev.matched = True
                    per_category[category_name] = ev
                    if matched_category is None:
                        matched_category = category_name
                    continue
                else:
                    ev.keyword_gate = GateResult('fail', reason='no keyword signal matched')

            # --- Keyword gate (Tier B: TMDb tag alone for movement categories) ---
            if rules.get('tier_b_eligible') and keyword_signals:
                tmdb_tags_lower = [k.lower() for k in tmdb_data.get('keywords', [])]
                matched_tag = next(
                    (tag for tag in keyword_signals.get('tmdb_tags', [])
                     if tag in tmdb_tags_lower),
                    None,
                )
                if matched_tag:
                    ev.keyword_gate = GateResult('pass', value=f'tier_b:{matched_tag}')
                    ev.matched = True
                    per_category[category_name] = ev
                    if matched_category is None:
                        matched_category = category_name
                    continue

            per_category[category_name] = ev

        return SatelliteEvidence(matched_category=matched_category, per_category=per_category)

    @staticmethod
    def _director_matches(director_lower: str, director_tokens: set, entry: str) -> bool:
        """Thin wrapper — delegates to lib.director_matching.match_director (Issue #54).

        Signature preserved for call-site compatibility. director_tokens is unused
        (match_director splits internally), retained to avoid changing all callers.
        """
        return match_director(director_lower, entry)

    @staticmethod
    def _title_matches_keywords(title: str, keywords) -> bool:
        """Conservative title keyword gate for high-false-positive categories."""
        if not title:
            return False
        return any(keyword in title for keyword in keywords)

    @staticmethod
    def _keyword_hit(tmdb_data: Dict, signals: Dict):
        """Check TMDb keyword tags and text fields for keyword_signals matches.

        Returns (hit: bool, source: str | None).
        TMDb tags checked first (higher precision). Text terms scan overview, tagline, plot.
        """
        tmdb_tags_lower = [k.lower() for k in tmdb_data.get('keywords', [])]
        text_blob = ' '.join([
            tmdb_data.get('overview', '') or '',
            tmdb_data.get('tagline', '') or '',
            tmdb_data.get('plot', '') or '',
        ]).lower()

        for tag in signals.get('tmdb_tags', []):
            if tag.lower() in tmdb_tags_lower:
                return True, 'tmdb_tag'
        for term in signals.get('text_terms', []):
            if term.lower() in text_blob:
                return True, 'text_term'
        return False, None

    def evaluate_category(
        self,
        film_data: Dict,
        category_name: str,
        rules: Dict,
        include_director: bool = True,
    ) -> Optional[str]:
        """Evaluate one category rule against pre-extracted film data (Issue #54).

        Single shared implementation of the per-category evaluation loop — replaces
        duplicate logic in classify() and classify_structural().

        Returns match_type string if category matches:
          'director'        — director identity match (tradition or movement)
          'country_genre'   — country + genre structural match (including Tier 3 untestable)
          'keyword_tier_a'  — country + keyword hit (genre gate waived)
          'keyword_tier_b'  — TMDb tag alone for tier_b_eligible movement categories
        Returns None if no match.

        Does NOT enforce caps — caller is responsible for _check_cap().

        Args:
            film_data: pre-extracted dict with keys:
                director_lower (str), director_tokens (set), decade (Optional[str]),
                countries (List[str]), genres (List[str]), title (str), tmdb_data (Dict)
            include_director: True = classify() mode (director checks active,
                structural match limited to tradition categories);
                False = classify_structural() mode (no director checks,
                structural match for all categories).
        """
        from lib.constants import (
            AMERICAN_EXPLOITATION_TITLE_KEYWORDS,
            BLAXPLOITATION_TITLE_KEYWORDS,
            CATEGORY_CERTAINTY_TIERS,
        )

        is_tradition = rules.get('is_tradition', bool(rules['country_codes']))
        director_lower = film_data.get('director_lower', '')
        director_tokens = film_data.get('director_tokens', set())
        decade = film_data.get('decade')
        countries = film_data.get('countries', [])
        genres = film_data.get('genres', [])
        title = film_data.get('title', '')
        tmdb_data = film_data.get('tmdb_data', {})

        # --- Director check: tradition categories fire BEFORE decade gate ---
        # (Issue #40 Phase 2: director identity persists across eras for tradition categories)
        if include_director and is_tradition and rules['directors'] and director_lower:
            if any(self._director_matches(director_lower, director_tokens, d)
                   for d in rules['directors']):
                return 'director'

        # --- Decade gate ---
        if rules['decades'] is not None and decade not in rules['decades']:
            return None

        # --- Director check: movement categories fire AFTER decade gate ---
        # (ensures only era-appropriate films route to FNW/AmNH/JNW via director)
        if include_director and not is_tradition and rules['directors'] and director_lower:
            if any(self._director_matches(director_lower, director_tokens, d)
                   for d in rules['directors']):
                return 'director'

        # --- Structural match path ---
        # classify() mode (include_director=True): only tradition categories (Issue #45).
        # classify_structural() mode (include_director=False): all categories.
        structural_enabled = is_tradition or not include_director

        # Country match
        country_match = True  # default: no restriction
        if rules['country_codes'] is not None:
            country_match = any(c in countries for c in rules['country_codes'])

        # Genre match — three-valued: True / False / None (untestable when genres=[])
        genre_match = True  # default: no restriction
        if rules['genres'] is not None:
            if not genres:
                genre_match = None  # data absent — untestable
            else:
                genre_match = any(g in genres for g in rules['genres'])

        # Title keyword gates (high-false-positive categories)
        if category_name == 'American Exploitation':
            if not self._title_matches_keywords(title, AMERICAN_EXPLOITATION_TITLE_KEYWORDS):
                return None
        if category_name == 'Blaxploitation':
            if not self._title_matches_keywords(title, BLAXPLOITATION_TITLE_KEYWORDS):
                return None

        # Country + genre structural match (positive genre evidence required)
        if structural_enabled and country_match and genre_match is True:
            return 'country_genre'

        # Tier 3 untestable genre: genre data absent but country matched
        # (Issue #34: Tier 1-2 categories require genre evidence; Tier 3+ can route on country alone)
        if structural_enabled and country_match and genre_match is None and rules['country_codes'] is not None:
            tier = CATEGORY_CERTAINTY_TIERS.get(category_name, 2)
            if tier >= 3:
                return 'country_genre'

        # Tier 1-2 partial structural match (Issue #56): country+decade pass, genre data absent.
        # Only in classify_structural() mode (include_director=False) — structural signal only.
        # Absent evidence ≠ negative evidence (Dempster-Shafer): surface as partial match with
        # uncertainty rather than silently discarding. Caller (score_structure) sets uncertainty=0.5.
        # Tier 4 categories (manual-only) are excluded (tier < 3 guard).
        if (not include_director and structural_enabled and country_match
                and genre_match is None and rules['country_codes'] is not None):
            tier = CATEGORY_CERTAINTY_TIERS.get(category_name, 2)
            if tier < 3:
                return 'partial_structural'

        # Keyword Tier A: country match + keyword hit waives the genre gate (Issue #29)
        keyword_signals = rules.get('keyword_signals')
        if keyword_signals and country_match and genre_match is not True:
            hit, _ = self._keyword_hit(tmdb_data, keyword_signals)
            if hit:
                return 'keyword_tier_a'

        # Keyword Tier B: TMDb tag alone for tier_b_eligible movement categories (Issue #29)
        if rules.get('tier_b_eligible') and keyword_signals:
            tmdb_tags_lower = [k.lower() for k in tmdb_data.get('keywords', [])]
            if any(tag in tmdb_tags_lower for tag in keyword_signals.get('tmdb_tags', [])):
                return 'keyword_tier_b'

        return None

    def classify_structural(self, metadata, tmdb_data: Optional[Dict]) -> List[Tuple[str, str]]:
        """Thin wrapper around evaluate_category() — structural-only routing (Issue #54).

        Iterates SATELLITE_ROUTING_RULES with include_director=False (classify_structural() mode).
        Returns ALL matching (category_name, match_type) pairs — no short-circuit, no cap.
        Director checks are intentionally excluded — use score_director() for those.

        Issue #42: Used by lib/signals.score_structure() to compute the structural
        triangulation signal independently from the director identity signal.

        Returns list of (category_name, match_type) tuples where match_type is one of:
          'country_genre'  — country + genre (or Tier 3 untestable genre) match
          'keyword_tier_a' — country + keyword hit (genre gate waived)
          'keyword_tier_b' — TMDb tag alone for tier_b_eligible movement categories
        """
        from lib.constants import SATELLITE_ROUTING_RULES

        year = getattr(metadata, 'year', None)
        tmdb_data = tmdb_data or {}

        # Merge metadata.country + tmdb countries (with uppercase normalization)
        countries = [c.upper() for c in (tmdb_data.get('countries') or [])]
        metadata_country = getattr(metadata, 'country', None)
        if metadata_country and metadata_country.upper() not in countries:
            countries.append(metadata_country.upper())

        film_data = {
            'director_lower': '',  # structural signal: no director
            'director_tokens': set(),
            'decade': f"{(year // 10) * 10}s" if year else None,
            'countries': countries,
            'genres': list(tmdb_data.get('genres') or []),
            'title': (getattr(metadata, 'title', '') or '').lower(),
            'tmdb_data': tmdb_data,
        }

        results: List[Tuple[str, str]] = []
        for category_name, rules in SATELLITE_ROUTING_RULES.items():
            match_type = self.evaluate_category(film_data, category_name, rules, include_director=False)
            if match_type is not None:
                results.append((category_name, match_type))

        return results

    def is_capped(self, category: str) -> bool:
        """Read-only cap check — does NOT increment. Used for pre-flight checks."""
        if category not in self.caps:
            return False
        return self.counts[category] >= self.caps[category]

    def _check_cap(self, category: str) -> Optional[str]:
        """Check if category has reached cap"""
        if category not in self.caps:
            return category

        if self.counts[category] >= self.caps[category]:
            logger.warning(f"Category '{category}' at cap ({self.caps[category]})")
            return None

        self.counts[category] += 1
        return category

    def increment_count(self, category: str):
        """Increment count for explicit lookup results (Issue #25 D7).

        Explicit lookup entries are NOT blocked by the cap — human curation
        overrides auto-classification limits. A warning is logged when the cap
        is exceeded so the collection can be audited.
        """
        self.counts[category] += 1
        if category in self.caps and self.counts[category] > self.caps[category]:
            logger.warning(
                "Satellite category '%s' has %d entries, exceeding auto-classification "
                "cap of %d. These are explicit lookup entries — not blocked, but worth auditing.",
                category, self.counts[category], self.caps[category]
            )

    def get_stats(self) -> Dict:
        """Get category classification statistics"""
        return {
            'counts': dict(self.counts),
            'caps': self.caps,
            'available': {cat: self.caps[cat] - self.counts[cat] for cat in self.caps}
        }
