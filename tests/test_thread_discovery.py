#!/usr/bin/env python3
"""Unit tests for thread discovery (Issue #12)"""

import pytest
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.rag.threads import ThreadDiscovery


@pytest.fixture
def mock_thread_index(tmp_path):
    """Create mock thread keyword index"""
    index = {
        'Giallo': {
            'keywords': [
                {'keyword': 'murder', 'count': 5, 'films': ['Film A', 'Film B']},
                {'keyword': 'mystery', 'count': 4, 'films': ['Film A']},
                {'keyword': 'psycho-killer', 'count': 3, 'films': ['Film B']},
            ],
            'tentpole_count': 5
        },
        'Pinku Eiga': {
            'keywords': [
                {'keyword': 'erotic', 'count': 5, 'films': ['Film C']},
                {'keyword': 'taboo', 'count': 3, 'films': ['Film D']},
            ],
            'tentpole_count': 4
        }
    }

    index_path = tmp_path / 'thread_keywords.json'
    with open(index_path, 'w') as f:
        json.dump(index, f)

    return index_path


def test_load_index(mock_thread_index):
    """ThreadDiscovery loads index correctly"""
    discovery = ThreadDiscovery(mock_thread_index)
    assert 'Giallo' in discovery.index
    assert 'Pinku Eiga' in discovery.index
    assert len(discovery.index) == 2


def test_load_index_missing_file():
    """ThreadDiscovery raises error if index missing"""
    with pytest.raises(FileNotFoundError) as exc_info:
        ThreadDiscovery(Path('/nonexistent/thread_keywords.json'))

    assert "Run: python scripts/build_thread_index.py" in str(exc_info.value)


def test_query_thread_exact_match(mock_thread_index):
    """Perfect overlap returns Jaccard = 1.0"""
    discovery = ThreadDiscovery(mock_thread_index)

    # Film has all 3 Giallo keywords
    film_keywords = ['murder', 'mystery', 'psycho-killer']
    result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.0)

    assert result is not None
    assert result['category'] == 'Giallo'
    assert result['jaccard_score'] == 1.0  # Perfect match
    assert result['overlap_count'] == 3
    assert set(result['shared_keywords']) == {'murder', 'mystery', 'psycho-killer'}


def test_query_thread_partial_match(mock_thread_index):
    """Partial overlap calculates Jaccard correctly"""
    discovery = ThreadDiscovery(mock_thread_index)

    # Film has 2 of 3 Giallo keywords + 1 unique
    film_keywords = ['murder', 'mystery', 'unique-keyword']
    result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.0)

    # Jaccard = |intersection| / |union|
    # intersection = {murder, mystery} = 2
    # union = {murder, mystery, psycho-killer, unique-keyword} = 4
    # Jaccard = 2/4 = 0.5
    assert result is not None
    assert result['jaccard_score'] == pytest.approx(0.5, abs=0.01)
    assert result['overlap_count'] == 2
    assert 'murder' in result['shared_keywords']
    assert 'mystery' in result['shared_keywords']


def test_query_thread_below_threshold(mock_thread_index):
    """Returns None if below min_overlap threshold"""
    discovery = ThreadDiscovery(mock_thread_index)

    film_keywords = ['murder']  # Low overlap
    result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.5)

    assert result is None


def test_query_thread_no_overlap(mock_thread_index):
    """Returns None if no keyword overlap"""
    discovery = ThreadDiscovery(mock_thread_index)

    film_keywords = ['comedy', 'romance']  # No overlap with Giallo
    result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.0)

    assert result is None


def test_query_thread_empty_keywords(mock_thread_index):
    """Returns None if film has no keywords"""
    discovery = ThreadDiscovery(mock_thread_index)

    result = discovery.query_thread('Giallo', [], min_overlap=0.0)

    assert result is None


def test_query_thread_unknown_category(mock_thread_index):
    """Returns None for unknown category"""
    discovery = ThreadDiscovery(mock_thread_index)

    result = discovery.query_thread('Unknown Category', ['murder'], min_overlap=0.0)

    assert result is None


def test_query_thread_case_insensitive(mock_thread_index):
    """Keyword matching is case-insensitive"""
    discovery = ThreadDiscovery(mock_thread_index)

    # Mixed case keywords
    film_keywords = ['MURDER', 'Mystery', 'psycho-KILLER']
    result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.0)

    assert result is not None
    assert result['jaccard_score'] == 1.0


def test_discover_threads_for_film(mock_thread_index):
    """Discover multiple threads ranked by Jaccard"""
    discovery = ThreadDiscovery(mock_thread_index)

    # Film keywords overlap with both categories
    film_keywords = ['murder', 'erotic', 'unique']
    threads = discovery.discover_threads_for_film(film_keywords, min_overlap=0.1)

    assert len(threads) > 0
    # Should be sorted by Jaccard score descending
    scores = [t['jaccard_score'] for t in threads]
    assert scores == sorted(scores, reverse=True)


def test_discover_threads_for_film_top_k(mock_thread_index):
    """Discover threads respects top_k limit"""
    discovery = ThreadDiscovery(mock_thread_index)

    # Film that matches both categories
    film_keywords = ['murder', 'erotic']
    threads = discovery.discover_threads_for_film(film_keywords, min_overlap=0.0, top_k=1)

    assert len(threads) <= 1


def test_discover_threads_for_film_no_matches(mock_thread_index):
    """Returns empty list if no threads match"""
    discovery = ThreadDiscovery(mock_thread_index)

    film_keywords = ['comedy', 'romance']
    threads = discovery.discover_threads_for_film(film_keywords, min_overlap=0.1)

    assert threads == []


def test_get_category_keywords(mock_thread_index):
    """Get top keywords for category"""
    discovery = ThreadDiscovery(mock_thread_index)

    keywords = discovery.get_category_keywords('Giallo', top_k=2)

    assert len(keywords) == 2
    assert keywords[0]['keyword'] == 'murder'
    assert keywords[0]['count'] == 5
    assert keywords[1]['keyword'] == 'mystery'
    assert keywords[1]['count'] == 4


def test_get_category_keywords_all(mock_thread_index):
    """Get all keywords if top_k exceeds available"""
    discovery = ThreadDiscovery(mock_thread_index)

    keywords = discovery.get_category_keywords('Giallo', top_k=100)

    assert len(keywords) == 3  # Only 3 keywords in mock data


def test_get_category_keywords_unknown_category(mock_thread_index):
    """Returns empty list for unknown category"""
    discovery = ThreadDiscovery(mock_thread_index)

    keywords = discovery.get_category_keywords('Unknown Category', top_k=10)

    assert keywords == []


def test_jaccard_formula_verification(mock_thread_index):
    """Verify Jaccard formula implementation"""
    discovery = ThreadDiscovery(mock_thread_index)

    # Known set sizes for manual verification
    # Giallo keywords: {murder, mystery, psycho-killer} = 3
    # Film keywords: {murder, action, thriller} = 3
    # Intersection: {murder} = 1
    # Union: {murder, mystery, psycho-killer, action, thriller} = 5
    # Expected Jaccard: 1/5 = 0.2

    film_keywords = ['murder', 'action', 'thriller']
    result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.0)

    assert result is not None
    assert result['jaccard_score'] == pytest.approx(0.2, abs=0.01)
    assert result['overlap_count'] == 1
    assert result['category_keyword_count'] == 3
    assert result['film_keyword_count'] == 3
