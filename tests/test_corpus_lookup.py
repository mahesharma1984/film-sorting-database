#!/usr/bin/env python3
"""
Test suite for lib/corpus.py — CorpusLookup class (Issue #38)
"""

import csv
import sys
import pytest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.corpus import CorpusLookup

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GIALLO_CORPORA_DIR = Path(__file__).parent.parent / 'data' / 'corpora'

SAMPLE_CSV_ROWS = [
    {'title': 'Deep Red', 'year': '1975', 'imdb_id': 'tt0073582',
     'director': 'Dario Argento', 'country': 'IT', 'canonical_tier': '1',
     'source': 'Koven 2006 p.45', 'notes': ''},
    {'title': 'Bay of Blood', 'year': '1971', 'imdb_id': 'tt0067125',
     'director': 'Mario Bava', 'country': 'IT', 'canonical_tier': '1',
     'source': 'Koven 2006 p.20', 'notes': ''},
    {'title': 'Short Night of Glass Dolls', 'year': '1971', 'imdb_id': 'tt0067668',
     'director': 'Aldo Lado', 'country': 'IT', 'canonical_tier': '2',
     'source': 'Lucas 2007', 'notes': ''},
    {'title': 'Spasmo', 'year': '1974', 'imdb_id': 'tt0072100',
     'director': 'Umberto Lenzi', 'country': 'IT', 'canonical_tier': '2',
     'source': 'Lucas 2007', 'notes': ''},
]


@pytest.fixture
def temp_corpora_dir():
    """Create a temporary corpora directory with a sample giallo CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        corpora_dir = Path(tmpdir)
        csv_path = corpora_dir / 'giallo.csv'
        fieldnames = ['title', 'year', 'imdb_id', 'director', 'country',
                      'canonical_tier', 'source', 'notes']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(SAMPLE_CSV_ROWS)
        yield corpora_dir


@pytest.fixture
def corpus(temp_corpora_dir):
    return CorpusLookup(temp_corpora_dir)


@pytest.fixture
def real_corpus():
    """Load real giallo corpus if data/corpora/ exists."""
    if not GIALLO_CORPORA_DIR.exists():
        pytest.skip("data/corpora/ not found")
    return CorpusLookup(GIALLO_CORPORA_DIR)


# ---------------------------------------------------------------------------
# Loading tests
# ---------------------------------------------------------------------------

class TestCorpusLoads:

    def test_corpus_loads_without_error(self, corpus):
        stats = corpus.get_stats()
        assert stats['total_entries'] == len(SAMPLE_CSV_ROWS)

    def test_corpus_categories_detected(self, corpus):
        stats = corpus.get_stats()
        assert 'Giallo' in stats['categories']

    def test_imdb_index_built(self, corpus):
        stats = corpus.get_stats()
        assert stats['imdb_index_size'] == len(SAMPLE_CSV_ROWS)

    def test_empty_corpora_dir_returns_empty_corpus(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cl = CorpusLookup(Path(tmpdir))
            assert cl.get_stats()['total_entries'] == 0

    def test_nonexistent_dir_gracefully_disabled(self):
        cl = CorpusLookup(Path('/nonexistent/path/that/does/not/exist'))
        assert cl.get_stats()['total_entries'] == 0
        assert cl.lookup('Deep Red', 1975) is None


# ---------------------------------------------------------------------------
# Title + year lookup tests
# ---------------------------------------------------------------------------

class TestTitleYearLookup:

    def test_canonical_film_found(self, corpus):
        result = corpus.lookup('Deep Red', 1975)
        assert result is not None
        assert result['category'] == 'Giallo'

    def test_canonical_tier_correct(self, corpus):
        result = corpus.lookup('Deep Red', 1975)
        assert result['canonical_tier'] == 1

    def test_source_preserved(self, corpus):
        result = corpus.lookup('Deep Red', 1975)
        assert result['source'] == 'Koven 2006 p.45'

    def test_director_preserved(self, corpus):
        result = corpus.lookup('Deep Red', 1975)
        assert result['director'] == 'Dario Argento'

    def test_tier_2_film_found(self, corpus):
        result = corpus.lookup('Short Night of Glass Dolls', 1971)
        assert result is not None
        assert result['canonical_tier'] == 2

    def test_year_mismatch_returns_none(self, corpus):
        result = corpus.lookup('Deep Red', 1980)
        assert result is None

    def test_title_not_in_corpus_returns_none(self, corpus):
        result = corpus.lookup('Rocco and His Brothers', 1960)
        assert result is None

    def test_completely_unknown_film(self, corpus):
        result = corpus.lookup('This Film Does Not Exist', 2099)
        assert result is None


# ---------------------------------------------------------------------------
# Normalization robustness
# ---------------------------------------------------------------------------

class TestNormalizedLookup:

    def test_case_insensitive_title(self, corpus):
        result = corpus.lookup('deep red', 1975)
        assert result is not None

    def test_extra_whitespace_in_title(self, corpus):
        result = corpus.lookup('  Deep Red  ', 1975)
        assert result is not None

    def test_format_signals_stripped(self, corpus):
        """Format signals in title should not break lookup (normalize_for_lookup strips them)"""
        result = corpus.lookup('Deep Red 35mm', 1975)
        assert result is not None

    def test_article_handling(self, corpus):
        """'Bay of Blood' should match regardless of article normalization"""
        result = corpus.lookup('Bay of Blood', 1971)
        assert result is not None


# ---------------------------------------------------------------------------
# IMDb ID lookup tests
# ---------------------------------------------------------------------------

class TestImdbLookup:

    def test_imdb_id_match_overrides_title(self, corpus):
        """IMDb ID match should work even with wrong title"""
        result = corpus.lookup('Wrong Title', 1975, imdb_id='tt0073582')
        assert result is not None
        assert result['category'] == 'Giallo'

    def test_imdb_id_match_overrides_year(self, corpus):
        """IMDb ID match should work even with wrong year"""
        result = corpus.lookup('Deep Red', 9999, imdb_id='tt0073582')
        assert result is not None

    def test_unknown_imdb_id_falls_through_to_title_year(self, corpus):
        """Unknown IMDb ID should fall through to title+year lookup, not block it."""
        result = corpus.lookup('Deep Red', 1975, imdb_id='tt9999999')
        assert result is not None  # title+year match succeeds

    def test_unknown_imdb_id_unknown_title_returns_none(self, corpus):
        """Unknown IMDb ID AND unknown title should return None."""
        result = corpus.lookup('Unknown Film', 2099, imdb_id='tt9999999')
        assert result is None

    def test_none_imdb_id_falls_through_to_title(self, corpus):
        result = corpus.lookup('Deep Red', 1975, imdb_id=None)
        assert result is not None


# ---------------------------------------------------------------------------
# Real corpus integration tests
# ---------------------------------------------------------------------------

class TestRealCorpus:

    def test_real_corpus_loads(self, real_corpus):
        stats = real_corpus.get_stats()
        assert stats['total_entries'] >= 10, "Real corpus should have at least 10 films"

    def test_bird_with_crystal_plumage_in_corpus(self, real_corpus):
        result = real_corpus.lookup('The Bird with the Crystal Plumage', 1970)
        assert result is not None
        assert result['category'] == 'Giallo'
        assert result['canonical_tier'] == 1

    def test_bird_via_imdb_id(self, real_corpus):
        result = real_corpus.lookup('anything', 1970, imdb_id='tt0065472')
        assert result is not None
        assert result['category'] == 'Giallo'

    def test_rocco_not_in_giallo_corpus(self, real_corpus):
        """Rocco and His Brothers (Visconti) should NOT be in the Giallo corpus"""
        result = real_corpus.lookup('Rocco and His Brothers', 1960)
        assert result is None
