"""Tests for lib/director_matching.py — single shared director name matching (Issue #54)"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.director_matching import match_director


class TestSingleTokenCandidate:
    """Single-word candidates use whole-word token matching."""

    def test_exact_single_token(self):
        assert match_director('bava', 'bava') is True

    def test_single_token_in_multi_word_query(self):
        assert match_director('mario bava', 'bava') is True

    def test_single_token_not_substring(self):
        """'bava' must not match inside 'lamberto bava jr' via substring."""
        assert match_director('lamberto bava jr', 'bava') is True  # full token present

    def test_single_token_not_inside_word(self):
        """'argento' should not match 'argentoni' via substring."""
        assert match_director('argentoni', 'argento') is False

    def test_single_token_must_be_full_word(self):
        assert match_director('fulcifilm', 'fulci') is False

    def test_single_token_case_sensitivity(self):
        """Callers lowercase before passing — match_director is case-sensitive."""
        assert match_director('bava', 'bava') is True
        assert match_director('bava', 'Bava') is False  # caller lowercases

    def test_hyphenated_surname_is_single_token(self):
        """'robbe-grillet' contains no space — treated as single token."""
        assert match_director('alain robbe-grillet', 'robbe-grillet') is True

    def test_hyphenated_not_substring(self):
        assert match_director('robbe-grilletfilm', 'robbe-grillet') is False


class TestMultiTokenCandidate:
    """Multi-word candidates use substring matching."""

    def test_exact_multiword_match(self):
        assert match_director('tsui hark', 'tsui hark') is True

    def test_multiword_in_longer_query(self):
        assert match_director('director tsui hark 1990', 'tsui hark') is True

    def test_multiword_not_present(self):
        assert match_director('john woo', 'tsui hark') is False

    def test_multiword_partial_no_match(self):
        assert match_director('tsui', 'tsui hark') is False

    def test_multiword_first_name_last_name(self):
        assert match_director('jean-luc godard', 'jean-luc godard') is True

    def test_multiword_substring_safety(self):
        """Multi-word substring is safe — exact phrase has no false positives."""
        assert match_director('nagisa oshima', 'nagisa oshima') is True
        assert match_director('not nagisa oshima here', 'nagisa oshima') is True


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_query(self):
        assert match_director('', 'bava') is False

    def test_empty_candidate_single_token(self):
        """Empty string has no space — whole-word check: '' in [].split() → False."""
        assert match_director('bava', '') is False

    def test_single_char_candidate(self):
        assert match_director('a bava film', 'a') is True  # whole-word 'a'
        assert match_director('bava', 'a') is False

    def test_query_with_extra_spaces(self):
        """Extra spaces create empty tokens — '' in split() is False."""
        assert match_director('mario  bava', 'bava') is True  # split() handles multiple spaces

    def test_multiword_candidate_with_space_in_query(self):
        assert match_director('john tsui hark woo', 'tsui hark') is True
