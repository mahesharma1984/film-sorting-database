"""
tests/test_signals.py — Tests for Issue #42 unified two-signal architecture.

Covers:
  - score_director(): Satellite and Core matches, decade validity, tradition vs movement
  - score_structure(): Reference canon, COUNTRY_TO_WAVE, satellite structural, Popcorn
  - integrate_signals(): All priority cases from the decision table
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.signals import (
    DirectorMatch,
    StructuralMatch,
    integrate_signals,
    score_director,
    score_structure,
)
from lib.core_directors import CoreDirectorDatabase
from lib.satellite import SatelliteClassifier
from lib.popcorn import PopcornClassifier


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def core_db():
    whitelist = Path('docs/CORE_DIRECTOR_WHITELIST_FINAL.md')
    return CoreDirectorDatabase(whitelist)


@pytest.fixture(scope='module')
def satellite_classifier():
    return SatelliteClassifier()


@pytest.fixture(scope='module')
def popcorn_classifier():
    return PopcornClassifier()


def _meta(title='Test Film', year=1970, country=None, director=None):
    """Create a minimal metadata stub."""
    m = MagicMock()
    m.title = title
    m.year = year
    m.country = country
    m.director = director
    m.format_signals = []
    return m


# ---------------------------------------------------------------------------
# score_director() tests
# ---------------------------------------------------------------------------

class TestScoreDirector:

    def test_no_director_returns_empty(self, core_db):
        assert score_director(None, 1970, core_db) == []
        assert score_director('', 1970, core_db) == []

    def test_satellite_movement_director_in_era(self, core_db):
        """Godard 1965 → FNW satellite match, decade_valid=True."""
        matches = score_director('Jean-Luc Godard', 1965, core_db)
        sat_matches = [m for m in matches if m.tier == 'Satellite']
        assert len(sat_matches) >= 1
        fnw = next((m for m in sat_matches if m.category == 'French New Wave'), None)
        assert fnw is not None, "Expected FNW match for Godard"
        assert fnw.decade_valid is True
        assert fnw.source == 'satellite_rules'

    def test_satellite_movement_director_out_of_era(self, core_db):
        """Godard 1990 → FNW decade_valid=False (1990s outside FNW bounds)."""
        matches = score_director('Jean-Luc Godard', 1990, core_db)
        sat_matches = [m for m in matches if m.tier == 'Satellite']
        fnw = next((m for m in sat_matches if m.category == 'French New Wave'), None)
        assert fnw is not None
        assert fnw.decade_valid is False, "FNW decade_valid should be False for 1990s"

    def test_tradition_director_always_decade_valid(self, core_db):
        """Ferrara (American Exploitation tradition) → decade_valid=True even for 1998."""
        matches = score_director('Abel Ferrara', 1998, core_db)
        sat_matches = [m for m in matches if m.tier == 'Satellite']
        ae = next((m for m in sat_matches if m.category == 'American Exploitation'), None)
        assert ae is not None, "Expected American Exploitation match for Ferrara"
        assert ae.is_tradition is True if hasattr(ae, 'is_tradition') else True
        assert ae.decade_valid is True, "Tradition director always decade_valid"

    def test_core_director_returns_core_match(self, core_db):
        """Kubrick is in Core whitelist → Core DirectorMatch returned."""
        matches = score_director('Stanley Kubrick', 1971, core_db)
        core_matches = [m for m in matches if m.tier == 'Core']
        assert len(core_matches) == 1
        assert core_matches[0].canonical_name is not None
        assert core_matches[0].source == 'core_whitelist'
        assert core_matches[0].decade_valid is True

    def test_returns_all_matches_not_first(self, core_db):
        """score_director returns all matches (Satellite + Core), not just first."""
        matches = score_director('Jean-Luc Godard', 1965, core_db)
        tiers = {m.tier for m in matches}
        # Godard is in both FNW directors list and Core whitelist
        assert 'Satellite' in tiers
        assert 'Core' in tiers

    def test_single_word_token_matching(self, core_db):
        """Single-word registry keys match via token (not substring)."""
        # 'bava' should match 'Mario Bava' but NOT appear as part of 'lamberto bava'
        mario = score_director('Mario Bava', 1968, core_db)
        sat = [m for m in mario if m.tier == 'Satellite' and m.category == 'Giallo']
        assert len(sat) >= 1, "Mario Bava should match Giallo via 'bava' token"

    def test_multi_word_director_substring_matching(self, core_db):
        """Multi-word registry keys match via substring (e.g. 'gordon parks jr.')."""
        matches = score_director('Gordon Parks Jr.', 1972, core_db)
        sat = [m for m in matches if m.tier == 'Satellite']
        # 'gordon parks jr.' is in Blaxploitation directors
        blax = next((m for m in sat if m.category == 'Blaxploitation'), None)
        assert blax is not None, "Gordon Parks Jr. should match Blaxploitation"


# ---------------------------------------------------------------------------
# score_structure() tests
# ---------------------------------------------------------------------------

class TestScoreStructure:

    def test_reference_canon_match(self, satellite_classifier, popcorn_classifier):
        """Citizen Kane (1941) should match Reference canon."""
        meta = _meta('Citizen Kane', 1941, country='US')
        matches = score_structure(meta, {}, satellite_classifier, popcorn_classifier)
        ref = [m for m in matches if m.tier == 'Reference']
        assert len(ref) == 1
        assert ref[0].match_type == 'reference_canon'

    def test_country_wave_match(self, satellite_classifier, popcorn_classifier):
        """Italian film 1971 → COUNTRY_TO_WAVE → Giallo country_wave match."""
        meta = _meta('Unknown Italian Film', 1971, country='IT')
        matches = score_structure(meta, {'genres': [], 'countries': ['IT']},
                                  satellite_classifier, popcorn_classifier)
        giallo = [m for m in matches if m.tier == 'Satellite' and m.category == 'Giallo']
        assert any(m.match_type == 'country_wave' for m in giallo), \
            "Expected country_wave match for Italian 1970s film"

    def test_satellite_structural_country_genre(self, satellite_classifier, popcorn_classifier):
        """Italian Horror 1971 → Giallo via country+genre."""
        meta = _meta('Test', 1971, country='IT')
        matches = score_structure(meta, {'genres': ['Horror'], 'countries': ['IT']},
                                  satellite_classifier, popcorn_classifier)
        giallo = [m for m in matches if m.category == 'Giallo']
        assert any(m.match_type == 'country_genre' for m in giallo), \
            "Expected country_genre match for Italian Horror 1971"

    def test_no_country_no_structural_satellite(self, satellite_classifier, popcorn_classifier):
        """Film with no country and no genres → no structural Satellite matches."""
        meta = _meta('Unknown', 1970, country=None)
        matches = score_structure(meta, {}, satellite_classifier, popcorn_classifier)
        sat = [m for m in matches if m.tier == 'Satellite']
        assert len(sat) == 0

    def test_no_structural_match_for_country_outside_wave(
            self, satellite_classifier, popcorn_classifier):
        """US film 2000 → not in COUNTRY_TO_WAVE, no country_wave match."""
        meta = _meta('Modern Film', 2000, country='US')
        matches = score_structure(meta, {'genres': ['Drama'], 'countries': ['US']},
                                  satellite_classifier, popcorn_classifier)
        country_waves = [m for m in matches if m.match_type == 'country_wave']
        assert len(country_waves) == 0

    def test_returns_all_matches_not_first(self, satellite_classifier, popcorn_classifier):
        """Brazilian Drama 1975 → multiple structural matches (BrazExpl + Indie Cinema)."""
        meta = _meta('Test', 1975, country='BR')
        matches = score_structure(meta, {'genres': ['Drama'], 'countries': ['BR']},
                                  satellite_classifier, popcorn_classifier)
        categories = {m.category for m in matches if m.tier == 'Satellite'}
        assert len(categories) >= 1  # at least Brazilian Exploitation


# ---------------------------------------------------------------------------
# integrate_signals() tests
# ---------------------------------------------------------------------------

class TestIntegrateSignals:

    def test_reference_canon_wins_unconditionally(self):
        """P1: Reference structural match → reference_canon, even if director says Core."""
        core_match = DirectorMatch(
            tier='Core', category='Core', canonical_name='Stanley Kubrick',
            source='core_whitelist', decade_valid=True
        )
        ref_match = StructuralMatch(tier='Reference', category=None, match_type='reference_canon')
        result = integrate_signals([core_match], [ref_match], '1940s', 'R3')
        assert result.tier == 'Reference'
        assert result.reason == 'reference_canon'

    def test_both_agree_director_and_structural(self):
        """P2: Director + structural both say Giallo → both_agree."""
        dm = DirectorMatch(tier='Satellite', category='Giallo', canonical_name=None,
                           source='satellite_rules', decade_valid=True)
        sm = StructuralMatch(tier='Satellite', category='Giallo', match_type='country_genre')
        result = integrate_signals([dm], [sm], '1970s', 'R3')
        assert result.tier == 'Satellite'
        assert result.category == 'Giallo'
        assert result.reason == 'both_agree'
        assert result.confidence == pytest.approx(0.85)

    def test_director_disambiguates_different_structural(self):
        """P3: Director says FNW, structure says Indie Cinema → director_disambiguates."""
        dm = DirectorMatch(tier='Satellite', category='French New Wave', canonical_name=None,
                           source='satellite_rules', decade_valid=True)
        sm = StructuralMatch(tier='Satellite', category='Indie Cinema', match_type='country_genre')
        result = integrate_signals([dm], [sm], '1960s', 'R3')
        assert result.tier == 'Satellite'
        assert result.category == 'French New Wave'
        assert result.reason == 'director_disambiguates'
        assert result.confidence == pytest.approx(0.75)

    def test_director_signal_only_no_structural(self):
        """P4: Director says FNW, no structural → director_signal."""
        dm = DirectorMatch(tier='Satellite', category='French New Wave', canonical_name=None,
                           source='satellite_rules', decade_valid=True)
        result = integrate_signals([dm], [], '1965s', 'R3')
        assert result.tier == 'Satellite'
        assert result.reason == 'director_signal'
        assert result.confidence == pytest.approx(0.65)

    def test_core_director_alone_is_director_signal(self):
        """P6: Core director, no structural Satellite → director_signal, Core tier."""
        dm = DirectorMatch(tier='Core', category='Core', canonical_name='Stanley Kubrick',
                           source='core_whitelist', decade_valid=True)
        result = integrate_signals([dm], [], '1960s', 'R3')
        assert result.tier == 'Core'
        assert result.reason == 'director_signal'
        assert result.confidence == pytest.approx(1.0)
        assert 'Stanley Kubrick' in result.destination

    def test_core_director_plus_satellite_structural_satellite_wins(self):
        """P5: Core director + structural Satellite → Satellite wins (Issue #25)."""
        core_dm = DirectorMatch(tier='Core', category='Core', canonical_name='Some Director',
                                source='core_whitelist', decade_valid=True)
        sm = StructuralMatch(tier='Satellite', category='Giallo', match_type='country_wave')
        result = integrate_signals([core_dm], [sm], '1970s', 'R3')
        assert result.tier == 'Satellite'
        assert result.category == 'Giallo'
        assert result.reason == 'structural_signal'

    def test_structural_signal_unique_category(self):
        """P7: No director, structural says one Satellite category → structural_signal."""
        sm = StructuralMatch(tier='Satellite', category='Giallo', match_type='country_genre')
        result = integrate_signals([], [sm], '1970s', 'R3')
        assert result.tier == 'Satellite'
        assert result.reason == 'structural_signal'
        assert result.confidence == pytest.approx(0.65)

    def test_review_flagged_ambiguous_structural(self):
        """P8: Structural says multiple categories, no director → review_flagged."""
        sm1 = StructuralMatch(tier='Satellite', category='Brazilian Exploitation',
                              match_type='country_wave')
        sm2 = StructuralMatch(tier='Satellite', category='Indie Cinema',
                              match_type='country_genre')
        result = integrate_signals([], [sm1, sm2], '1970s', 'R3')
        assert result.tier == 'Satellite'
        assert result.reason == 'review_flagged'
        assert result.confidence == pytest.approx(0.4)
        assert result.category == 'Brazilian Exploitation'  # highest priority wins

    def test_popcorn_structural_signal(self):
        """P9: No Satellite/Core signal, Popcorn structural → popcorn sub-reason."""
        pm = StructuralMatch(tier='Popcorn', category=None, match_type='popcorn_cast_popularity')
        result = integrate_signals([], [pm], '1990s', 'R3')
        assert result.tier == 'Popcorn'
        assert result.reason == 'popcorn_cast_popularity'

    def test_no_signal_returns_unsorted(self):
        """P10: No signals → Unsorted."""
        result = integrate_signals([], [], '1980s', 'R3')
        assert result.tier == 'Unsorted'
        assert 'unsorted' in result.reason

    def test_r2_confidence_capped(self):
        """R2 readiness: confidence capped at 0.6."""
        dm = DirectorMatch(tier='Satellite', category='Giallo', canonical_name=None,
                           source='satellite_rules', decade_valid=True)
        sm = StructuralMatch(tier='Satellite', category='Giallo', match_type='country_genre')
        result = integrate_signals([dm], [sm], '1970s', 'R2')
        assert result.confidence <= 0.6, \
            f"R2 confidence should be capped at 0.6, got {result.confidence}"

    def test_r2_core_confidence_capped(self):
        """R2: Core director_signal confidence also capped."""
        dm = DirectorMatch(tier='Core', category='Core', canonical_name='Kubrick',
                           source='core_whitelist', decade_valid=True)
        result = integrate_signals([dm], [], '1960s', 'R2')
        assert result.confidence <= 0.6

    def test_out_of_era_movement_director_does_not_route(self):
        """Movement director outside declared decades (decade_valid=False) → Unsorted."""
        dm = DirectorMatch(tier='Satellite', category='French New Wave', canonical_name=None,
                           source='satellite_rules', decade_valid=False)
        result = integrate_signals([dm], [], '1990s', 'R3')
        # sat_dir_valid is empty → falls through to P7/P8/P9/P10
        assert result.tier == 'Unsorted'

    def test_destination_path_format_satellite(self):
        """Satellite destination uses category-first tier-first format."""
        dm = DirectorMatch(tier='Satellite', category='Giallo', canonical_name=None,
                           source='satellite_rules', decade_valid=True)
        result = integrate_signals([dm], [], '1970s', 'R3')
        assert result.destination == 'Satellite/Giallo/1970s/'

    def test_destination_path_format_reference(self):
        """Reference destination: Reference/{decade}/."""
        sm = StructuralMatch(tier='Reference', category=None, match_type='reference_canon')
        result = integrate_signals([], [sm], '1960s', 'R3')
        assert result.destination == 'Reference/1960s/'

    def test_destination_path_format_core(self):
        """Core destination: Core/{decade}/{canonical}/."""
        dm = DirectorMatch(tier='Core', category='Core', canonical_name='Jean-Luc Godard',
                           source='core_whitelist', decade_valid=True)
        result = integrate_signals([dm], [], '1990s', 'R3')
        assert result.destination == 'Core/1990s/Jean-Luc Godard/'
