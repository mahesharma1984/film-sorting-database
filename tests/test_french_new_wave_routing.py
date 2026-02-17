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
