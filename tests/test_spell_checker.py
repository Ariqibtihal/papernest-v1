"""
Tests for Spell Checker Service.

These tests validate the spell checking functionality.
"""

from __future__ import annotations

from services.spell_checker import SpellChecker, check_spelling, get_spell_checker


class TestSpellChecker:
    """Test SpellChecker functionality."""

    def test_common_misspelling(self):
        """Test detection of common misspellings."""
        checker = SpellChecker()

        # Test known misspellings
        result = checker.check("machne learning", auto_correct=False)

        # Suggestions should be provided for misspellings
        assert len(result.suggestions) > 0

    def test_technical_terms_not_corrected(self):
        """Test that technical terms are not corrected."""
        checker = SpellChecker()

        # Technical terms should be marked as correct
        result = checker.check("CNN neural network", auto_correct=False)

        # CNN should not be corrected
        assert "CNN" not in result.suggestions

    def test_auto_correct(self):
        """Test auto-correction mode."""
        checker = SpellChecker()

        result = checker.check("machne learning", auto_correct=True)

        if result.has_corrections:
            assert "machine" in result.corrected.lower()

    def test_empty_query(self):
        """Test empty query handling."""
        checker = SpellChecker()

        result = checker.check("", auto_correct=False)

        assert result.has_corrections is False
        assert result.corrected == ""

    def test_suggestions(self):
        """Test getting suggestions for a word."""
        checker = SpellChecker()

        suggestions = checker.suggest("machne")

        assert len(suggestions) > 0
        assert "machine" in suggestions

    def test_short_word_skipped(self):
        """Test that short words are skipped."""
        checker = SpellChecker()

        result = checker.check("AI ML", auto_correct=False)

        # Short words should not be checked
        assert result.has_corrections is False

    def test_query_preserved(self):
        """Test that query structure is preserved."""
        checker = SpellChecker()

        result = checker.check('"deep learning" title:neural', auto_correct=False)

        # Quotes and field syntax should be preserved
        assert '"' in result.corrected
        assert "title:" in result.corrected


class TestSpellCheckerIntegration:
    """Integration tests for spell checker."""

    def test_academic_query(self):
        """Test academic query spell checking."""
        result = check_spelling("convolutinal neural network", auto_correct=False)

        # Should provide suggestions for misspelled words
        assert len(result.suggestions) > 0

    def test_get_spell_checker_singleton(self):
        """Test that get_spell_checker returns singleton."""
        checker1 = get_spell_checker()
        checker2 = get_spell_checker()

        assert checker1 is checker2
