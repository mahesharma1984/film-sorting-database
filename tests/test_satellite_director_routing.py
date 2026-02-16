#!/usr/bin/env python3
"""Test decade-validated director-based Satellite routing (Issue #6)"""

import pytest
from lib.satellite import SatelliteClassifier
from lib.parser import FilmMetadata


# Mock metadata for testing
@pytest.fixture
def mock_metadata():
    return FilmMetadata(
        filename='test.mkv',
        title='Test Film',
        year=1975,
        director=None,
        language=None,
        country=None,
        user_tag=None
    )


def test_fukasaku_1970s_routes_to_japanese_exploitation(mock_metadata):
    """Kinji Fukasaku 1970s → Japanese Exploitation"""
    tmdb_data = {
        'director': 'Kinji Fukasaku',
        'year': 1973,
        'countries': ['JP'],
        'genres': ['Crime', 'Action']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Japanese Exploitation'


def test_fukasaku_2000s_not_routed(mock_metadata):
    """Kinji Fukasaku 2000s → None (outside decade bounds)"""
    tmdb_data = {
        'director': 'Kinji Fukasaku',
        'year': 2000,
        'countries': ['JP'],
        'genres': ['Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result is None  # Outside 1970s-1980s


def test_all_six_new_directors_issue_6(mock_metadata):
    """All 6 new directors from Issue #6 route correctly"""
    test_cases = [
        ('Kinji Fukasaku', 1973, ['JP'], ['Crime'], 'Japanese Exploitation'),
        ('Yasuzō Masumura', 1964, ['JP'], ['Drama'], 'Pinku Eiga'),
        ('Larry Clark', 1995, ['US'], ['Drama'], 'American Exploitation'),
        ('Lam Nai-Choi', 1978, ['HK'], ['Action'], 'Hong Kong Action'),
        ('Ernest R. Dickerson', 1992, ['US'], ['Crime'], 'Blaxploitation'),
        ('Roger Vadim', 1968, ['FR'], ['Drama'], 'European Sexploitation'),
    ]

    for director, year, countries, genres, expected_category in test_cases:
        tmdb_data = {
            'director': director,
            'year': year,
            'countries': countries,
            'genres': genres
        }
        classifier = SatelliteClassifier()
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == expected_category, \
            f"{director} ({year}) → {result}, expected {expected_category}"


def test_existing_director_argento_still_works(mock_metadata):
    """Dario Argento 1977 → Giallo (regression test)"""
    tmdb_data = {
        'director': 'Dario Argento',
        'year': 1977,
        'countries': ['IT'],
        'genres': ['Horror']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_argento_2010s_not_routed(mock_metadata):
    """Dario Argento 2012 → None (outside Giallo decades)"""
    tmdb_data = {
        'director': 'Dario Argento',
        'year': 2012,
        'countries': ['IT'],
        'genres': ['Horror']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result is None  # Outside 1960s-1980s


def test_decade_validation_prevents_misclassification(mock_metadata):
    """Decade validation prevents routing films outside valid eras"""
    # Test: 1950s Japanese film with Crime genre should NOT route
    tmdb_data = {
        'director': 'Unknown',
        'year': 1955,
        'countries': ['JP'],
        'genres': ['Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result is None  # Before Pinku Eiga/Japanese Exploitation eras


def test_director_match_overrides_country_genre(mock_metadata):
    """Director match alone is sufficient (highest confidence)"""
    # Fukasaku film WITHOUT country data should still route
    tmdb_data = {
        'director': 'Kinji Fukasaku',
        'year': 1975,
        'countries': [],  # No country data
        'genres': []  # No genre data
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Japanese Exploitation'  # Director alone sufficient


def test_substring_matching_case_insensitive(mock_metadata):
    """Director matching is case-insensitive substring"""
    test_cases = [
        'kinji fukasaku',  # lowercase
        'KINJI FUKASAKU',  # uppercase
        'Kinji Fukasaku',  # mixed case
        'Fukasaku',  # substring (last name only)
    ]

    for director_name in test_cases:
        tmdb_data = {
            'director': director_name,
            'year': 1975,
            'countries': ['JP'],
            'genres': ['Action']
        }
        classifier = SatelliteClassifier()
        result = classifier.classify(mock_metadata, tmdb_data)
        assert result == 'Japanese Exploitation', \
            f"Failed to match director: {director_name}"


def test_bava_1960s_routes_to_giallo(mock_metadata):
    """Mario Bava 1960s → Giallo (existing director regression test)"""
    tmdb_data = {
        'director': 'Mario Bava',
        'year': 1964,
        'countries': ['IT'],
        'genres': ['Horror']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_russ_meyer_1970s_routes_to_american_exploitation(mock_metadata):
    """Russ Meyer 1970s → American Exploitation (existing director regression test)"""
    tmdb_data = {
        'director': 'Russ Meyer',
        'year': 1975,
        'countries': ['US'],
        'genres': ['Comedy']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_john_woo_1980s_routes_to_hk_action(mock_metadata):
    """John Woo 1980s → Hong Kong Action (existing director regression test)"""
    tmdb_data = {
        'director': 'John Woo',
        'year': 1986,
        'countries': ['HK'],
        'genres': ['Action']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Hong Kong Action'


def test_vadim_1960s_routes_to_european_sexploitation(mock_metadata):
    """Roger Vadim 1960s → European Sexploitation (new director Issue #6)"""
    tmdb_data = {
        'director': 'Roger Vadim',
        'year': 1968,
        'countries': ['FR'],
        'genres': ['Drama', 'Romance']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'European Sexploitation'


def test_vadim_1990s_not_routed(mock_metadata):
    """Roger Vadim 1990s → None (outside European Sexploitation decades)"""
    tmdb_data = {
        'director': 'Roger Vadim',
        'year': 1995,
        'countries': ['FR'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result is None  # Outside 1960s-1980s


def test_larry_clark_1995_routes_to_american_exploitation(mock_metadata):
    """Larry Clark 1995 (Kids) → American Exploitation"""
    tmdb_data = {
        'director': 'Larry Clark',
        'year': 1995,
        'countries': ['US'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_larry_clark_2000s_routes_to_american_exploitation(mock_metadata):
    """Larry Clark 2000s (Bully, Ken Park) → American Exploitation"""
    tmdb_data = {
        'director': 'Larry Clark',
        'year': 2001,
        'countries': ['US'],
        'genres': ['Drama', 'Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_ernest_dickerson_1992_routes_to_blaxploitation(mock_metadata):
    """Ernest R. Dickerson 1992 (Juice) → Blaxploitation"""
    tmdb_data = {
        'director': 'Ernest R. Dickerson',
        'year': 1992,
        'countries': ['US'],
        'genres': ['Crime', 'Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Blaxploitation'


def test_ernest_dickerson_1980s_not_routed(mock_metadata):
    """Ernest Dickerson 1980s with no keyword fallback should not route."""
    tmdb_data = {
        'director': 'Ernest Dickerson',
        'year': 1985,
        'countries': ['US'],
        'genres': ['Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result is None


def test_lam_nai_choi_1978_routes_to_hk_action(mock_metadata):
    """Lam Nai-Choi 1978 → Hong Kong Action"""
    tmdb_data = {
        'director': 'Lam Nai-Choi',
        'year': 1978,
        'countries': ['HK'],
        'genres': ['Action', 'Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Hong Kong Action'


def test_masumura_1964_routes_to_pinku_eiga(mock_metadata):
    """Yasuzō Masumura 1964 → Pinku Eiga"""
    tmdb_data = {
        'director': 'Yasuzō Masumura',
        'year': 1964,
        'countries': ['JP'],
        'genres': ['Drama', 'Romance']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Pinku Eiga'


def test_masumura_1990s_not_routed(mock_metadata):
    """Yasuzō Masumura 1990s → None (outside Pinku Eiga decades)"""
    tmdb_data = {
        'director': 'Yasuzō Masumura',
        'year': 1995,
        'countries': ['JP'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result is None  # Outside 1960s-1980s


def test_music_film_no_decade_restriction(mock_metadata):
    """Music Films have no decade restriction"""
    tmdb_data = {
        'director': 'Unknown',
        'year': 2020,
        'countries': ['US'],
        'genres': ['Music', 'Documentary']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Music Films'  # No decade bounds for Music Films


def test_country_genre_match_still_works(mock_metadata):
    """Country + genre match still works (regression test)"""
    # Brazilian film 1970s with Drama genre → Brazilian Exploitation
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 1975,
        'countries': ['BR'],
        'genres': ['Drama', 'Romance']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Brazilian Exploitation'


def test_rush_hour_not_blaxploitation_false_positive():
    """US action-comedy should not be auto-routed to blaxploitation."""
    metadata = FilmMetadata(
        filename='Rush Hour (1998).mkv',
        title='Rush Hour',
        year=1998,
        director='Brett Ratner',
        language=None,
        country='US',
        user_tag=None
    )
    tmdb_data = {
        'title': 'Rush Hour',
        'director': 'Brett Ratner',
        'year': 1998,
        'countries': ['US'],
        'genres': ['Action', 'Comedy', 'Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(metadata, tmdb_data)
    assert result is None


def test_house_party_not_american_exploitation_false_positive():
    """US studio comedy should not be auto-routed to american exploitation."""
    metadata = FilmMetadata(
        filename='House Party (1990).mkv',
        title='House Party',
        year=1990,
        director='Reginald Hudlin',
        language=None,
        country='US',
        user_tag=None
    )
    tmdb_data = {
        'title': 'House Party',
        'director': 'Reginald Hudlin',
        'year': 1990,
        'countries': ['US'],
        'genres': ['Comedy']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(metadata, tmdb_data)
    assert result is None


def test_chainsaw_hookers_keyword_routes_to_american_exploitation():
    """Keyword-gated exploitation fallback should still route obvious cases."""
    metadata = FilmMetadata(
        filename='Hollywood Chainsaw Hookers (1988).mkv',
        title='Hollywood Chainsaw Hookers',
        year=1988,
        director='Unknown',
        language=None,
        country='US',
        user_tag=None
    )
    tmdb_data = {
        'title': 'Hollywood Chainsaw Hookers',
        'director': 'Unknown',
        'year': 1988,
        'countries': ['US'],
        'genres': ['Horror']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_no_tmdb_data_returns_none(mock_metadata):
    """No TMDb data → None"""
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, None)
    assert result is None
