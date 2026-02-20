#!/usr/bin/env python3
"""Test keyword-based Satellite routing (Issue #29)

Covers:
- Tier A: country + decade + keyword hit substitutes for genre gate
- Tier B: TMDb keyword tag alone routes French New Wave and American New Hollywood
- Boundary: text_terms do NOT trigger Tier B (only tmdb_tags do)
- Passthrough: films with no keyword signals still classify via structural routing
"""

import pytest
from lib.satellite import SatelliteClassifier
from lib.parser import FilmMetadata


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


# ---------------------------------------------------------------------------
# Tier A: country + decade + keyword hit (genre gate waived)
# ---------------------------------------------------------------------------

def test_tier_a_giallo_tmdb_tag_waives_genre(mock_metadata):
    """Italian Drama 1970s + TMDb tag 'giallo' → Giallo despite genre mismatch."""
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 1973,
        'countries': ['IT'],
        'genres': ['Drama'],           # Not Horror/Thriller/Mystery — genre gate fails
        'keywords': ['giallo'],        # TMDb tag rescues it
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_tier_a_giallo_text_term_in_overview(mock_metadata):
    """Italian film 1971, overview contains 'giallo' → Giallo via text scan."""
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 1971,
        'countries': ['IT'],
        'genres': ['Drama'],
        'keywords': [],
        'overview': 'A classic giallo mystery set in Rome.',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_tier_a_giallo_text_term_in_plot(mock_metadata):
    """Italian film 1975, OMDb plot contains 'giallo' → Giallo via text scan."""
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 1975,
        'countries': ['IT'],
        'genres': ['Drama'],
        'keywords': [],
        'overview': '',
        'tagline': '',
        'plot': 'An Italian giallo thriller with stylized violence.',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_tier_a_does_not_fire_when_country_mismatch(mock_metadata):
    """Keyword hit without country match does NOT route to Giallo."""
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 1973,
        'countries': ['FR'],           # Not IT
        'genres': ['Drama'],
        'keywords': ['giallo'],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Giallo'


def test_tier_a_does_not_fire_when_decade_mismatch(mock_metadata):
    """Keyword hit without decade match does NOT route to Giallo."""
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 2010,                  # Outside 1960s-1980s
        'countries': ['IT'],
        'genres': ['Drama'],
        'keywords': ['giallo'],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Giallo'


# ---------------------------------------------------------------------------
# Tier B: TMDb keyword tag alone for movement categories
# ---------------------------------------------------------------------------

def test_tier_b_french_new_wave_tmdb_tag_no_director(mock_metadata):
    """No director match + TMDb tag 'nouvelle vague' → French New Wave."""
    tmdb_data = {
        'director': 'Jean Renaud',     # Not in FNW directors list
        'year': 1963,
        'countries': ['FR'],
        'genres': ['Drama'],
        'keywords': ['nouvelle vague'],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'French New Wave'


def test_tier_b_american_new_hollywood_tmdb_tag_no_director(mock_metadata):
    """No director match + TMDb tag 'new hollywood' → American New Hollywood."""
    tmdb_data = {
        'director': 'John Smith',      # Not in ANH directors list
        'year': 1972,
        'countries': ['US'],
        'genres': ['Drama'],
        'keywords': ['new hollywood'],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'American New Hollywood'


def test_tier_b_text_term_does_not_route_fnw(mock_metadata):
    """Text term 'new wave' in overview does NOT trigger Tier B for French New Wave.
    Tier B is TMDb tags only — text scan terms are not high-precision enough."""
    tmdb_data = {
        'director': 'Jean Renaud',
        'year': 1963,
        'countries': ['FR'],
        'genres': ['Drama'],
        'keywords': [],                # No TMDb tags
        'overview': 'A seminal new wave film from France.',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'French New Wave'


def test_tier_b_decade_gate_still_enforced(mock_metadata):
    """Tier B does not fire outside movement decade bounds."""
    tmdb_data = {
        'director': 'Jean Renaud',
        'year': 1985,                  # Outside FNW 1950s-1970s
        'countries': ['FR'],
        'genres': ['Drama'],
        'keywords': ['nouvelle vague'],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'French New Wave'


# ---------------------------------------------------------------------------
# Passthrough: existing structural routing unaffected
# ---------------------------------------------------------------------------

def test_structural_routing_unchanged_argento(mock_metadata):
    """Dario Argento 1977 → Giallo via director match (no keyword needed)."""
    tmdb_data = {
        'director': 'Dario Argento',
        'year': 1977,
        'countries': ['IT'],
        'genres': ['Horror'],
        'keywords': [],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'Giallo'


def test_structural_routing_unchanged_truffaut(mock_metadata):
    """François Truffaut 1962 → French New Wave via director match (no keyword needed)."""
    tmdb_data = {
        'director': 'François Truffaut',
        'year': 1962,
        'countries': ['FR'],
        'genres': ['Drama'],
        'keywords': [],
        'overview': '',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result == 'French New Wave'


def test_no_keyword_no_route(mock_metadata):
    """Italian Drama 1975 with no keywords and wrong genre → no classification."""
    tmdb_data = {
        'director': 'Unknown Director',
        'year': 1975,
        'countries': ['IT'],
        'genres': ['Drama'],
        'keywords': [],
        'overview': 'A quiet domestic drama.',
        'tagline': '',
        'plot': '',
    }
    classifier = SatelliteClassifier()
    result = classifier.classify(mock_metadata, tmdb_data)
    assert result != 'Giallo'
