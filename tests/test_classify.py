#!/usr/bin/env python3
"""
Test suite for classify.py — full pipeline classification tests
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser import FilenameParser, FilmMetadata
from lib.normalization import normalize_for_lookup
from lib.constants import REFERENCE_CANON


class TestReferenceCanon:
    """Reference canon lookup via constants.py"""

    def test_citizen_kane_in_canon(self):
        key = (normalize_for_lookup("Citizen Kane"), 1941)
        assert key in REFERENCE_CANON

    def test_casablanca_in_canon(self):
        key = (normalize_for_lookup("Casablanca"), 1942)
        assert key in REFERENCE_CANON

    def test_pulp_fiction_in_canon(self):
        key = (normalize_for_lookup("Pulp Fiction"), 1994)
        assert key in REFERENCE_CANON

    def test_unknown_film_not_in_canon(self):
        key = (normalize_for_lookup("Random Unknown Film"), 2020)
        assert key not in REFERENCE_CANON

    def test_canon_size(self):
        """Reference canon should have ~50 films (some have alternate normalizations)"""
        assert len(REFERENCE_CANON) >= 48


class TestClassificationPipeline:
    """Integration tests for the full classify pipeline"""

    @pytest.fixture
    def classifier(self):
        """Create classifier with --no-tmdb for offline testing"""
        config_path = Path(__file__).parent.parent / 'config_external.yaml'
        if not config_path.exists():
            pytest.skip("config_external.yaml not found")

        from classify import FilmClassifier
        return FilmClassifier(config_path, no_tmdb=True)

    def test_kubrick_dr_strangelove(self, classifier):
        """Dr. Strangelove should classify to Core/Stanley Kubrick via explicit lookup"""
        meta = classifier.parser.parse("Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Stanley Kubrick" in result.destination
        assert result.reason == "explicit_lookup"

    def test_kubrick_the_shining(self, classifier):
        """The Shining should classify to Core/Stanley Kubrick via explicit lookup"""
        meta = classifier.parser.parse("The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Stanley Kubrick" in result.destination

    def test_kubrick_2001(self, classifier):
        """2001: A Space Odyssey should parse year 1968 and classify correctly"""
        meta = classifier.parser.parse("2001 - A Space Odyssey (1968) - 4K.mkv")
        assert meta.year == 1968

        result = classifier.classify(meta)
        assert result.tier == "Core"
        assert "1960s" in result.destination

    def test_reference_canon_film(self, classifier):
        """Psycho (1960) should be Reference via canon check"""
        meta = classifier.parser.parse("Psycho (1960).mkv")
        result = classifier.classify(meta)

        # Could be explicit_lookup OR reference_canon depending on SORTING_DATABASE
        assert result.tier in ("Reference", "Core")

    def test_unsorted_unknown_film(self, classifier):
        """Unknown film should go to Unsorted"""
        meta = FilmMetadata(
            filename="Totally Unknown Film (2023).mkv",
            title="Totally Unknown Film",
            year=2023
        )
        result = classifier.classify(meta)

        assert result.tier == "Unsorted"
        assert "unsorted" in result.reason

    def test_unsorted_no_year(self, classifier):
        """Film with no year should go to Unsorted with no_year reason"""
        meta = FilmMetadata(
            filename="Mystery Film.mkv",
            title="Mystery Film",
            year=None
        )
        result = classifier.classify(meta)

        assert result.tier == "Unsorted"
        assert "no_year" in result.reason

    def test_format_signals_not_classification(self, classifier):
        """Format signals should NOT trigger tier classification"""
        meta = FilmMetadata(
            filename="Unknown Film (1985) Criterion 35mm.mkv",
            title="Unknown Film",
            year=1985,
            format_signals=["criterion", "35mm"]
        )
        result = classifier.classify(meta)

        # Should be Unsorted since film is unknown, NOT Popcorn
        assert result.tier == "Unsorted"


class TestUserTagRecovery:
    """User tag parsing"""

    @pytest.fixture
    def classifier(self):
        config_path = Path(__file__).parent.parent / 'config_external.yaml'
        if not config_path.exists():
            pytest.skip("config_external.yaml not found")

        from classify import FilmClassifier
        return FilmClassifier(config_path, no_tmdb=True)

    def test_user_tag_parsing(self, classifier):
        """User tag should be parsed into tier and decade"""
        parsed = classifier._parse_user_tag("Popcorn-1970s")
        assert parsed['tier'] == "Popcorn"
        assert parsed['decade'] == "1970s"

    def test_user_tag_with_director(self, classifier):
        parsed = classifier._parse_user_tag("Core-1960s-Jacques Demy")
        assert parsed['tier'] == "Core"
        assert parsed['decade'] == "1960s"
        assert "Jacques" in parsed.get('extra', '')

    # Issue #23 Bug 1: bare [Satellite-DECADE] tag produces malformed 'Satellite/' destination
    def test_bare_satellite_tag_falls_through(self, classifier):
        """[Satellite-1970s] without a category should NOT route to 'Satellite/' (malformed path)"""
        meta = FilmMetadata(
            filename="Unknown Obscure Film (1975) [Satellite-1970s].mkv",
            title="Unknown Obscure Film",
            year=1975,
            user_tag="Satellite-1970s",
        )
        result = classifier.classify(meta)
        assert result.destination != 'Satellite/'
        assert result.reason != 'user_tag_recovery'

    def test_satellite_tag_with_category_routes_correctly(self, classifier):
        """[Satellite-1970s-Giallo] should route to Satellite/Giallo/1970s/"""
        meta = FilmMetadata(
            filename="Unknown Italian Film (1975) [Satellite-1970s-Giallo].mkv",
            title="Unknown Italian Film",
            year=1975,
            user_tag="Satellite-1970s-Giallo",
        )
        result = classifier.classify(meta)
        assert result.destination == 'Satellite/Giallo/1970s/'
        assert result.reason == 'user_tag_recovery'
        assert result.tier == 'Satellite'

    # Issue #23 Bug 2: [Core-DECADE-DIRECTOR] bypasses Core whitelist check
    def test_core_tag_valid_director_routes_to_core(self, classifier):
        """[Core-1960s-Director] with director in whitelist should route to Core/"""
        meta = FilmMetadata(
            filename="Unknown Film A (1968) [Core-1960s-Akira Kurosawa].mkv",
            title="Unknown Film A",
            year=1968,
            director=None,
            user_tag="Core-1960s-Akira Kurosawa",
        )
        # Mock the Core whitelist check — director present in whitelist
        classifier.core_db.is_core_director = MagicMock(return_value=True)
        result = classifier.classify(meta)
        assert result.tier == 'Core'
        assert 'Akira Kurosawa' in result.destination
        assert result.reason == 'user_tag_recovery'

    def test_core_tag_unknown_director_falls_through(self, classifier):
        """[Core-1960s-Unknown Person] with director NOT in whitelist should fall through"""
        meta = FilmMetadata(
            filename="Unknown Film B (1968) [Core-1960s-Unknown Person].mkv",
            title="Unknown Film B",
            year=1968,
            director=None,
            user_tag="Core-1960s-Unknown Person",
        )
        # Mock the Core whitelist check — director NOT in whitelist
        classifier.core_db.is_core_director = MagicMock(return_value=False)
        result = classifier.classify(meta)
        assert result.tier != 'Core'
        assert result.reason != 'user_tag_recovery'

    def test_core_tag_typo_director_falls_through(self, classifier):
        """[Core-1960s-Godart] (typo for Godard) should fall through since not in whitelist"""
        meta = FilmMetadata(
            filename="Unknown Film C (1965) [Core-1960s-Godart].mkv",
            title="Unknown Film C",
            year=1965,
            director=None,
            user_tag="Core-1960s-Godart",
        )
        result = classifier.classify(meta)
        # 'Godart' is not a real Core director — should fall through
        assert result.tier != 'Core'

    # Regression: Reference and Popcorn tags should continue working unchanged
    def test_reference_tag_routes_to_reference(self, classifier):
        """[Reference-1960s] tag should route to Reference/1960s/"""
        meta = FilmMetadata(
            filename="Unknown Film D (1965) [Reference-1960s].mkv",
            title="Unknown Film D",
            year=1965,
            user_tag="Reference-1960s",
        )
        result = classifier.classify(meta)
        assert result.tier == 'Reference'
        assert result.decade == '1960s'
        assert result.reason == 'user_tag_recovery'

    def test_popcorn_tag_routes_to_popcorn(self, classifier):
        """[Popcorn-1980s] tag should route to Popcorn/1980s/"""
        meta = FilmMetadata(
            filename="Unknown Film E (1985) [Popcorn-1980s].mkv",
            title="Unknown Film E",
            year=1985,
            user_tag="Popcorn-1980s",
        )
        result = classifier.classify(meta)
        assert result.tier == 'Popcorn'
        assert result.decade == '1980s'
        assert result.reason == 'user_tag_recovery'


class TestDestinationPathParsing:
    """Destination path parsing from SORTING_DATABASE"""

    @pytest.fixture
    def classifier(self):
        config_path = Path(__file__).parent.parent / 'config_external.yaml'
        if not config_path.exists():
            pytest.skip("config_external.yaml not found")

        from classify import FilmClassifier
        return FilmClassifier(config_path, no_tmdb=True)

    def test_decade_first_core(self, classifier):
        parsed = classifier._parse_destination_path("1960s/Core/Jean-Luc Godard/")
        assert parsed['tier'] == "Core"
        assert parsed['decade'] == "1960s"
        assert parsed['subdirectory'] == "Jean-Luc Godard"

    def test_decade_first_satellite(self, classifier):
        parsed = classifier._parse_destination_path("1970s/Satellite/Brazilian Exploitation/")
        assert parsed['tier'] == "Satellite"
        assert parsed['decade'] == "1970s"
        assert parsed['subdirectory'] == "Brazilian Exploitation"

    def test_decade_first_reference(self, classifier):
        parsed = classifier._parse_destination_path("1960s/Reference/")
        assert parsed['tier'] == "Reference"
        assert parsed['decade'] == "1960s"

    def test_decade_first_popcorn(self, classifier):
        parsed = classifier._parse_destination_path("1980s/Popcorn/")
        assert parsed['tier'] == "Popcorn"
        assert parsed['decade'] == "1980s"
