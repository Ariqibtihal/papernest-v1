"""
Spell Correction Service for PaperLens

Provides spell checking and correction for search queries.
Uses PySpelling with technical/academic dictionaries.

Features:
- Multi-language support (English primary)
- Technical term handling (not over-correcting domain terms)
- Query suggestions for misspelled terms
- Configurable correction thresholds

Reference:
- PySpelling: https://github.com/pycontribs/pyspelling
- Aspell: http://aspell.net/
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from loguru import logger


@dataclass(frozen=True)
class CorrectionResult:
    """
    Result of spell correction.

    Attributes:
        original: Original query
        corrected: Corrected query (if corrections were made)
        corrections: List of (original_word, corrected_word) pairs
        has_corrections: Whether any corrections were made
        suggestions: Dictionary of word -> list of suggestions
    """

    original: str
    corrected: str
    corrections: tuple[tuple[str, str], ...]
    has_corrections: bool
    suggestions: dict[str, list[str]]

    @property
    def correction_count(self) -> int:
        """Number of corrections made."""
        return len(self.corrections)


class SpellChecker:
    """
    Spell checker for academic search queries.

    Uses PySpelling with custom dictionaries for:
    - Common English words
    - Technical/academic terms
    - Common abbreviations (e.g., CNN, LSTM, BERT)

    The checker is designed to:
    - NOT over-correct domain-specific terms
    - Preserve query structure
    - Provide suggestions without automatic correction
    """

    # Common academic/technical terms that should not be corrected
    TECHNICAL_TERMS = {
        # ML/DL terms
        "cnn",
        "rnn",
        "lstm",
        "gru",
        "gan",
        "vae",
        "bert",
        "gpt",
        "transformer",
        "attention",
        "embedding",
        "backpropagation",
        "gradient",
        "neural",
        "tensor",
        "keras",
        "pytorch",
        "tensorflow",
        "sklearn",
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "jupyter",
        "colab",
        # Common abbreviations
        "arxiv",
        "doi",
        "issn",
        "isbn",
        "pubmed",
        "scopus",
        "wos",
        "ieee",
        "acm",
        "springer",
        "elsevier",
        "nature",
        "science",
        # Programming terms
        "api",
        "rest",
        "json",
        "xml",
        "html",
        "css",
        "javascript",
        "python",
        "java",
        "cpp",
        "rust",
        "golang",
        "typescript",
        # Research terms
        "abstract",
        "methodology",
        "hypothesis",
        "empirical",
        "theoretical",
        "qualitative",
        "quantitative",
        "meta-analysis",
        "systematic",
    }

    # Common misspellings and their corrections
    COMMON_CORRECTIONS = {
        "machne": "machine",
        "machien": "machine",
        "machiene": "machine",
        "neurl": "neural",
        "neurak": "neural",
        "netowrk": "network",
        "netowk": "network",
        "deepth": "depth",
        "learing": "learning",
        "reinforcment": "reinforcement",
        "convolutinal": "convolutional",
        "convoltional": "convolutional",
        "attetion": "attention",
        "atention": "attention",
        "transfomer": "transformer",
        "transformr": "transformer",
        "classifiction": "classification",
        "classifiation": "classification",
        "segmantation": "segmentation",
        "segmentaion": "segmentation",
        "recogniton": "recognition",
        "recogniiton": "recognition",
        "predction": "prediction",
        "predictoin": "prediction",
        "optimiztion": "optimization",
        "optimiation": "optimization",
        "regualrization": "regularization",
        "regulariztion": "regularization",
        "generatvie": "generative",
        "geneartive": "generative",
        "discriminatvie": "discriminative",
        "discrminative": "discriminative",
    }

    def __init__(self):
        """Initialize spell checker."""
        self._loaded = False
        self._aspell = None
        self._try_load_aspell()

    def _try_load_aspell(self):
        """Try to load PySpelling/Aspell."""
        try:
            import subprocess

            result = subprocess.run(
                ["aspell", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._loaded = True
                logger.info("Aspell loaded successfully")
            else:
                logger.warning("Aspell not available, using fallback spell checker")
        except FileNotFoundError:
            logger.warning("Aspell not installed, using fallback spell checker")
        except Exception as e:
            logger.warning(f"Failed to load Aspell: {e}, using fallback")

    def check(self, query: str, auto_correct: bool = False) -> CorrectionResult:
        """
        Check spelling of a search query.

        Args:
            query: Search query to check
            auto_correct: If True, apply corrections automatically

        Returns:
            CorrectionResult with corrections and suggestions
        """
        if not query or not query.strip():
            return CorrectionResult(
                original=query,
                corrected=query,
                corrections=(),
                has_corrections=False,
                suggestions={},
            )

        # Tokenize query
        words = self._tokenize(query)

        corrections = []
        suggestions = {}
        corrected_words = []

        for word in words:
            # Skip short words, numbers, and technical terms
            if len(word) <= 2 or word.isdigit() or self._is_technical_term(word):
                corrected_words.append(word)
                continue

            # Check spelling
            is_correct, word_suggestions = self._check_word(word)

            if not is_correct and word_suggestions:
                suggestions[word] = word_suggestions

                # Apply correction if auto_correct and good suggestion available
                if auto_correct and word_suggestions:
                    best_suggestion = word_suggestions[0]
                    if best_suggestion.lower() != word.lower():
                        corrections.append((word, best_suggestion))
                        corrected_words.append(best_suggestion)
                        continue

            corrected_words.append(word)

        # Reconstruct query
        corrected_query = " ".join(corrected_words)

        return CorrectionResult(
            original=query,
            corrected=corrected_query,
            corrections=tuple(corrections),
            has_corrections=len(corrections) > 0,
            suggestions=suggestions,
        )

    def suggest(self, word: str, max_suggestions: int = 5) -> list[str]:
        """
        Get spelling suggestions for a word.

        Args:
            word: Word to get suggestions for
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested corrections
        """
        if not word or len(word) <= 2:
            return []

        # Check common corrections first
        if word.lower() in self.COMMON_CORRECTIONS:
            return [self.COMMON_CORRECTIONS[word.lower()]]

        # Check Aspell if available
        if self._loaded and self._aspell:
            return self._aspell_suggest(word, max_suggestions)

        # Fallback: no suggestions
        return []

    def _check_word(self, word: str) -> tuple[bool, list[str]]:
        """
        Check if a word is spelled correctly.

        Returns:
            (is_correct, list_of_suggestions)
        """
        # Check common corrections first
        if word.lower() in self.COMMON_CORRECTIONS:
            return False, [self.COMMON_CORRECTIONS[word.lower()]]

        # Check Aspell if available
        if self._loaded:
            return self._aspell_check(word)

        # Fallback: assume correct
        return True, []

    def _aspell_check(self, word: str) -> tuple[bool, list[str]]:
        """Check word using Aspell."""
        try:
            import subprocess

            result = subprocess.run(
                ["aspell", "list", "-l", "en"],
                input=word,
                capture_output=True,
                text=True,
                timeout=5,
            )

            # If aspell returns nothing, word is correct
            if not result.stdout.strip():
                return True, []

            # Get suggestions
            suggestions = self._aspell_suggest(word)
            return False, suggestions

        except Exception as e:
            logger.debug(f"Aspell check failed: {e}")
            return True, []

    def _aspell_suggest(self, word: str, max_suggestions: int = 5) -> list[str]:
        """Get Aspell suggestions for a word."""
        try:
            import subprocess

            result = subprocess.run(
                ["aspell", "dump", "suggest"],
                input=word,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.stdout.strip():
                suggestions = result.stdout.strip().split("\n")
                return suggestions[:max_suggestions]

            return []

        except Exception as e:
            logger.debug(f"Aspell suggest failed: {e}")
            return []

    def _is_technical_term(self, word: str) -> bool:
        """Check if a word is a technical term that should not be corrected."""
        return word.lower() in self.TECHNICAL_TERMS

    def _tokenize(self, query: str) -> list[str]:
        """Tokenize query into words."""
        # Split on whitespace and preserve quotes
        tokens = re.findall(r'(?:"[^"]+"|\S+)', query)
        return tokens


# Module-level singleton
_spell_checker: SpellChecker | None = None


def get_spell_checker() -> SpellChecker:
    """Get the singleton SpellChecker instance."""
    global _spell_checker
    if _spell_checker is None:
        _spell_checker = SpellChecker()
    return _spell_checker


# Convenience function
def check_spelling(query: str, auto_correct: bool = False) -> CorrectionResult:
    """Check spelling of a search query."""
    return get_spell_checker().check(query, auto_correct)
