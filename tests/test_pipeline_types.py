"""Tests for lib/pipeline_types.py — L3 enforcement layer (Issue #54)"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.pipeline_types import EnrichedFilm, Resolution


class TestEnrichedFilm:
    """EnrichedFilm dataclass — typed ENRICH stage output."""

    def test_required_fields_present(self):
        film = EnrichedFilm(
            director='Dario Argento',
            countries=['IT'],
            genres=['Horror'],
            keywords=['giallo'],
            tmdb_id=12345,
            tmdb_title='Suspiria',
            readiness='R3',
        )
        assert film.director == 'Dario Argento'
        assert film.countries == ['IT']
        assert film.genres == ['Horror']
        assert film.keywords == ['giallo']
        assert film.tmdb_id == 12345
        assert film.tmdb_title == 'Suspiria'
        assert film.readiness == 'R3'

    def test_defaults(self):
        film = EnrichedFilm(
            director=None,
            countries=[],
            genres=[],
            keywords=[],
            tmdb_id=None,
            tmdb_title=None,
            readiness='R1',
        )
        assert film.sources == {}
        assert film.raw is None

    def test_sources_dict_independent(self):
        """Each instance gets its own sources dict."""
        a = EnrichedFilm(director=None, countries=[], genres=[], keywords=[],
                         tmdb_id=None, tmdb_title=None, readiness='R1')
        b = EnrichedFilm(director=None, countries=[], genres=[], keywords=[],
                         tmdb_id=None, tmdb_title=None, readiness='R1')
        a.sources['director'] = 'omdb'
        assert b.sources == {}

    def test_raw_dict_preserved(self):
        raw = {'director': 'Argento', 'year': 1977, 'countries': ['IT']}
        film = EnrichedFilm(
            director='Dario Argento',
            countries=['IT'],
            genres=['Horror'],
            keywords=[],
            tmdb_id=None,
            tmdb_title=None,
            readiness='R3',
            raw=raw,
        )
        assert film.raw['year'] == 1977
        assert film.raw['director'] == 'Argento'

    def test_none_director(self):
        """R1/R2 films may have no director."""
        film = EnrichedFilm(
            director=None,
            countries=['FR'],
            genres=['Drama'],
            keywords=[],
            tmdb_id=None,
            tmdb_title=None,
            readiness='R2',
        )
        assert film.director is None
        assert film.readiness == 'R2'


class TestResolution:
    """Resolution dataclass — typed output of any classifier resolver."""

    def test_required_fields(self):
        res = Resolution(
            tier='Satellite',
            decade='1970s',
            subdirectory='Giallo',
            destination='Satellite/Giallo/1970s/',
            confidence=0.85,
            reason='both_agree',
            source_name='two_signal',
        )
        assert res.tier == 'Satellite'
        assert res.decade == '1970s'
        assert res.subdirectory == 'Giallo'
        assert res.destination == 'Satellite/Giallo/1970s/'
        assert res.confidence == 0.85
        assert res.reason == 'both_agree'
        assert res.source_name == 'two_signal'

    def test_explanation_defaults_empty(self):
        res = Resolution(
            tier='Reference',
            decade='1960s',
            subdirectory=None,
            destination='Reference/1960s/',
            confidence=1.0,
            reason='reference_canon',
            source_name='explicit_lookup',
        )
        assert res.explanation == ''

    def test_explicit_explanation(self):
        res = Resolution(
            tier='Unsorted',
            decade=None,
            subdirectory=None,
            destination='Unsorted/',
            confidence=0.0,
            reason='unsorted_no_match',
            source_name='unsorted',
            explanation='no signal matched',
        )
        assert res.explanation == 'no signal matched'

    def test_core_resolution(self):
        res = Resolution(
            tier='Core',
            decade='1960s',
            subdirectory='Jean-Luc Godard',
            destination='Core/1960s/Jean-Luc Godard/',
            confidence=1.0,
            reason='director_signal',
            source_name='two_signal',
            explanation='Core director whitelist match',
        )
        assert res.tier == 'Core'
        assert res.subdirectory == 'Jean-Luc Godard'

    def test_none_subdirectory_allowed(self):
        """Reference and Popcorn tiers have no subdirectory."""
        res = Resolution(
            tier='Popcorn',
            decade='2010s',
            subdirectory=None,
            destination='Popcorn/2010s/',
            confidence=0.65,
            reason='popcorn_popularity',
            source_name='two_signal',
        )
        assert res.subdirectory is None
