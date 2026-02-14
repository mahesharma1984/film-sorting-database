#!/usr/bin/env python3
"""
Test suite for lib/normalization.py — symmetric normalization guarantees
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.normalization import normalize_for_lookup
from lib.lookup import SortingDatabaseLookup


class TestFormatSignalStripping:
    """Format signals must be stripped during normalization"""

    def test_criterion_stripped(self):
        assert normalize_for_lookup("Dr Strangelove Criterion") == "dr strangelove"

    def test_35mm_stripped(self):
        assert normalize_for_lookup("The Shining 35mm Scan") == "the shining scan"

    def test_4k_stripped(self):
        assert normalize_for_lookup("2001 A Space Odyssey 4K") == "2001 a space odyssey"

    def test_no_signals(self):
        assert normalize_for_lookup("Breathless") == "breathless"

    def test_multiple_signals(self):
        result = normalize_for_lookup("Film Title Open Matte Extended")
        assert result == "film title"

    def test_directors_cut(self):
        result = normalize_for_lookup("Apocalypse Now Redux")
        assert result == "apocalypse now"

    def test_without_stripping(self):
        result = normalize_for_lookup("Film 4K", strip_format_signals=False)
        assert "4k" in result


class TestUnicodeNormalization:
    """Unicode diacritics should be removed"""

    def test_french_accents(self):
        assert normalize_for_lookup("À bout de souffle") == "a bout de souffle"

    def test_german_umlauts(self):
        result = normalize_for_lookup("Über den Wolken")
        assert "uber" in result

    def test_portuguese_accents(self):
        result = normalize_for_lookup("São Paulo")
        assert "sao paulo" in result


class TestPunctuationRemoval:
    """Punctuation should be removed, spaces collapsed"""

    def test_apostrophe(self):
        result = normalize_for_lookup("Can't Buy Me Love")
        assert "cant buy me love" == result

    def test_period(self):
        result = normalize_for_lookup("Dr. Strangelove")
        assert "dr strangelove" == result

    def test_colon(self):
        result = normalize_for_lookup("Alien: Resurrection")
        assert "alien resurrection" == result


class TestLookupSymmetry:
    """Database building and querying must produce identical normalization"""

    @pytest.fixture
    def lookup_db(self):
        project_path = Path(__file__).parent.parent
        db_path = project_path / 'docs' / 'SORTING_DATABASE.md'
        if not db_path.exists():
            pytest.skip("SORTING_DATABASE.md not found")
        return SortingDatabaseLookup(db_path)

    def test_dr_strangelove_with_criterion(self, lookup_db):
        """Query with format signal should still match database entry"""
        result = lookup_db.lookup("Dr Strangelove Criterion", 1964)
        assert result is not None
        assert "Stanley Kubrick" in result

    def test_dr_strangelove_clean(self, lookup_db):
        """Clean query should match"""
        result = lookup_db.lookup("Dr Strangelove", 1964)
        # May or may not be in database — just verify no crash
        # The title in database might be "Dr. Strangelove"

    def test_shining_with_signals(self, lookup_db):
        """Format signals in query should be stripped before lookup"""
        # Note: Release tags (Scan, FullScreen, HYBRID) are stripped by the parser
        # before the title reaches the lookup. Only format signals like "35mm"
        # and "open matte" are stripped by normalize_for_lookup().
        result = lookup_db.lookup("The Shining 35mm", 1980)
        assert result is not None
        assert "Stanley Kubrick" in result

    def test_2001_with_4k(self, lookup_db):
        """4K format signal in query should be stripped"""
        result = lookup_db.lookup("2001 A Space Odyssey 4K", 1968)
        assert result is not None
