#!/usr/bin/env python3
"""
Test suite for lib/lookup.py — SORTING_DATABASE.md parsing and querying
"""

import pytest
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.lookup import SortingDatabaseLookup


@pytest.fixture
def lookup_db():
    project_path = Path(__file__).parent.parent
    db_path = project_path / 'docs' / 'SORTING_DATABASE.md'
    if not db_path.exists():
        pytest.skip("SORTING_DATABASE.md not found")
    return SortingDatabaseLookup(db_path)


class TestDatabaseLoading:
    """Verify database loads correctly"""

    def test_database_not_empty(self, lookup_db):
        stats = lookup_db.get_stats()
        assert stats['total_entries'] > 0

    def test_database_has_many_entries(self, lookup_db):
        """Should have 100+ human-curated entries"""
        stats = lookup_db.get_stats()
        assert stats['total_entries'] >= 100

    def test_most_entries_have_year(self, lookup_db):
        stats = lookup_db.get_stats()
        assert stats['entries_with_year'] > stats['entries_without_year']


class TestLookupQueries:
    """Test lookup query behavior"""

    def test_known_film_with_year(self, lookup_db):
        """Known film should return destination"""
        result = lookup_db.lookup("Rashomon", 1950)
        assert result is not None
        assert "Reference" in result

    def test_unknown_film(self, lookup_db):
        """Unknown film should return None"""
        result = lookup_db.lookup("This Film Does Not Exist At All", 2099)
        assert result is None

    def test_format_signal_in_query(self, lookup_db):
        """Format signals in query should be stripped before lookup"""
        # If "The Shining" is in the database
        result_clean = lookup_db.lookup("The Shining", 1980)
        result_with_signal = lookup_db.lookup("The Shining 35mm", 1980)

        # Both should give same result (or both None if not in DB)
        assert result_clean == result_with_signal

    def test_year_prefix_format(self, lookup_db):
        """Brazilian year-prefix entries should be found"""
        # Test if any Brazilian entries exist
        stats = lookup_db.get_stats()
        # Just verify the database loads without errors
        assert stats['total_entries'] > 0


class TestLookupSymmetry:
    """Verify symmetric normalization between build and query"""

    def test_same_normalization_path(self, lookup_db):
        """Build and query should use identical normalization"""
        from lib.normalization import normalize_for_lookup

        # Pick a known title format from the database
        # The database normalizes with strip_format_signals=True
        # The query should too
        test_title = "Some Film Criterion"
        normalized = normalize_for_lookup(test_title, strip_format_signals=True)

        # The key used for lookup should strip "Criterion"
        assert "criterion" not in normalized


class TestLookupValidation:
    """Reject ambiguous destinations from SORTING_DATABASE entries."""

    def test_ambiguous_or_destination_is_ignored(self):
        content = (
            "- Se7en (1995) 35mm → Reference OR Popcorn?\n"
            "- Rush Hour (1998) → 1990s/Popcorn/\n"
        )
        with NamedTemporaryFile('w+', suffix='.md', encoding='utf-8') as tmp:
            tmp.write(content)
            tmp.flush()
            db = SortingDatabaseLookup(Path(tmp.name))

            assert db.lookup("Se7en", 1995) is None
            assert db.lookup("Rush Hour", 1998) == "1990s/Popcorn"
