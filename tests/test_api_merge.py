#!/usr/bin/env python3
"""Test suite for parallel API query and merge logic"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from classify import FilmClassifier
from lib.parser import FilmMetadata
from lib.tmdb import TMDbClient


@pytest.fixture
def classifier():
    """Create classifier without API clients for testing"""
    with patch('classify.load_config') as mock_config:
        # Mock config to return minimal required config
        mock_config.return_value = {
            'project_path': '/tmp/test',
            'library_path': '/tmp/library'
        }

        with patch('classify.FilmClassifier._setup_components'):
            classifier = FilmClassifier(
                config_path=Path('/tmp/test/config.yaml'),
                no_tmdb=False
            )
            classifier.tmdb = None
            classifier.omdb = None
            classifier.stats = defaultdict(int)
            return classifier


class TestTitleCleaning:
    """Test _clean_title_for_api() extraction"""

    def test_removes_user_tags(self, classifier):
        """User tag brackets [...] should be removed"""
        title = "Breathless [Popcorn-1960s]"
        clean = classifier._clean_title_for_api(title)
        assert clean == "Breathless"
        assert "[" not in clean
        assert "]" not in clean

    def test_removes_format_signals(self, classifier):
        """Format signals like Criterion, 4K should be removed"""
        title = "Citizen Kane Criterion 4K"
        clean = classifier._clean_title_for_api(title)
        assert "Criterion" not in clean
        assert "4K" not in clean

    def test_removes_empty_parens(self, classifier):
        """Empty parentheses () should be removed"""
        title = "Film Title ()"
        clean = classifier._clean_title_for_api(title)
        assert "()" not in clean

    def test_preserves_punctuation(self, classifier):
        """Should preserve punctuation for proper title matching"""
        title = "Dr. Strangelove: Or How I Learned to Stop Worrying"
        clean = classifier._clean_title_for_api(title)
        assert "Dr." in clean
        assert ":" in clean

    @pytest.mark.parametrize("title", ["Shadow", "The Conformist", "Shahid"])
    def test_release_tags_do_not_truncate_real_words(self, classifier, title):
        """Short release tags (hd/nf) should not match inside normal words."""
        clean = classifier._clean_title_for_api(title)
        assert clean == title

    def test_release_tags_still_strip_when_tokenized(self, classifier):
        """Tokenized release tags should still be removed."""
        title = "Shadow 1080p NF"
        clean = classifier._clean_title_for_api(title)
        assert clean == "Shadow"


class TestParallelQuery:
    """Test _query_apis() parallel execution"""

    def test_queries_both_apis(self, classifier):
        """Both TMDb and OMDb should be queried (not fallback)"""
        # Mock both API clients
        classifier.tmdb = MagicMock()
        classifier.omdb = MagicMock()

        classifier.tmdb.search_film.return_value = {'director': 'TMDb Director'}
        classifier.omdb.search_film.return_value = {'director': 'OMDb Director'}

        metadata = FilmMetadata(
            filename="test.mkv",
            title="Test Film",
            year=1975
        )

        results = classifier._query_apis(metadata)

        # Both should be called
        classifier.tmdb.search_film.assert_called_once()
        classifier.omdb.search_film.assert_called_once()
        assert results['tmdb'] == {'director': 'TMDb Director'}
        assert results['omdb'] == {'director': 'OMDb Director'}

    def test_soft_gate_no_year(self, classifier):
        """Missing year should return empty results, not crash"""
        classifier.tmdb = MagicMock()
        classifier.omdb = MagicMock()

        metadata = FilmMetadata(
            filename="test.mkv",
            title="Test Film",
            year=None
        )

        results = classifier._query_apis(metadata)

        assert results == {'tmdb': None, 'omdb': None}
        # APIs should not be called when year is missing
        classifier.tmdb.search_film.assert_not_called()
        classifier.omdb.search_film.assert_not_called()

    def test_statistics_tracking(self, classifier):
        """Should track tmdb_success, omdb_success, both_apis_success"""
        classifier.tmdb = MagicMock()
        classifier.omdb = MagicMock()

        classifier.tmdb.search_film.return_value = {'director': 'Test'}
        classifier.omdb.search_film.return_value = {'director': 'Test'}

        metadata = FilmMetadata(
            filename="test.mkv",
            title="Test Film",
            year=1975
        )

        classifier._query_apis(metadata)

        assert classifier.stats['tmdb_success'] == 1
        assert classifier.stats['omdb_success'] == 1
        assert classifier.stats['both_apis_success'] == 1


class TestSmartMerge:
    """Test _merge_api_results() priority rules"""

    def test_director_omdb_wins(self, classifier):
        """OMDb director should take priority over TMDb"""
        tmdb_data = {'director': 'TMDb Director'}
        omdb_data = {'director': 'OMDb Director'}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['director'] == 'OMDb Director'
        assert metadata.director == 'OMDb Director'
        assert classifier.stats['director_from_omdb'] == 1

    def test_director_tmdb_fallback(self, classifier):
        """TMDb director used if OMDb missing"""
        tmdb_data = {'director': 'TMDb Director'}
        omdb_data = {}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['director'] == 'TMDb Director'
        assert metadata.director == 'TMDb Director'
        assert classifier.stats['director_from_tmdb'] == 1

    def test_country_omdb_wins(self, classifier):
        """OMDb country should take priority over TMDb"""
        tmdb_data = {'countries': ['US']}
        omdb_data = {'countries': ['IT']}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['countries'] == ['IT']
        assert metadata.country == 'IT'
        assert classifier.stats['country_from_omdb'] == 1

    def test_country_tmdb_fallback(self, classifier):
        """TMDb country used if OMDb missing (critical case)"""
        tmdb_data = {'countries': ['IT']}
        omdb_data = {}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['countries'] == ['IT']
        assert metadata.country == 'IT'
        assert classifier.stats['country_from_tmdb'] == 1

    def test_genres_tmdb_wins(self, classifier):
        """TMDb genres should take priority over OMDb"""
        tmdb_data = {'genres': ['Horror', 'Thriller']}
        omdb_data = {'genres': ['Horror']}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['genres'] == ['Horror', 'Thriller']
        assert classifier.stats['genres_from_tmdb'] == 1

    def test_year_filename_wins(self, classifier):
        """Filename year should take priority over API years"""
        tmdb_data = {'year': 1976}
        omdb_data = {'year': 1977}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['year'] == 1975  # Filename wins

    def test_respects_existing_metadata_director(self, classifier):
        """Should not overwrite metadata.director if already set"""
        tmdb_data = {'director': 'TMDb Director'}
        omdb_data = {'director': 'OMDb Director'}

        metadata = FilmMetadata(
            filename="test.mkv",
            title="Test",
            year=1975,
            director="Filename Director"  # Already set
        )

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['director'] == 'OMDb Director'  # Merge uses OMDb
        assert metadata.director == "Filename Director"  # But metadata unchanged

    def test_respects_existing_metadata_country(self, classifier):
        """Should not overwrite metadata.country if already set"""
        tmdb_data = {'countries': ['US']}
        omdb_data = {'countries': ['IT']}

        metadata = FilmMetadata(
            filename="test.mkv",
            title="Test",
            year=1975,
            country="BR"  # Already set
        )

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['countries'] == ['IT']  # Merge uses OMDb
        assert metadata.country == "BR"  # But metadata unchanged

    def test_both_apis_none(self, classifier):
        """Should return None if both APIs fail"""
        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(None, None, metadata)

        assert merged is None

    def test_title_tmdb_wins(self, classifier):
        """TMDb title should take priority (canonical names)"""
        tmdb_data = {'title': 'The Seventh Seal'}
        omdb_data = {'title': 'Det sjunde inseglet'}

        metadata = FilmMetadata(filename="test.mkv", title="Seventh Seal", year=1957)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['title'] == 'The Seventh Seal'

    def test_original_language_from_tmdb_only(self, classifier):
        """Only TMDb provides original_language"""
        tmdb_data = {'original_language': 'sv'}
        omdb_data = {}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1957)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['original_language'] == 'sv'

    def test_empty_countries_handling(self, classifier):
        """Should handle empty country lists gracefully"""
        tmdb_data = {'countries': []}
        omdb_data = {'countries': []}

        metadata = FilmMetadata(filename="test.mkv", title="Test", year=1975)

        merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

        assert merged['countries'] == []
        assert metadata.country is None


class TestIntegration:
    """Integration tests for end-to-end workflow"""

    def test_query_and_merge_integration(self, classifier):
        """Test full workflow from query to merge"""
        classifier.tmdb = MagicMock()
        classifier.omdb = MagicMock()

        # Mock: TMDb has genres, OMDb has better director/country
        classifier.tmdb.search_film.return_value = {
            'director': 'Dario Argento',
            'genres': ['Horror', 'Mystery'],
            'countries': []  # Empty!
        }
        classifier.omdb.search_film.return_value = {
            'director': 'Dario Argento',
            'countries': ['IT'],
            'genres': ['Horror']
        }

        metadata = FilmMetadata(
            filename="Suspiria (1977).mkv",
            title="Suspiria",
            year=1977
        )

        # Query both APIs
        api_results = classifier._query_apis(metadata)

        # Merge results
        merged = classifier._merge_api_results(
            api_results['tmdb'],
            api_results['omdb'],
            metadata
        )

        # Verify merge
        assert merged['director'] == 'Dario Argento'
        assert merged['countries'] == ['IT']  # OMDb provided this
        assert merged['genres'] == ['Horror', 'Mystery']  # TMDb provided this

        # Verify metadata was enriched
        assert metadata.director == 'Dario Argento'
        assert metadata.country == 'IT'

        # Verify statistics
        assert classifier.stats['tmdb_success'] == 1
        assert classifier.stats['omdb_success'] == 1
        assert classifier.stats['both_apis_success'] == 1
        assert classifier.stats['country_from_omdb'] == 1
        assert classifier.stats['genres_from_tmdb'] == 1


@pytest.fixture
def tmdb_client(tmp_path):
    """TMDbClient with a dummy API key and temp cache"""
    return TMDbClient(api_key='test_key', cache_path=tmp_path / 'tmdb_cache.json')


class TestTMDbValidation:
    """Tests for TMDbClient._validate_result() — Issue #21"""

    def test_exact_match_accepted(self, tmdb_client):
        candidate = {'title': 'Suspiria', 'release_date': '1977-02-01'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is True

    def test_year_adjacent_accepted(self, tmdb_client):
        """Year delta of 1 should pass (e.g. different release regions)"""
        candidate = {'title': 'Suspiria', 'release_date': '1978-01-01'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is True

    def test_year_delta_two_accepted(self, tmdb_client):
        """Year delta of exactly 2 should pass"""
        candidate = {'title': 'Suspiria', 'release_date': '1979-01-01'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is True

    def test_year_too_far_rejected(self, tmdb_client):
        """A remake 41 years later must not match the original"""
        candidate = {'title': 'Suspiria', 'release_date': '2018-10-26'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is False

    def test_title_mismatch_rejected(self, tmdb_client):
        """Completely different title should be rejected regardless of year"""
        candidate = {'title': 'Alien', 'release_date': '1977-01-01'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is False

    def test_no_query_year_skips_year_check(self, tmdb_client):
        """When query year is None, year check is skipped — title match alone passes"""
        candidate = {'title': 'Suspiria', 'release_date': '2018-10-26'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', None) is True

    def test_no_release_date_skips_year_check(self, tmdb_client):
        """When candidate has no release_date, year check is skipped"""
        candidate = {'title': 'Suspiria'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is True

    def test_original_title_fallback(self, tmdb_client):
        """Should use original_title when title is absent"""
        candidate = {'original_title': 'Profondo Rosso', 'release_date': '1975-03-07'}
        assert tmdb_client._validate_result(candidate, 'Profondo Rosso', 1975) is True

    def test_empty_candidate_title_rejected(self, tmdb_client):
        """Candidate with no title fields should be rejected"""
        candidate = {'release_date': '1977-01-01'}
        assert tmdb_client._validate_result(candidate, 'Suspiria', 1977) is False

    def test_similar_title_above_threshold_accepted(self, tmdb_client):
        """A title with minor punctuation difference should pass (similarity > 0.6)"""
        # 'The Apartment' vs 'Apartment, The' — both refer to same film
        candidate = {'title': 'The Apartment', 'release_date': '1960-06-15'}
        assert tmdb_client._validate_result(candidate, 'Apartment The', 1960) is True

    def test_first_result_mismatch_second_match(self, tmdb_client):
        """_query_api should skip mismatched results and return the first valid one"""
        search_response = {
            'results': [
                {'id': 1, 'title': 'Suspiria', 'release_date': '2018-10-26'},  # Wrong year
                {'id': 2, 'title': 'Suspiria', 'release_date': '1977-02-01'},  # Correct
                {'id': 3, 'title': 'Suspiria Uncut', 'release_date': '1977-05-01'},
            ]
        }
        details_response = {
            'title': 'Suspiria',
            'release_date': '1977-02-01',
            'credits': {'crew': [{'job': 'Director', 'name': 'Dario Argento'}], 'cast': []},
            'genres': [{'name': 'Horror'}],
            'production_countries': [{'iso_3166_1': 'IT'}],
            'origin_country': [],
            'keywords': {'keywords': []},
        }

        with patch('requests.get') as mock_get:
            # First call: search; second call: details
            search_mock = MagicMock()
            search_mock.json.return_value = search_response
            search_mock.raise_for_status = MagicMock()

            details_mock = MagicMock()
            details_mock.json.return_value = details_response
            details_mock.raise_for_status = MagicMock()

            mock_get.side_effect = [search_mock, details_mock]

            result = tmdb_client._query_api('Suspiria', 1977)

        assert result is not None
        assert result['director'] == 'Dario Argento'
        assert result['tmdb_id'] == 2  # Second result (first valid one)

    def test_all_top3_mismatch_returns_none(self, tmdb_client):
        """If all top 3 results fail validation, return None"""
        search_response = {
            'results': [
                {'id': 1, 'title': 'Suspiria', 'release_date': '2018-10-26'},
                {'id': 2, 'title': 'Suspiria 2', 'release_date': '2019-01-01'},
                {'id': 3, 'title': 'Completely Different Film', 'release_date': '1977-01-01'},
            ]
        }

        with patch('requests.get') as mock_get:
            search_mock = MagicMock()
            search_mock.json.return_value = search_response
            search_mock.raise_for_status = MagicMock()
            mock_get.return_value = search_mock

            result = tmdb_client._query_api('Suspiria', 1977)

        assert result is None


class TestOMDbCountryMapping:
    """Tests for OMDbClient._map_countries_to_codes() — Issue #25 D2"""

    @pytest.fixture
    def omdb_client(self, tmp_path):
        from lib.omdb import OMDbClient
        return OMDbClient('dummy_key', tmp_path / 'omdb_cache.json')

    def test_known_country_maps_correctly(self, omdb_client):
        assert omdb_client._map_countries_to_codes(['West Germany']) == ['DE']

    def test_east_germany_maps_to_de(self, omdb_client):
        assert omdb_client._map_countries_to_codes(['East Germany']) == ['DE']

    def test_federal_republic_maps_to_de(self, omdb_client):
        assert omdb_client._map_countries_to_codes(['Federal Republic of Germany']) == ['DE']

    def test_soviet_union_maps_to_su(self, omdb_client):
        assert omdb_client._map_countries_to_codes(['Soviet Union']) == ['SU']

    def test_unknown_country_returns_empty(self, omdb_client):
        """Unknown country must NOT produce a corrupt 2-letter truncation"""
        result = omdb_client._map_countries_to_codes(['Ruritania'])
        assert result == []

    def test_unknown_country_does_not_append_truncation(self, omdb_client):
        """Confirm no 'RU' (truncation of 'Ruritania') is added"""
        result = omdb_client._map_countries_to_codes(['Ruritania'])
        assert 'RU' not in result

    def test_mixed_known_unknown_preserves_known(self, omdb_client):
        """Known country kept, unknown dropped — not corrupted"""
        result = omdb_client._map_countries_to_codes(['Italy', 'Ruritania'])
        assert result == ['IT']

    def test_multiple_known_countries(self, omdb_client):
        result = omdb_client._map_countries_to_codes(['France', 'Italy'])
        assert result == ['FR', 'IT']
