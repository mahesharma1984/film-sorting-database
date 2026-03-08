#!/usr/bin/env python3
"""Test decade-validated director-based Satellite routing (Issue #6, Issue #20)"""

import pytest
from lib.satellite import SatelliteClassifier
from lib.parser import FilmMetadata, FilenameParser


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


def test_fukasaku_2000s_routes_to_japanese_exploitation(mock_metadata):
    """Kinji Fukasaku 2000s → Japanese Exploitation via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Fukasaku is in Japanese Exploitation directors, so his 2000 film routes via
    director identity regardless of decade. Use SORTING_DATABASE pins to override
    specific films (e.g. Battle Royale 2000 → JNW).
    """
    tmdb_data = {
        'director': 'Kinji Fukasaku',
        'year': 2000,
        'countries': ['JP'],
        'genres': ['Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Japanese Exploitation'  # Director identity overrides decade bound (Phase 2)


def test_all_six_new_directors_issue_6(mock_metadata):
    """All 6 new directors from Issue #6 route correctly within decade bounds"""
    test_cases = [
        ('Kinji Fukasaku', 1973, ['JP'], ['Crime'], 'Japanese Exploitation'),
        ('Yasuzō Masumura', 1964, ['JP'], ['Drama'], 'Pinku Eiga'),
        ('Larry Clark', 1978, ['US'], ['Drama'], 'American Exploitation'),  # Issue #20: 1978 within AE 1960s-1980s bounds; 1995 would route to Indie Cinema
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


def test_argento_2010s_routes_to_giallo(mock_metadata):
    """Dario Argento 2012 → Giallo via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Argento is a listed Giallo director; his 2012 film routes via director identity.
    Use SORTING_DATABASE pins to override specific films if needed.
    """
    tmdb_data = {
        'director': 'Dario Argento',
        'year': 2012,
        'countries': ['IT'],
        'genres': ['Horror']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'  # Director identity overrides decade bound (Phase 2)


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


def test_director_matching_case_insensitive(mock_metadata):
    """Director matching is case-insensitive whole-word matching (Issue #25 D1)

    Single-word entries (e.g. 'fukasaku') require a whole whitespace-delimited
    token match. These cases all work because 'fukasaku' is a token in every variant.
    """
    test_cases = [
        'kinji fukasaku',  # lowercase
        'KINJI FUKASAKU',  # uppercase
        'Kinji Fukasaku',  # mixed case
        'Fukasaku',        # last name only — still a whole token
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


def test_director_whole_word_prevents_false_positive(mock_metadata):
    """Issue #25 D1: single-word entries require whole-word token match

    A director whose name *contains* a listed entry as a substring (not a whole
    token) must NOT match. 'Mallette' contains 'malle' as a substring but not
    as a whitespace-delimited token, so it should not route to French New Wave.
    """
    tmdb_data = {
        'director': 'Pierre Mallette',  # contains 'malle' but 'mallette' ≠ 'malle'
        'year': 1965,
        'countries': ['FR'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'French New Wave', (
        f"'Pierre Mallette' should not match 'malle' (whole-word guard failed)"
    )


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


def test_vadim_1990s_routes_to_european_sexploitation(mock_metadata):
    """Roger Vadim 1990s → European Sexploitation via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Vadim is a listed EuroSex director; his 1995 film routes via director identity
    regardless of decade bound.
    """
    tmdb_data = {
        'director': 'Roger Vadim',
        'year': 1995,
        'countries': ['FR'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'European Sexploitation'  # Director identity overrides decade bound (Phase 2)


def test_larry_clark_1980s_routes_to_american_exploitation(mock_metadata):
    """Larry Clark 1980s → American Exploitation (within AE decade bounds)"""
    tmdb_data = {
        'director': 'Larry Clark',
        'year': 1983,
        'countries': ['US'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_larry_clark_1995_routes_to_american_exploitation(mock_metadata):
    """Larry Clark 1995 (Kids) → American Exploitation via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Clark is in AmExploit directors; his 1995 film routes via director identity.
    To classify specific Clark films as Indie Cinema (Kids, Bully, Ken Park),
    add SORTING_DATABASE pins — those fire at Stage 2 before Satellite routing.
    """
    tmdb_data = {
        'director': 'Larry Clark',
        'year': 1995,
        'countries': ['US'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'  # Director identity overrides decade bound (Phase 2)


def test_larry_clark_2000s_routes_to_american_exploitation(mock_metadata):
    """Larry Clark 2000s (Bully, Ken Park) → American Exploitation via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Clark is in AmExploit directors; director identity routes regardless of decade.
    Use SORTING_DATABASE pins for specific films that should override to Indie Cinema.
    """
    tmdb_data = {
        'director': 'Larry Clark',
        'year': 2001,
        'countries': ['US'],
        'genres': ['Drama', 'Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'  # Director identity overrides decade bound (Phase 2)


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


def test_ernest_dickerson_1980s_routes_to_blaxploitation(mock_metadata):
    """Ernest Dickerson 1985 → Blaxploitation via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Blaxploitation's 1980s decade exclusion no longer blocks director-identity routing.
    Dickerson is a listed Blaxploitation director; his 1985 film routes via director identity.
    """
    tmdb_data = {
        'director': 'Ernest Dickerson',
        'year': 1985,
        'countries': ['US'],
        'genres': ['Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Blaxploitation'  # Director identity overrides decade bound (Phase 2)


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


def test_masumura_1990s_routes_to_pinku_eiga(mock_metadata):
    """Yasuzō Masumura 1990s → Pinku Eiga via director identity (Issue #40 Phase 2)

    Phase 2 change: tradition categories check director BEFORE decade gate.
    Masumura is a listed Pinku Eiga director; his 1995 film routes via director identity.
    """
    tmdb_data = {
        'director': 'Yasuzō Masumura',
        'year': 1995,
        'countries': ['JP'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Pinku Eiga'  # Director identity overrides decade bound (Phase 2)


def test_music_film_no_longer_auto_routes(mock_metadata):
    """Issue #51: Music Films removed from SATELLITE_ROUTING_RULES.
    A film with Music/Documentary genres no longer auto-classifies to Music Films.
    It falls to unsorted_no_match (or remains in review queue for manual curation).
    SORTING_DATABASE pins to Music Films still work via explicit_lookup."""
    tmdb_data = {
        'director': 'Unknown',
        'year': 2020,
        'countries': ['US'],
        'genres': ['Music', 'Documentary']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Music Films', "Music Films should no longer auto-classify (Issue #51)"


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


# =============================================================================
# Issue #20: Parser NON_FILM_PREFIXES fix (Stage 1)
# =============================================================================

def test_interview_prefix_not_director():
    """'Interview - Rodney Hill (2014)' → director=None, not 'Interview'"""
    parser = FilenameParser()
    result = parser.parse('Interview - Rodney Hill (2014).mkv')
    assert result.director is None, \
        f"Expected director=None, got director={result.director!r}"
    # Title should be the right-side token, not the prefix
    assert result.title != 'Interview'


def test_english_version_prefix_not_director():
    """'English version - El Topo (1970)' → director=None, not 'English version'"""
    parser = FilenameParser()
    result = parser.parse('English version - El Topo (1970).mkv')
    assert result.director is None, \
        f"Expected director=None, got director={result.director!r}"


# =============================================================================
# Issue #51: Indie Cinema removed from auto-routing
# =============================================================================

def test_cn_1990s_no_longer_routes_to_indie_cinema(mock_metadata):
    """Issue #51: Farewell My Concubine (CN, 1993, Drama) → no auto-classification.
    Previously routed to Indie Cinema. Now falls to unsorted_no_match.
    SORTING_DATABASE pins still work via explicit_lookup."""
    tmdb_data = {
        'director': 'Kaige Chen',
        'year': 1993,
        'countries': ['CN'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Indie Cinema', \
        f"Indie Cinema should no longer auto-classify (Issue #51), got {result!r}"


def test_jp_2000s_no_longer_routes_to_indie_cinema(mock_metadata):
    """Issue #51: Kamikaze Girls (JP, 2004, Drama) → no auto-classification.
    Previously routed to Indie Cinema. Now falls to unsorted_no_match."""
    tmdb_data = {
        'director': 'Tetsuya Nakashima',
        'year': 2004,
        'countries': ['JP'],
        'genres': ['Drama', 'Comedy']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Indie Cinema', \
        f"Indie Cinema should no longer auto-classify (Issue #51), got {result!r}"


def test_au_1970s_no_longer_routes_to_indie_cinema(mock_metadata):
    """Issue #51: Wake in Fright (AU, 1971, Drama) → no auto-classification.
    Previously routed to Indie Cinema. Now falls to unsorted_no_match."""
    tmdb_data = {
        'director': 'Ted Kotcheff',
        'year': 1971,
        'countries': ['AU'],
        'genres': ['Drama', 'Thriller']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Indie Cinema', \
        f"Indie Cinema should no longer auto-classify (Issue #51), got {result!r}"


def test_jp_1975_still_routes_to_pinku_eiga(mock_metadata):
    """Regression (Issue #51): JP Drama 1970s still hits Pinku Eiga correctly."""
    tmdb_data = {
        'director': 'Kōji Wakamatsu',
        'year': 1975,
        'countries': ['JP'],
        'genres': ['Drama', 'Romance']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Pinku Eiga', \
        f"Regression: expected 'Pinku Eiga', got {result!r}"


# =============================================================================
# Issue #20: Brazilian Exploitation decade bounds widened (Stage 3)
# =============================================================================

def test_br_1966_routes_to_brazilian_exploitation(mock_metadata):
    """O Padre e a Moça (BR, 1966, Drama) → Brazilian Exploitation (newly in bounds)"""
    tmdb_data = {
        'director': 'Joaquim Pedro de Andrade',
        'year': 1966,
        'countries': ['BR'],
        'genres': ['Drama', 'Romance']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Brazilian Exploitation', \
        f"Expected 'Brazilian Exploitation', got {result!r}"


def test_br_1991_routes_to_brazilian_exploitation(mock_metadata):
    """Vai Trabalhar Vagabundo II (BR, 1991, Drama) → Brazilian Exploitation (newly in bounds)"""
    tmdb_data = {
        'director': 'Hugo Carvana',
        'year': 1991,
        'countries': ['BR'],
        'genres': ['Drama', 'Crime']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Brazilian Exploitation', \
        f"Expected 'Brazilian Exploitation', got {result!r}"


# =============================================================================
# Issue #25 D7: increment_count() cap warning
# =============================================================================

def test_increment_count_logs_warning_at_cap(caplog):
    """increment_count() should log a WARNING when count exceeds the category cap"""
    import logging
    classifier = SatelliteClassifier()
    cap = classifier.caps['Giallo']
    # Fill to the cap (no warning yet)
    for _ in range(cap):
        classifier.increment_count('Giallo')
    # One more — should trigger the warning
    with caplog.at_level(logging.WARNING, logger='lib.satellite'):
        classifier.increment_count('Giallo')
    assert 'Giallo' in caplog.text
    assert str(cap) in caplog.text


def test_increment_count_does_not_block_over_cap():
    """increment_count() must still increment even over cap — lookup entries are never blocked"""
    classifier = SatelliteClassifier()
    cap = classifier.caps['Giallo']
    for _ in range(cap + 5):
        classifier.increment_count('Giallo')
    assert classifier.counts['Giallo'] == cap + 5


def test_increment_count_no_warning_under_cap(caplog):
    """increment_count() must not warn when count is at or below cap"""
    import logging
    classifier = SatelliteClassifier()
    cap = classifier.caps['Giallo']
    with caplog.at_level(logging.WARNING, logger='lib.satellite'):
        for _ in range(cap):
            classifier.increment_count('Giallo')
    assert 'Giallo' not in caplog.text


# =============================================================================
# Issue #40 Phase 2: Tradition director fires before decade gate
# =============================================================================

def test_ferrara_1998_routes_to_american_exploitation(mock_metadata):
    """Abel Ferrara 1998 → American Exploitation via director identity (Issue #40 Phase 2 core case)

    The motivating example for Phase 2: Ferrara is in AmExploit directors but
    1998 > 1980s decade bound. Old behavior: decade gate blocked, result None.
    New behavior: director check fires before decade gate, returns AmExploit.
    """
    tmdb_data = {
        'director': 'Abel Ferrara',
        'year': 1998,
        'countries': ['US'],
        'genres': ['Drama', 'Thriller']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_tradition_director_fires_before_decade_gate(mock_metadata):
    """Tradition category director match fires regardless of decade (Issue #40 Phase 2)

    Generic principle test: a director listed in a tradition category (country_codes
    populated) routes correctly even when the film's decade is outside the structural
    window. Uses Ruggero Deodato 2000 (newly added Phase 1 director, Giallo).
    """
    tmdb_data = {
        'director': 'Ruggero Deodato',
        'year': 2000,
        'countries': ['IT'],
        'genres': ['Horror']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'  # Director identity fires before 1960s-1980s decade gate


def test_movement_director_still_needs_decade_match(mock_metadata):
    """Movement category director is still blocked by decade gate (Issue #40 Phase 2 unchanged)

    FNW (country_codes=[]) is a movement category — decade gate fires BEFORE director check.
    Godard 2014 should NOT route to FNW: year 2014 is outside 1950s-1970s decade bounds.
    Movement categories are intentionally unchanged by Phase 2.
    """
    tmdb_data = {
        'director': 'Jean-Luc Godard',
        'year': 2014,
        'countries': ['CH'],
        'genres': ['Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'French New Wave'  # Decade gate blocks FNW for out-of-era Godard


# =============================================================================
# Issue #40 Phase 1: New directors regression tests
# =============================================================================

def test_van_peebles_1971_routes_to_blaxploitation(mock_metadata):
    """Melvin Van Peebles 1971 → Blaxploitation (Phase 1 new director)"""
    tmdb_data = {
        'director': 'Melvin Van Peebles',
        'year': 1971,
        'countries': ['US'],
        'genres': ['Drama', 'Action']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Blaxploitation'


def test_john_ford_1940s_routes_to_classic_hollywood(mock_metadata):
    """John Ford 1940s → Classic Hollywood (Phase 1 new director)"""
    tmdb_data = {
        'director': 'John Ford',
        'year': 1946,
        'countries': ['US'],
        'genres': ['Western', 'Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Classic Hollywood'


def test_corman_1960s_routes_to_american_exploitation(mock_metadata):
    """Roger Corman 1966 → American Exploitation (Phase 1 new director)"""
    tmdb_data = {
        'director': 'Roger Corman',
        'year': 1966,
        'countries': ['US'],
        'genres': ['Horror', 'Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American Exploitation'


def test_deodato_1980_routes_to_giallo(mock_metadata):
    """Ruggero Deodato 1980 → Giallo (Phase 1 new director, within era)"""
    tmdb_data = {
        'director': 'Ruggero Deodato',
        'year': 1980,
        'countries': ['IT'],
        'genres': ['Horror', 'Thriller']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_king_hu_1979_routes_to_hk_action(mock_metadata):
    """King Hu 1979 → Hong Kong Action (Phase 1 new director)"""
    tmdb_data = {
        'director': 'King Hu',
        'year': 1979,
        'countries': ['HK'],
        'genres': ['Action', 'Drama']
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Hong Kong Action'
