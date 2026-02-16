#!/usr/bin/env python3
"""Tests for Popcorn fallback classifier."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.popcorn import PopcornClassifier
from lib.parser import FilmMetadata


def test_popcorn_cast_popularity_signal():
    classifier = PopcornClassifier()
    metadata = FilmMetadata(
        filename="Rush Hour (1998).mkv",
        title="Rush Hour",
        year=1998,
        director="Brett Ratner",
    )
    api_data = {
        'countries': ['US'],
        'genres': ['Action', 'Comedy', 'Crime'],
        'cast': ['Jackie Chan', 'Chris Tucker'],
        'popularity': 18.2,
        'vote_count': 6000,
    }
    assert classifier.classify_reason(metadata, api_data) == 'popcorn_cast_popularity'


def test_popcorn_rejects_exploitation_title_keywords():
    classifier = PopcornClassifier()
    metadata = FilmMetadata(
        filename="Hollywood Chainsaw Hookers (1988).mkv",
        title="Hollywood Chainsaw Hookers",
        year=1988,
        director=None,
    )
    api_data = {
        'countries': ['US'],
        'genres': ['Horror'],
        'cast': [],
        'popularity': 2.0,
        'vote_count': 150,
    }
    assert classifier.classify_reason(metadata, api_data) is None


def test_popcorn_requires_year():
    classifier = PopcornClassifier()
    metadata = FilmMetadata(
        filename="Unknown.mkv",
        title="Unknown Film",
        year=None,
        director=None,
    )
    api_data = {
        'countries': ['US'],
        'genres': ['Comedy'],
        'cast': ['Eddie Murphy'],
        'popularity': 14.0,
        'vote_count': 2500,
    }
    assert classifier.classify_reason(metadata, api_data) is None
