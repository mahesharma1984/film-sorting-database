"""Test Core director priority over Satellite routing (Issue #14)

This test suite validates that Core directors route to Core regardless of:
- Which decade section they appear in the whitelist
- Whether their film's country/decade matches a Satellite category
- Whether Satellite routing would otherwise catch the film

Key bug fix: Jacques Demy (1960s whitelist) routing to Core for 1970s films
"""
import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.core_directors import CoreDirectorDatabase
from lib.parser import FilenameParser, FilmMetadata
from classify import FilmClassifier


class TestCoreDirectorPriority:
    """Validate Core directors route to Core regardless of decade"""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance"""
        config_path = Path(__file__).parent.parent / 'config_external.yaml'
        if not config_path.exists():
            pytest.skip("config_external.yaml not found")
        return FilmClassifier(config_path, no_tmdb=True)

    # =========================================================================
    # TEST GROUP 1: Jacques Demy (1960s whitelist, 1970s work)
    # =========================================================================

    def test_demy_1960s_routes_to_core(self, classifier):
        """Demy 1964 film → Core/1960s/Jacques Demy"""
        meta = classifier.parser.parse("The.Umbrellas.of.Cherbourg.1964.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Jacques Demy" in result.destination
        assert "1960s" in result.destination

    def test_demy_1970s_routes_to_core_not_satellite(self, classifier):
        """Demy 1970 film → Core/1970s/Jacques Demy (NOT Satellite/European Sexploitation)

        This is the PRIMARY test for Issue #14. Before the fix, this film
        would route to Satellite/European Sexploitation/1970s because:
        - Country: FR + Decade: 1970s matched European Sexploitation
        - Demy is only in 1960s whitelist section
        - Core check failed due to decade-gating
        """
        meta = classifier.parser.parse("Donkey.Skin.1970.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core", f"Expected Core, got {result.tier} ({result.reason})"
        assert "Jacques Demy" in result.destination, f"Expected Demy folder, got {result.destination}"
        assert "1970s" in result.destination, f"Expected 1970s folder, got {result.destination}"
        assert "Satellite" not in result.destination
        assert "Sexploitation" not in result.destination
        assert result.reason == "core_director"

    # =========================================================================
    # TEST GROUP 2: Multi-decade directors (Kubrick spanning 1960s-1990s)
    # =========================================================================

    def test_kubrick_1960s(self, classifier):
        """Kubrick 1968 → Core/1960s/Stanley Kubrick"""
        meta = classifier.parser.parse("2001.A.Space.Odyssey.1968.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Stanley Kubrick" in result.destination
        assert "1960s" in result.destination

    def test_kubrick_1980s(self, classifier):
        """Kubrick 1980 → Core/1980s/Stanley Kubrick

        Validates that multi-decade directors route to correct decade folder
        """
        meta = classifier.parser.parse("The.Shining.1980.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Stanley Kubrick" in result.destination
        assert "1980s" in result.destination

    def test_kubrick_1999(self, classifier):
        """Kubrick 1999 → Core/1990s/Stanley Kubrick"""
        meta = classifier.parser.parse("Eyes.Wide.Shut.1999.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Stanley Kubrick" in result.destination
        assert "1990s" in result.destination

    # =========================================================================
    # TEST GROUP 3: Core priority over Satellite country routing
    # =========================================================================

    def test_godard_not_routed_to_european_sexploitation(self, classifier):
        """Godard French 1960s → Core (NOT European Sexploitation)

        Tests that Core check happens BEFORE Satellite country routing.
        A French 1960s film would normally match European Sexploitation,
        but Godard is Core so it should never reach Satellite routing.
        """
        meta = classifier.parser.parse("Breathless.1960.French.mkv")
        meta.country = "FR"  # Simulate country detection
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Godard" in result.destination
        assert "Sexploitation" not in result.destination
        assert result.reason == "core_director"

    def test_varda_not_routed_to_french_new_wave(self, classifier):
        """Varda French 1960s → Core (NOT Satellite/French New Wave)

        Even though French New Wave category exists, Core directors
        take priority.
        """
        meta = classifier.parser.parse("Cleo.from.5.to.7.1962.mkv")
        meta.country = "FR"
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Varda" in result.destination or "Agnès Varda" in result.destination
        assert "French New Wave" not in result.destination

    # =========================================================================
    # TEST GROUP 4: Decade folder calculation
    # =========================================================================

    def test_godard_1960s_folder(self, classifier):
        """Godard 1967 → Core/1960s/Jean-Luc Godard"""
        meta = classifier.parser.parse("Weekend.1967.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "1960s" in result.destination

    def test_godard_1980s_folder(self, classifier):
        """Godard 1985 → Core/1980s/Jean-Luc Godard

        Validates decade folder is based on film year, not whitelist section
        """
        meta = classifier.parser.parse("Hail.Mary.1985.mkv")
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "1980s" in result.destination

    # =========================================================================
    # TEST GROUP 5: Director name normalization
    # =========================================================================

    def test_core_director_case_insensitive(self, classifier):
        """Core director check should be case-insensitive"""
        meta = FilmMetadata(
            filename="test.mkv",
            title="Test Film",
            year=1970,
            director="JACQUES DEMY"  # All caps
        )
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Jacques Demy" in result.destination

    def test_core_director_extra_spaces(self, classifier):
        """Core director check should handle extra spaces"""
        meta = FilmMetadata(
            filename="test.mkv",
            title="Test Film",
            year=1970,
            director="  Jacques  Demy  "  # Extra spaces
        )
        result = classifier.classify(meta)

        assert result.tier == "Core"
        assert "Jacques Demy" in result.destination
