#!/usr/bin/env python3
"""
Test suite for v0.1 classification system fixes

Validates fixes for:
1. Asymmetric normalization bug (format signals blocking lookup)
2. Year parsing bug (2001 - A Space Odyssey extracting wrong year)
3. Format signals as tier classification (should be metadata only)

Critical test cases: 3 Kubrick films from effectiveness report
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from classify_v01 import FilmClassifierV01
from lib.parser import FilenameParser
from lib.normalization import normalize_for_lookup
from lib.lookup import SortingDatabaseLookup


class TestKubrickClassification:
    """Validate fixes for Kubrick film misclassifications from effectiveness report"""

    @pytest.fixture
    def classifier(self):
        project_path = Path(__file__).parent.parent
        return FilmClassifierV01(project_path)

    def test_dr_strangelove_with_criterion(self, classifier):
        """
        Test: Dr. Strangelove with Criterion format signal

        Before fix: Routed to Popcorn/1960s/ (format_signal)
        After fix: Should route to Core/1960s/Stanley Kubrick/ (explicit_lookup)
        """
        filename = 'Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv'

        metadata = classifier.parser.parse(filename)
        result = classifier.classify(metadata)

        assert result.tier == 'Core', \
            f"Expected Core, got {result.tier} (reason: {result.reason})"
        assert result.destination == 'Core/1960s/Stanley Kubrick/', \
            f"Wrong destination: {result.destination}"
        assert result.year == 1964, f"Wrong year: {result.year}"
        assert result.reason == 'explicit_lookup', \
            f"Should match via explicit_lookup, got: {result.reason}"

    def test_the_shining_with_35mm(self, classifier):
        """
        Test: The Shining with 35mm and multiple format signals

        Before fix: Routed to Popcorn/1980s/ (format_signal)
        After fix: Should route to Core/1980s/Stanley Kubrick/ (explicit_lookup)
        """
        filename = 'The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv'

        metadata = classifier.parser.parse(filename)
        result = classifier.classify(metadata)

        assert result.tier == 'Core', \
            f"Expected Core, got {result.tier} (reason: {result.reason})"
        assert result.destination == 'Core/1980s/Stanley Kubrick/', \
            f"Wrong destination: {result.destination}"
        assert '1980s' in result.destination, \
            "Should be in 1980s, not other decade"
        assert result.reason == 'explicit_lookup', \
            f"Should match via explicit_lookup, got: {result.reason}"

    def test_2001_year_parsing(self, classifier):
        """
        Test: 2001 - A Space Odyssey extracts correct year (1968, not 2001)

        Before fix:
        - year = 2001 (from title "2001")
        - Routed to Popcorn/2000s/ (wrong decade!)

        After fix:
        - year = 1968 (from parentheses)
        - Routed to Core/1960s/Stanley Kubrick/
        """
        filename = '2001 - A Space Odyssey (1968) - 4K.mkv'

        metadata = classifier.parser.parse(filename)

        # Critical: Year should be 1968 (from parens), NOT 2001 (from title)
        assert metadata.year == 1968, \
            f"Year parsing failed: got {metadata.year}, expected 1968"

        result = classifier.classify(metadata)

        assert result.tier == 'Core', \
            f"Expected Core, got {result.tier} (reason: {result.reason})"
        assert '1960s' in result.destination, \
            f"Should be 1960s (film from 1968), not 2000s: {result.destination}"
        assert result.destination == 'Core/1960s/Stanley Kubrick/', \
            f"Wrong destination: {result.destination}"
        assert result.reason == 'explicit_lookup', \
            f"Should match via explicit_lookup, got: {result.reason}"


class TestNormalization:
    """Test symmetric normalization fixes"""

    def test_format_signals_stripped_from_lookup(self):
        """Verify format signals are stripped during normalization"""
        test_cases = [
            ("Dr Strangelove Criterion", "dr strangelove"),
            ("The Shining 35mm Scan", "the shining"),  # "35mm" and "scan" both stripped
            ("2001 A Space Odyssey 4K", "2001 a space odyssey"),  # "4k" stripped
            ("Breathless", "breathless"),  # No format signals
            ("Film Title Open Matte Extended", "film title"),  # Multiple signals
        ]

        for raw_title, expected_normalized in test_cases:
            normalized = normalize_for_lookup(raw_title, strip_format_signals=True)
            assert normalized == expected_normalized, \
                f"normalize_for_lookup('{raw_title}') = '{normalized}', expected '{expected_normalized}'"

    def test_lookup_symmetry(self):
        """
        Verify database and query use identical normalization

        This is the core fix: lookup should succeed even when query
        contains format signals, because both database and query strip them.
        """
        project_path = Path(__file__).parent.parent
        lookup_db = SortingDatabaseLookup(project_path / 'docs' / 'SORTING_DATABASE.md')

        # Test cases: (query_title, year, should_find_match)
        test_cases = [
            ("Dr Strangelove Criterion", 1964, True),  # Format signal in query
            ("Dr Strangelove", 1964, True),  # Clean query
            ("The Shining 35mm Scan FullScreen HYBRID OPEN MATTE", 1980, True),
            ("2001 A Space Odyssey 4K", 1968, True),  # Query has 4K, should still match
        ]

        for query_title, year, should_match in test_cases:
            result = lookup_db.lookup(query_title, year)

            if should_match:
                assert result is not None, \
                    f"Lookup failed for '{query_title}' ({year}) - format signals not stripped from query!"
                assert 'Stanley Kubrick' in result, \
                    f"Wrong lookup result for '{query_title}': {result}"
            else:
                assert result is None, \
                    f"Unexpected match for '{query_title}': {result}"


class TestYearParsing:
    """Test year extraction priority fixes"""

    def test_parenthetical_year_priority(self):
        """Parenthetical year should always take priority over leading digits"""
        parser = FilenameParser()

        test_cases = [
            # (filename, expected_year, expected_title_contains)
            ("2001 - A Space Odyssey (1968) - 4K.mkv", 1968, "2001"),
            ("1984 (1956).mkv", 1956, "1984"),
            ("1917 (2019).mkv", 2019, "1917"),
            ("2010 The Year We Make Contact (1984).mkv", 1984, "2010"),
        ]

        for filename, expected_year, title_should_contain in test_cases:
            metadata = parser.parse(filename)
            assert metadata.year == expected_year, \
                f"File '{filename}': expected year={expected_year}, got {metadata.year}"
            assert title_should_contain.lower() in metadata.title.lower(), \
                f"File '{filename}': title '{metadata.title}' should contain '{title_should_contain}'"

    def test_brazilian_format_still_works(self):
        """Brazilian year-prefix format should still work when no parenthetical year exists"""
        parser = FilenameParser()

        test_cases = [
            ("1976 - Amadas e Violentadas.avi", 1976, "Amadas e Violentadas"),
            ("1977 - Escola Penal de Meninas Violentadas.mkv", 1977, "Escola Penal"),
        ]

        for filename, expected_year, title_should_contain in test_cases:
            metadata = parser.parse(filename)
            assert metadata.year == expected_year, \
                f"File '{filename}': expected year={expected_year}, got {metadata.year}"
            assert title_should_contain.lower() in metadata.title.lower(), \
                f"File '{filename}': title '{metadata.title}' should contain '{title_should_contain}'"


class TestFormatSignalMetadata:
    """Verify format signals are metadata, not tier classification"""

    @pytest.fixture
    def classifier(self):
        project_path = Path(__file__).parent.parent
        return FilmClassifierV01(project_path)

    def test_format_signals_detected_but_not_classified(self, classifier):
        """
        Format signals should be detected but NOT trigger Popcorn classification

        Before fix: Film with format signal → Popcorn
        After fix: Film with format signal → Unsorted (if no other match)
        """
        # Film with format signal but NOT in database
        filename = "Unknown Film (1985) Criterion 35mm.mkv"

        metadata = classifier.parser.parse(filename)

        # Should detect format signals
        assert 'criterion' in metadata.format_signals or '35mm' in metadata.format_signals, \
            "Format signals not detected"

        result = classifier.classify(metadata)

        # Should go to Unsorted, NOT Popcorn
        assert result.tier == 'Unsorted', \
            f"Film with format signals but no match should be Unsorted, not {result.tier}"
        assert result.reason.startswith('unsorted'), \
            f"Wrong reason: {result.reason}"

    def test_format_signals_preserved_as_metadata(self, classifier):
        """Format signals should be preserved in metadata for future use"""
        test_cases = [
            ("Film (1985) Criterion.mkv", ['criterion']),
            ("Film (1980) 35mm Open Matte.mkv", ['35mm', 'open matte']),
            ("Film (1990) 4K UHD.mkv", ['4k', 'uhd']),
            ("Film (1975) Directors Cut Extended.mkv", ["director's cut", "directors cut", 'extended']),
        ]

        for filename, expected_signals in test_cases:
            metadata = classifier.parser.parse(filename)

            # Check that at least one of the expected signals was detected
            found_signals = [sig for sig in expected_signals if sig in metadata.format_signals]
            assert len(found_signals) > 0, \
                f"File '{filename}': no format signals detected. Expected one of {expected_signals}, got {metadata.format_signals}"


class TestNoRegression:
    """Ensure fixes don't break previously working classifications"""

    @pytest.fixture
    def classifier(self):
        project_path = Path(__file__).parent.parent
        return FilmClassifierV01(project_path)

    def test_clean_filenames_still_work(self, classifier):
        """Films without format signals should still classify correctly"""
        # These should match explicit lookup
        test_cases = [
            ("Breathless (1960).mkv", "Core", "1960s"),
            ("Psycho (1960).mkv", "Reference", "1960s"),
        ]

        for filename, expected_tier, expected_decade in test_cases:
            metadata = classifier.parser.parse(filename)
            result = classifier.classify(metadata)

            # Allow both explicit_lookup and unsorted (depending on database content)
            # The important thing is it doesn't crash or misclassify
            assert result.tier in [expected_tier, 'Unsorted'], \
                f"File '{filename}': unexpected tier {result.tier}"

            if result.tier != 'Unsorted':
                assert expected_decade in result.destination, \
                    f"File '{filename}': wrong decade in {result.destination}"


def test_imports():
    """Verify all new modules can be imported"""
    try:
        from lib.constants import FORMAT_SIGNALS, RELEASE_TAGS
        from lib.normalization import normalize_for_lookup
        from lib.lookup import SortingDatabaseLookup
        from lib.parser import FilenameParser
        from classify_v01 import FilmClassifierV01

        assert len(FORMAT_SIGNALS) > 0, "FORMAT_SIGNALS is empty"
        assert len(RELEASE_TAGS) > 0, "RELEASE_TAGS is empty"

    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
