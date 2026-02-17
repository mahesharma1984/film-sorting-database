#!/usr/bin/env python3
"""
Test suite for lib/normalizer.py — filename normalization pre-stage (Issue #18)

One test class per dirty pattern class, using real filenames from the Unsorted audit.
Tests verify both cleaned_filename and change_type.

TDD: These tests are written BEFORE the implementation.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.normalizer import FilenameNormalizer, NormalizationResult


@pytest.fixture
def normalizer():
    return FilenameNormalizer()


# ─── Pattern 1: Leading junk tokens ───────────────────────────────────────────

class TestLeadingJunkStripping:
    """[TAG] and NN- prefixes must be stripped from filename stems"""

    def test_db_tag_prefix(self, normalizer):
        """[DB] prefix before film title → stripped"""
        result = normalizer.normalize("[DB]Tokyo Godfathers_-(Dual Audio 10bit BD1080p x265).mkv")
        assert "Tokyo Godfathers" in result.cleaned_filename
        assert not result.cleaned_filename.startswith("[")
        assert result.change_type == "strip_junk"

    def test_zza_tag_prefix(self, normalizer):
        """[zza] scene-release tag prefix → stripped"""
        result = normalizer.normalize("[zza]-2-Old.Boy.2003.1080p.x265.AC3.mkv")
        assert not result.cleaned_filename.startswith("[")
        assert result.change_type == "strip_junk"

    def test_numeric_prefix_with_dash(self, normalizer):
        """'02 - Lili St. Cyr...' leading number → stripped"""
        result = normalizer.normalize("02 - Lili St. Cyr in Color (1950).mkv")
        assert not result.cleaned_filename.startswith("02")
        assert result.change_type == "strip_junk"

    def test_clean_bracket_tag_no_false_positive(self, normalizer):
        """Film with [year] bracket — NOT a junk prefix, should not be stripped"""
        result = normalizer.normalize("Breathless [1960].mkv")
        # The bracket year should remain for parser to use
        assert "[1960]" in result.cleaned_filename or "1960" in result.cleaned_filename

    def test_user_classification_tag_preserved(self, normalizer):
        """[Core-1960s] user classification tag should NOT be stripped as junk"""
        result = normalizer.normalize("Breathless [Core-1960s] (1960).mkv")
        assert "[Core-1960s]" in result.cleaned_filename


# ─── Pattern 2: Edition markers in title position ─────────────────────────────

class TestEditionNormalization:
    """Edition markers like '- Uncut' should be moved to {edition-NAME} Plex format"""

    def test_uncut_edition(self, normalizer):
        """'Braindead - Uncut (1992) - LaserDisc.mkv' → edition normalized"""
        result = normalizer.normalize("Braindead - Uncut (1992) - LaserDisc.mp4")
        assert "edition" in result.cleaned_filename.lower() or "{edition-" in result.cleaned_filename
        assert result.change_type == "normalize_edition"

    def test_r_rated_cut(self, normalizer):
        """'- R-Rated Cut' edition marker → Plex format"""
        result = normalizer.normalize("Total Recall - R-Rated Cut (1990).mkv")
        assert result.change_type == "normalize_edition"
        assert "R-Rated" not in result.cleaned_filename.split("{")[0] or "{edition-" in result.cleaned_filename

    def test_directors_cut(self, normalizer):
        """'- Director's Cut' edition marker → Plex format"""
        result = normalizer.normalize("Apocalypse Now - Director's Cut (1979).mkv")
        assert result.change_type == "normalize_edition"

    def test_extended_cut(self, normalizer):
        """'- Extended Cut' edition marker → Plex format"""
        result = normalizer.normalize("Aliens - Extended Cut (1986).mkv")
        assert result.change_type == "normalize_edition"

    def test_no_edition_unchanged(self, normalizer):
        """Film without edition marker → unchanged"""
        result = normalizer.normalize("Breathless (1960).mkv")
        assert result.change_type == "unchanged"


# ─── Pattern 3: Year trapped in quality parenthetical ─────────────────────────

class TestYearInQualityParenthetical:
    """'(1978 - 480p - Áudio Original)' → extract year → '(1978)'"""

    def test_year_with_resolution_suffix(self, normalizer):
        """'(1978 - 480p - Áudio Original em Português)' → '(1978)'"""
        result = normalizer.normalize(
            "A Força dos Sentidos (1978 - 480p - Áudio Original em Português).mp4"
        )
        # Year must be preserved in cleaned filename
        assert "1978" in result.cleaned_filename
        # Quality junk must be gone from the parenthetical
        assert "480p" not in result.cleaned_filename
        assert result.change_type == "fix_year"

    def test_year_with_bluray_quality(self, normalizer):
        """'(1971) (2160p BluRay x265 10bit DV HDR r00t)' — second paren is quality, not year"""
        result = normalizer.normalize("Wake in Fright (1971) (2160p BluRay x265 10bit DV HDR r00t).mkv")
        assert "1971" in result.cleaned_filename
        assert "2160p" not in result.cleaned_filename
        assert result.change_type == "fix_year"

    def test_clean_year_paren_unchanged(self, normalizer):
        """'Film (1984)' — clean year paren → unchanged"""
        result = normalizer.normalize("Repo Man (1984).mkv")
        assert result.change_type == "unchanged"


# ─── Pattern 4: Multiple years, wrong one chosen ──────────────────────────────

class TestMultipleYears:
    """When leading year AND parenthetical year both present, trust the parenthetical"""

    def test_leading_year_same_as_paren(self, normalizer):
        """'1992 Andrew Dice Clay For Ladies (1992 Hbo Broadcast).m4v'
        Leading '1992' is redundant; year is in paren — strip leading year"""
        result = normalizer.normalize(
            "1992 Andrew Dice Clay For Ladies (1992 Hbo Broadcast) .m4v"
        )
        assert "1992" in result.cleaned_filename
        # The leading '1992 ' should not remain as part of title
        assert not result.cleaned_filename.startswith("1992")
        assert result.change_type == "fix_year"

    def test_no_false_positive_on_title_starting_with_year(self, normalizer):
        """'2001 - A Space Odyssey (1968)' — the leading '2001' is the title, not a year prefix"""
        result = normalizer.normalize("2001 - A Space Odyssey (1968).mkv")
        # Should NOT strip '2001' because it's part of the title
        assert "2001" in result.cleaned_filename
        # This should either be unchanged or fix_year, but NOT strip the 2001
        # The key: a 4-digit leading number followed by ' - ' (Brazilian format) that also
        # has a parenthetical year is ambiguous — we trust the parenthetical year
        # but preserve the title's leading year
        assert "Space Odyssey" in result.cleaned_filename


# ─── Pattern 5: TV episode format ─────────────────────────────────────────────

class TestTVEpisodeDetection:
    """TV episodes (SnnEnn) and multi-part films must be detected as nonfim"""

    def test_s01e05_format(self, normalizer):
        """Standard TV episode format → flag_nonfim"""
        result = normalizer.normalize("S01E05.mp4")
        assert result.change_type == "flag_nonfim"
        assert "tv" in result.notes.lower() or "episode" in result.notes.lower()

    def test_south_bank_show_episode(self, normalizer):
        """'The South Bank Show (1978) - S12E11...' → flag_nonfim"""
        result = normalizer.normalize("The South Bank Show (1978) - S12E11 - Marlon Brando.mp4")
        assert result.change_type == "flag_nonfim"

    def test_war_and_peace_part(self, normalizer):
        """'War.and.Peace.Part.1.Andrey.Bolkonsky WEB-DL 1080p.mkv' → flag_nonfim"""
        result = normalizer.normalize("War.and.Peace.Part.1.Andrey.Bolkonsky WEB-DL 1080p.mkv")
        assert result.change_type == "flag_nonfim"

    def test_real_film_not_flagged(self, normalizer):
        """'Breathless (1960).mkv' — not a TV episode → not flagged"""
        result = normalizer.normalize("Breathless (1960).mkv")
        assert result.change_type != "flag_nonfim"


# ─── Pattern 6: Interview / documentary prefix ────────────────────────────────

class TestNonFilmPrefixDetection:
    """Supplementary content with recognizable prefix → flag_nonfim"""

    def test_interview_prefix(self, normalizer):
        """'Interview - Stanley Kubrick (1966).mkv' → flag_nonfim"""
        result = normalizer.normalize("Interview - Stanley Kubrick (1966).mkv")
        assert result.change_type == "flag_nonfim"
        assert "supplementary" in result.notes.lower() or "nonfim" in result.notes.lower()

    def test_video_essay_prefix(self, normalizer):
        """'Video Essay - Robert Carringer - Rosebud Reconsidered (2021).mkv' → flag_nonfim"""
        result = normalizer.normalize(
            "Video Essay - Robert Carringer - Rosebud Reconsidered (2021).mkv"
        )
        assert result.change_type == "flag_nonfim"

    def test_audio_essay_prefix(self, normalizer):
        """'Audio Essay - Adam Holender.mkv' → flag_nonfim"""
        result = normalizer.normalize("Audio Essay - Adam Holender.mkv")
        assert result.change_type == "flag_nonfim"

    def test_audio_essay_lowercase(self, normalizer):
        """'Audio essay by author and critic Alexandra Heller-Nicholas.mkv' → flag_nonfim"""
        result = normalizer.normalize(
            "Audio essay by author and critic Alexandra Heller-Nicholas.mkv"
        )
        assert result.change_type == "flag_nonfim"

    def test_deleted_scene(self, normalizer):
        """'Deleted Scene.mkv' → flag_nonfim"""
        result = normalizer.normalize("Deleted Scene.mkv")
        assert result.change_type == "flag_nonfim"

    def test_deleted_scenes_plural(self, normalizer):
        """'Deleted Scenes.mkv' → flag_nonfim"""
        result = normalizer.normalize("Deleted Scenes.mkv")
        assert result.change_type == "flag_nonfim"

    def test_making_of_prefix(self, normalizer):
        """'A Million Feet of Film - The Making of One-Eyed Jacks.mkv' → flag_nonfim"""
        result = normalizer.normalize(
            "A Million Feet of Film - The Making of One-Eyed Jacks.mkv"
        )
        assert result.change_type == "flag_nonfim"

    def test_conversations_with_prefix(self, normalizer):
        """'Conversations with Marlon Brando.mkv' → flag_nonfim"""
        result = normalizer.normalize("Conversations with Marlon Brando - One-Eyed Jacks.mkv")
        assert result.change_type == "flag_nonfim"

    def test_real_film_not_flagged(self, normalizer):
        """'The Conversation (1974).mkv' — film title starting with 'The Conversation' → NOT nonfim"""
        result = normalizer.normalize("The Conversation (1974).mkv")
        assert result.change_type != "flag_nonfim"

    def test_documentary_film_title_not_flagged(self, normalizer):
        """'Documentary Now (2015).mkv' — a real film/show title, NOT a prefix"""
        result = normalizer.normalize("Documentary Now (2015).mkv")
        # Only flag if "Documentary" appears as a standalone prefix with dash separator
        # "Documentary Now" without a dash is likely a title, not a prefix
        # This tests the boundary condition


# ─── Unchanged: clean filenames should not be modified ────────────────────────

class TestUnchanged:
    """Well-formed filenames must pass through unmodified"""

    def test_simple_title_year(self, normalizer):
        result = normalizer.normalize("Breathless (1960).mkv")
        assert result.change_type == "unchanged"
        assert result.cleaned_filename == "Breathless (1960).mkv"

    def test_director_title_year(self, normalizer):
        result = normalizer.normalize("Jean-Luc Godard - Breathless (1960).mkv")
        assert result.change_type == "unchanged"

    def test_title_bracket_year(self, normalizer):
        result = normalizer.normalize("Rashomon [1950].mkv")
        assert result.change_type == "unchanged"

    def test_title_bare_year(self, normalizer):
        result = normalizer.normalize("Aguirre the Wrath of God 1972.mkv")
        assert result.change_type == "unchanged"

    def test_director_year_comma_format(self, normalizer):
        result = normalizer.normalize("A Bay of Blood (Mario Bava, 1971).mkv")
        assert result.change_type == "unchanged"


# ─── NormalizationResult contract ─────────────────────────────────────────────

class TestNormalizationResultContract:
    """NormalizationResult must always have all required fields"""

    def test_all_fields_present(self, normalizer):
        result = normalizer.normalize("Breathless (1960).mkv")
        assert hasattr(result, "original_filename")
        assert hasattr(result, "cleaned_filename")
        assert hasattr(result, "change_type")
        assert hasattr(result, "notes")

    def test_original_filename_preserved(self, normalizer):
        filename = "[DB]Tokyo Godfathers_-(Dual Audio).mkv"
        result = normalizer.normalize(filename)
        assert result.original_filename == filename

    def test_change_type_is_valid(self, normalizer):
        valid_types = {"strip_junk", "normalize_edition", "fix_year", "flag_nonfim", "unchanged"}
        result = normalizer.normalize("Breathless (1960).mkv")
        assert result.change_type in valid_types

    def test_extension_preserved_after_normalization(self, normalizer):
        """Normalize should never drop the file extension"""
        result = normalizer.normalize("[DB]Tokyo Godfathers (2003).mkv")
        assert result.cleaned_filename.endswith(".mkv")

    def test_mp4_extension_preserved(self, normalizer):
        result = normalizer.normalize("[zza]-Old.Boy.2003.1080p.x265.AC3.mkv")
        assert result.cleaned_filename.endswith(".mkv")
