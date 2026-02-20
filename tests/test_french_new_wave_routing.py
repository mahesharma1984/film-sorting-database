"""Test French New Wave category routing (Issue #14)

This test suite validates that:
1. French New Wave directors route to Satellite/French New Wave
2. French New Wave category comes BEFORE European Sexploitation in priority
3. French erotica still routes to European Sexploitation
4. Decade bounds are respected (1950s-1970s for FNW)
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.satellite import SatelliteClassifier
from lib.parser import FilmMetadata


class TestFrenchNewWaveRouting:
    """Validate French New Wave category"""

    @pytest.fixture
    def classifier(self):
        return SatelliteClassifier()

    @pytest.fixture
    def mock_metadata(self):
        return FilmMetadata(filename="test.mkv", title="test", year=1962)

    # =========================================================================
    # TEST GROUP 1: French New Wave directors route correctly
    # =========================================================================

    def test_marker_1960s_routes_to_fnw(self, classifier, mock_metadata):
        """Chris Marker 1962 → French New Wave (NOT European Sexploitation)

        This is the PRIMARY test for Issue #14. Before the fix, Marker's
        La jetée was routing to European Sexploitation.
        """
        tmdb_data = {
            'director': 'Chris Marker',
            'year': 1962,
            'countries': ['FR'],
            'genres': ['Documentary']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave'

    def test_rohmer_1960s_routes_to_fnw(self, classifier, mock_metadata):
        """Eric Rohmer 1969 → French New Wave"""
        tmdb_data = {
            'director': 'Éric Rohmer',
            'year': 1969,
            'countries': ['FR'],
            'genres': ['Drama', 'Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave'

    def test_resnais_1960s_routes_to_fnw(self, classifier, mock_metadata):
        """Alain Resnais 1961 → French New Wave

        Note: If Resnais is promoted to Core, this should fail and
        the test should be updated
        """
        tmdb_data = {
            'director': 'Alain Resnais',
            'year': 1961,
            'countries': ['FR'],
            'genres': ['Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        # Resnais might be Core - accept either
        assert result in ['French New Wave', None]

    def test_rivette_1970s_routes_to_fnw(self, classifier, mock_metadata):
        """Jacques Rivette 1974 → French New Wave or Core

        Note: Rivette is on Core whitelist, so might not route to Satellite
        """
        tmdb_data = {
            'director': 'Jacques Rivette',
            'year': 1974,
            'countries': ['FR'],
            'genres': ['Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        # Rivette is Core, so this might return None (Core handles it first)
        assert result in ['French New Wave', None]

    def test_malle_1950s_routes_to_fnw(self, classifier, mock_metadata):
        """Louis Malle 1958 → French New Wave (extends to 1950s)"""
        tmdb_data = {
            'director': 'Louis Malle',
            'year': 1958,
            'countries': ['FR'],
            'genres': ['Crime', 'Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave'

    # =========================================================================
    # TEST GROUP 2: French New Wave vs European Sexploitation priority
    # =========================================================================

    def test_french_erotica_still_routes_to_sexploitation(self, classifier, mock_metadata):
        """Just Jaeckin Emmanuelle 1974 → European Sexploitation (NOT French New Wave)

        Validates that European Sexploitation still works for actual erotica
        """
        tmdb_data = {
            'director': 'Just Jaeckin',
            'year': 1974,
            'countries': ['FR'],
            'genres': ['Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'European Sexploitation'

    def test_borowczyk_routes_to_sexploitation(self, classifier, mock_metadata):
        """Walerian Borowczyk 1973 → European Sexploitation"""
        tmdb_data = {
            'director': 'Walerian Borowczyk',
            'year': 1973,
            'countries': ['FR'],
            'genres': ['Drama', 'Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'European Sexploitation'

    def test_marker_not_routed_to_sexploitation(self, classifier, mock_metadata):
        """Chris Marker should NEVER route to European Sexploitation

        Critical test: validates director matching happens before country matching
        """
        tmdb_data = {
            'director': 'Chris Marker',
            'year': 1962,
            'countries': ['FR'],
            'genres': ['Documentary']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result != 'European Sexploitation'
        assert result == 'French New Wave'

    # =========================================================================
    # TEST GROUP 3: Decade bounds validation
    # =========================================================================

    def test_rohmer_1990s_routes_to_indie_cinema(self, classifier, mock_metadata):
        """Eric Rohmer 1996 → Indie Cinema (outside FNW 1950s-1970s decade bounds)

        Issue #20: FNW decade bounds are 1950s-1970s. Director routing respects
        decade bounds (Issue #6 design). Late Rohmer (1990s) falls through FNW
        to Indie Cinema catch-all (FR + 1990s + Romance).
        """
        tmdb_data = {
            'director': 'Éric Rohmer',
            'year': 1996,
            'countries': ['FR'],
            'genres': ['Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'Indie Cinema'  # Decade check prevents FNW; Indie Cinema catch-all applies

    def test_french_1980s_non_fnw_director_no_match(self, classifier, mock_metadata):
        """French 1980s film by unknown director → NOT French New Wave

        Validates that FNW category respects decade bounds for non-director matches
        """
        tmdb_data = {
            'director': 'Unknown French Director',
            'year': 1985,
            'countries': ['FR'],
            'genres': ['Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        # 1980s is outside FNW decade bounds (1950s-1970s)
        # Should not route to FNW without director match
        assert result != 'French New Wave'

    def test_french_1940s_pre_fnw(self, classifier, mock_metadata):
        """French 1940s film → NOT French New Wave (pre-movement)"""
        tmdb_data = {
            'director': 'Unknown French Director',
            'year': 1945,
            'countries': ['FR'],
            'genres': ['Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        # 1940s is before FNW movement (starts 1958)
        assert result != 'French New Wave'

    # =========================================================================
    # TEST GROUP 4: Genre validation
    # =========================================================================

    def test_marker_documentary_genre_accepted(self, classifier, mock_metadata):
        """Chris Marker documentary → French New Wave

        Validates that Documentary genre is accepted for FNW
        (European Sexploitation removed 'Documentary' to avoid Marker)
        """
        tmdb_data = {
            'director': 'Chris Marker',
            'year': 1962,
            'countries': ['FR'],
            'genres': ['Documentary']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave'

    def test_rohmer_romance_genre_accepted(self, classifier, mock_metadata):
        """Eric Rohmer romance → French New Wave"""
        tmdb_data = {
            'director': 'Éric Rohmer',
            'year': 1969,
            'countries': ['FR'],
            'genres': ['Romance', 'Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave'

    # =========================================================================
    # TEST GROUP 5: Director name variations
    # =========================================================================

    def test_rohmer_accent_variation(self, classifier, mock_metadata):
        """Éric Rohmer vs Eric Rohmer - both should work"""
        for director_name in ['Éric Rohmer', 'Eric Rohmer', 'eric rohmer']:
            tmdb_data = {
                'director': director_name,
                'year': 1969,
                'countries': ['FR'],
                'genres': ['Drama']
            }
            result = classifier.classify(mock_metadata, tmdb_data)
            assert result == 'French New Wave', f"Failed for director name: {director_name}"

    def test_marker_case_variations(self, classifier, mock_metadata):
        """Chris Marker case variations"""
        for director_name in ['Chris Marker', 'chris marker', 'CHRIS MARKER']:
            tmdb_data = {
                'director': director_name,
                'year': 1962,
                'countries': ['FR'],
                'genres': ['Documentary']
            }
            result = classifier.classify(mock_metadata, tmdb_data)
            assert result == 'French New Wave', f"Failed for director name: {director_name}"

    # =========================================================================
    # TEST GROUP 6: Issue #22 — Core audit additions (Truffaut, Robbe-Grillet)
    #               and Core/FNW boundary documentation
    # =========================================================================

    def test_truffaut_routes_to_french_new_wave(self, classifier, mock_metadata):
        """François Truffaut → French New Wave (Issue #22: confirmed not in Core whitelist)

        Truffaut was not in the Core director whitelist (only Godard, Varda etc. are Core).
        Added 'truffaut' to FNW directors list in Issue #22.
        """
        tmdb_data = {
            'director': 'François Truffaut',
            'year': 1962,
            'countries': ['FR'],
            'genres': ['Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave', (
            f"Truffaut (non-Core) should route to French New Wave, got {result!r}"
        )

    def test_robbe_grillet_routes_to_french_new_wave(self, classifier, mock_metadata):
        """Alain Robbe-Grillet → French New Wave (Issue #22: confirmed not in Core whitelist)

        Robbe-Grillet's hyphenated surname is a single token under str.split(), so
        whole-word matching (Issue #25 D1) correctly matches 'robbe-grillet'.
        """
        tmdb_data = {
            'director': 'Alain Robbe-Grillet',
            'year': 1963,
            'countries': ['FR'],
            'genres': ['Drama', 'Mystery']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave', (
            f"Robbe-Grillet (non-Core) should route to French New Wave, got {result!r}"
        )

    def test_eustache_routes_to_french_new_wave(self, classifier, mock_metadata):
        """Jean Eustache 1973 → French New Wave"""
        tmdb_data = {
            'director': 'Jean Eustache',
            'year': 1973,
            'countries': ['FR'],
            'genres': ['Drama', 'Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave', (
            f"Eustache should route to French New Wave, got {result!r}"
        )

    def test_godard_routes_to_fnw_in_movement_period(self, classifier, mock_metadata):
        """Godard 1960 → French New Wave (Issue #25: Core guard removed)

        Issue #25 removed the Core director guard from SatelliteClassifier. Core directors
        whose films fall within a movement's decade bounds now route to that movement.
        Godard is in the FNW directors list; 1960s is within FNW bounds → French New Wave.
        The main pipeline (classify.py) fires Satellite before Core, so Godard 1960s films
        reach this point and correctly land in FNW.
        """
        tmdb_data = {
            'director': 'Jean-Luc Godard',
            'year': 1960,
            'countries': ['FR'],
            'genres': ['Drama']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave', (
            f"Godard 1960 should route to French New Wave (movement period), got {result!r}"
        )

    def test_unknown_french_1965_drama_falls_to_european_sexploitation(self, classifier, mock_metadata):
        """Unknown French director + 1965 + Drama → European Sexploitation

        Issue #22 Scenario B: France is NOT in COUNTRY_TO_WAVE (intentional).
        FNW is director-only — no director match fires. The film falls through to
        European Sexploitation (FR + Drama + 1960s). This is the documented fallback.
        """
        tmdb_data = {
            'director': 'Unknown French Director',
            'year': 1965,
            'countries': ['FR'],
            'genres': ['Drama', 'Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'European Sexploitation', (
            f"Unknown French 1965 Drama: expected 'European Sexploitation' fallback, "
            f"got {result!r}. "
            f"FR is not in COUNTRY_TO_WAVE (design decision), so country-wave stage skips. "
            f"FNW has no director match. Film falls to EurSex (FR + Drama + 1960s)."
        )

    def test_fnw_director_takes_priority_over_european_sexploitation(self, classifier, mock_metadata):
        """FR + FNW director + 1965 + Romance → French New Wave (not European Sexploitation)

        FNW is first in SATELLITE_ROUTING_RULES priority order. A director match fires
        before European Sexploitation is evaluated, even when country/genre also match EurSex.
        """
        tmdb_data = {
            'director': 'Louis Malle',
            'year': 1965,
            'countries': ['FR'],
            'genres': ['Drama', 'Romance']
        }
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'French New Wave', (
            f"Malle (FNW director) should take priority over European Sexploitation, "
            f"got {result!r}"
        )
