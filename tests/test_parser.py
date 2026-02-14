#!/usr/bin/env python3
"""
Test suite for lib/parser.py — filename parsing edge cases
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser import FilenameParser, FilmMetadata


@pytest.fixture
def parser():
    return FilenameParser()


class TestParenthicalYearPriority:
    """Parenthetical year (Year) must take priority over leading digits"""

    def test_2001_space_odyssey(self, parser):
        meta = parser.parse("2001 - A Space Odyssey (1968) - 4K.mkv")
        assert meta.year == 1968
        assert "2001" in meta.title

    def test_1984_film(self, parser):
        meta = parser.parse("1984 (1956).mkv")
        assert meta.year == 1956

    def test_1917_film(self, parser):
        meta = parser.parse("1917 (2019).mkv")
        assert meta.year == 2019

    def test_2010_contact(self, parser):
        meta = parser.parse("2010 The Year We Make Contact (1984).mkv")
        assert meta.year == 1984


class TestBrazilianYearPrefix:
    """Brazilian format: Year - Title"""

    def test_basic_brazilian(self, parser):
        meta = parser.parse("1976 - Amadas e Violentadas.avi")
        assert meta.year == 1976
        assert "Amadas" in meta.title

    def test_brazilian_with_long_title(self, parser):
        meta = parser.parse("1977 - Escola Penal de Meninas Violentadas.mkv")
        assert meta.year == 1977
        assert "Escola Penal" in meta.title


class TestDirectorYearExplicit:
    """(Director, Year) pattern"""

    def test_director_comma_year(self, parser):
        meta = parser.parse("A Bay of Blood (Mario Bava, 1971).mkv")
        assert meta.year == 1971
        assert meta.director == "Mario Bava"
        assert "Bay of Blood" in meta.title

    def test_director_comma_year_with_article(self, parser):
        meta = parser.parse("The Bird with the Crystal Plumage (Dario Argento, 1970).mkv")
        assert meta.year == 1970
        assert meta.director == "Dario Argento"


class TestDirectorDashTitle:
    """Director - Title (Year) pattern"""

    def test_director_dash_title(self, parser):
        meta = parser.parse("Jean-Luc Godard - Breathless (1960).mkv")
        assert meta.year == 1960
        assert meta.director == "Jean-Luc Godard"
        assert "Breathless" in meta.title

    def test_title_year_dash_resolution_no_director(self, parser):
        """Bug 1: 'Casablanca (1942) - 4K' should NOT extract director"""
        meta = parser.parse("Casablanca (1942) - 4K.mkv")
        assert meta.year == 1942
        assert meta.director is None
        assert "Casablanca" in meta.title

    def test_subtitle_not_director(self, parser):
        """Bug 2: 'Cinema Paradiso - Theatrical Cut (1988)' should NOT extract director"""
        meta = parser.parse("Cinema Paradiso - Theatrical Cut (1988).mkv")
        assert meta.year == 1988
        assert meta.director is None
        assert "Cinema Paradiso" in meta.title


class TestFormatSignalDetection:
    """Format signals should be detected as metadata"""

    def test_criterion(self, parser):
        meta = parser.parse("Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv")
        assert "criterion" in meta.format_signals

    def test_35mm(self, parser):
        meta = parser.parse("The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv")
        assert "35mm" in meta.format_signals
        # Note: "open matte" won't match "open.matte" (dot separator)
        # This is expected behavior — format signals match substring on raw filename

    def test_open_matte_with_spaces(self, parser):
        meta = parser.parse("Film (1980) 35mm Open Matte.mkv")
        assert "35mm" in meta.format_signals
        assert "open matte" in meta.format_signals

    def test_4k_uhd(self, parser):
        meta = parser.parse("Film (1990) 4K UHD.mkv")
        assert "4k" in meta.format_signals
        assert "uhd" in meta.format_signals

    def test_directors_cut(self, parser):
        meta = parser.parse("Film (1975) Directors Cut Extended.mkv")
        assert any(s in meta.format_signals for s in ["director's cut", "directors cut"])
        assert "extended" in meta.format_signals


class TestLanguageDetection:
    """Language and country detection from filename"""

    def test_portuguese(self, parser):
        meta = parser.parse("1976 - Amadas e Violentadas Dublado.avi")
        assert meta.language == "pt"
        assert meta.country == "BR"

    def test_italian(self, parser):
        meta = parser.parse("Film Title (1972) Italian.mkv")
        assert meta.language == "it"
        assert meta.country == "IT"

    def test_french(self, parser):
        meta = parser.parse("Film Title (1965) French.mkv")
        assert meta.language == "fr"
        assert meta.country == "FR"

    def test_japanese(self, parser):
        meta = parser.parse("Film Title (1971) Japanese.mkv")
        assert meta.language == "ja"
        assert meta.country == "JP"

    def test_no_language(self, parser):
        meta = parser.parse("Film Title (1980).mkv")
        assert meta.language is None
        assert meta.country is None


class TestUserTagExtraction:
    """User classification tags like [Popcorn-1970s]"""

    def test_popcorn_tag(self, parser):
        meta = parser.parse("Film Title (1975) [Popcorn-1970s].mkv")
        assert meta.user_tag == "Popcorn-1970s"

    def test_core_tag(self, parser):
        meta = parser.parse("Breathless (1960) [Core-1960s-Jean-Luc Godard].mkv")
        assert meta.user_tag == "Core-1960s-Jean-Luc Godard"

    def test_no_tag(self, parser):
        meta = parser.parse("Film Title (1975).mkv")
        assert meta.user_tag is None

    def test_non_classification_bracket(self, parser):
        """Brackets without classification prefix should NOT be user tags"""
        meta = parser.parse("Film Title [1080p] (1975).mkv")
        assert meta.user_tag is None


class TestEdgeCases:
    """Edge cases and tricky filenames"""

    def test_scene_release_dots(self, parser):
        meta = parser.parse("The.Matrix.1999.1080p.BluRay.x264.mkv")
        assert meta.year == 1999
        assert "Matrix" in meta.title

    def test_no_year(self, parser):
        meta = parser.parse("Unknown Film Title.mkv")
        assert meta.year is None
        assert meta.title is not None

    def test_bracket_year(self, parser):
        meta = parser.parse("Film Title [1969].mkv")
        assert meta.year == 1969

    def test_resolution_not_year(self, parser):
        """1080 and 2160 should not be mistaken for years"""
        meta = parser.parse("Film Title 1080p BluRay.mkv")
        assert meta.year is None or meta.year != 1080

    def test_empty_extension(self, parser):
        meta = parser.parse("Film Title (1985)")
        assert meta.year == 1985
