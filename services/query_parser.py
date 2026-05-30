"""
Advanced Query Parser for PaperLens

Supports syntax:
- "exact phrase" — exact match for phrases
- title:keyword — search in title only
- author:name — search by author name
- abstract:keyword — search in abstract only
- venue:name — search in venue/journal name
- year:2020-2024 — year range
- year:2023 — specific year
- NOT keyword — exclude keyword
- keyword1 AND keyword2 — both keywords required
- keyword1 OR keyword2 — either keyword

Field-specific with phrases:
- title:"convolutional neural network"
- abstract:"deep learning" NOT BERT

Examples:
- "machine learning" title:deep NOT year:2020
- author:smith abstract:"neural network" year:2019-2024
- title:"convolutional neural" venue:nature

Reference:
- Google Scholar search syntax: https://scholar.google.com/intl/en/scholar/help.html
- PubMed search syntax: https://pubmed.ncbi.nlm.nih.gov/help/
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FieldType(Enum):
    """Supported field types for field-specific search."""

    TITLE = "title"
    AUTHOR = "author"
    ABSTRACT = "abstract"
    VENUE = "venue"
    YEAR = "year"
    KEYWORD = "keyword"  # General keyword (default)


@dataclass(frozen=True)
class SearchTerm:
    """
    Single search term after parsing.

    Attributes:
        value: The search term value
        field: Which field to search in (None = all fields)
        is_exact: Whether this is an exact phrase match
        is_negated: Whether this term should be excluded (NOT)
    """

    value: str
    field: FieldType = FieldType.KEYWORD
    is_exact: bool = False
    is_negated: bool = False


@dataclass(frozen=True)
class YearRange:
    """
    Year range filter parsed from query.

    Attributes:
        year_from: Start year (inclusive), None = no lower bound
        year_to: End year (inclusive), None = no upper bound
    """

    year_from: int | None = None
    year_to: int | None = None


@dataclass(frozen=True)
class ParsedQuery:
    """
    Parsed search query with structured components.

    Attributes:
        raw: Original query string
        terms: List of parsed search terms
        year_range: Year range filter (if specified)
        has_exact_phrases: Whether any exact phrases are present
        has_field_searches: Whether any field-specific searches are present
        has_boolean_operators: Whether any boolean operators are used
    """

    raw: str
    terms: tuple[SearchTerm, ...]
    year_range: YearRange | None = None
    has_exact_phrases: bool = False
    has_field_searches: bool = False
    has_boolean_operators: bool = False

    @property
    def keywords(self) -> list[str]:
        """Get all keyword values (non-negated, for main search)."""
        return [t.value for t in self.terms if not t.is_negated and t.field == FieldType.KEYWORD]

    @property
    def title_terms(self) -> list[str]:
        """Get all title-specific terms."""
        return [t.value for t in self.terms if t.field == FieldType.TITLE]

    @property
    def author_terms(self) -> list[str]:
        """Get all author-specific terms."""
        return [t.value for t in self.terms if t.field == FieldType.AUTHOR]

    @property
    def abstract_terms(self) -> list[str]:
        """Get all abstract-specific terms."""
        return [t.value for t in self.terms if t.field == FieldType.ABSTRACT]

    @property
    def venue_terms(self) -> list[str]:
        """Get all venue-specific terms."""
        return [t.value for t in self.terms if t.field == FieldType.VENUE]

    @property
    def negated_terms(self) -> list[str]:
        """Get all negated terms (to exclude)."""
        return [t.value for t in self.terms if t.is_negated]

    def to_simple_query(self) -> str:
        """Convert back to simple query string for APIs that don't support advanced syntax."""
        parts = []
        for term in self.terms:
            if term.is_negated:
                continue  # Skip negated terms for simple queries
            if term.is_exact:
                parts.append(f'"{term.value}"')
            else:
                parts.append(term.value)
        return " ".join(parts)


class QueryParser:
    """
    Parse advanced search query syntax.

    Supports:
    - Quoted phrases: "machine learning"
    - Field-specific: title:deep, author:smith, abstract:"neural network"
    - Year ranges: year:2020-2024, year:2023
    - Boolean operators: AND, OR, NOT

    The parser uses a state machine approach to handle overlapping patterns.
    """

    # Field type mapping
    _FIELD_TYPE_MAP = {
        "title": FieldType.TITLE,
        "author": FieldType.AUTHOR,
        "abstract": FieldType.ABSTRACT,
        "venue": FieldType.VENUE,
        "year": FieldType.YEAR,
    }

    # Regex patterns
    _YEAR_RANGE = re.compile(r"^(\d{4})(?:-(\d{4}))?$")

    @classmethod
    def parse(cls, query: str) -> ParsedQuery:
        """
        Parse an advanced search query using state machine approach.

        Args:
            query: Raw search query string

        Returns:
            ParsedQuery with structured components

        Raises:
            ValueError: If query is invalid or empty after parsing
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        original_query = query
        terms: list[SearchTerm] = []
        year_range: YearRange | None = None
        has_exact = False
        has_field = False
        has_boolean = False

        # Tokenize the query
        tokens = cls._tokenize(query)

        # Process tokens
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Check for boolean operators
            if token.upper() == "AND" or token.upper() == "OR":
                has_boolean = True
                i += 1
                continue

            # Check for NOT operator
            if token.upper() == "NOT":
                has_boolean = True
                # Next token is negated
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if not cls._is_operator(next_token):
                        # Check if next token is a field search
                        if ":" in next_token:
                            field_term, field_year_range = cls._parse_field_term(
                                next_token, is_negated=True
                            )
                            if field_term:
                                terms.append(field_term)
                                has_field = True
                            if field_year_range:
                                year_range = field_year_range
                        else:
                            terms.append(SearchTerm(value=next_token, is_negated=True))
                        i += 2
                        continue
                i += 1
                continue

            # Check for field search
            if ":" in token:
                field_term, field_year_range = cls._parse_field_term(token)
                if field_term:
                    terms.append(field_term)
                    has_field = True
                    if field_term.is_exact:
                        has_exact = True
                if field_year_range:
                    year_range = field_year_range
                i += 1
                continue

            # Regular keyword or quoted phrase
            if token.startswith('"') and token.endswith('"'):
                # Quoted phrase
                phrase = token[1:-1].strip()
                if phrase:
                    terms.append(SearchTerm(value=phrase, is_exact=True))
                    has_exact = True
            elif token:
                terms.append(SearchTerm(value=token))

            i += 1

        # Build result
        return ParsedQuery(
            raw=original_query,
            terms=tuple(terms),
            year_range=year_range,
            has_exact_phrases=has_exact,
            has_field_searches=has_field,
            has_boolean_operators=has_boolean,
        )

    @classmethod
    def _tokenize(cls, query: str) -> list[str]:
        """
        Tokenize query string into individual tokens.

        Handles:
        - Quoted phrases (preserves spaces within)
        - Field:value and field:"value with spaces"
        - Boolean operators
        - Regular words
        """
        tokens = []
        i = 0
        n = len(query)

        while i < n:
            # Skip whitespace
            if query[i].isspace():
                i += 1
                continue

            # Check for quoted phrase
            if query[i] == '"':
                # Find closing quote
                j = i + 1
                while j < n and query[j] != '"':
                    j += 1
                if j < n:
                    # Found closing quote
                    tokens.append(query[i : j + 1])
                    i = j + 1
                else:
                    # No closing quote, treat rest as phrase
                    tokens.append(query[i:])
                    i = n
                continue

            # Check for field search (field:value or field:"value")
            # Look for field: pattern
            field_match = re.match(r"(title|author|abstract|venue|year):", query[i:], re.IGNORECASE)
            if field_match:
                field_prefix = field_match.group(0)
                j = i + len(field_prefix)

                # Check if value is quoted
                if j < n and query[j] == '"':
                    # Quoted field value
                    k = j + 1
                    while k < n and query[k] != '"':
                        k += 1
                    if k < n:
                        tokens.append(query[i : k + 1])
                        i = k + 1
                    else:
                        tokens.append(query[i:])
                        i = n
                else:
                    # Unquoted field value
                    k = j
                    while k < n and not query[k].isspace():
                        k += 1
                    tokens.append(query[i:k])
                    i = k
                continue

            # Regular word (might contain hyphens, etc.)
            j = i
            while j < n and not query[j].isspace() and query[j] != '"':
                j += 1
            if j > i:
                tokens.append(query[i:j])
            i = j

        return tokens

    @classmethod
    def _parse_field_term(
        cls, token: str, is_negated: bool = False
    ) -> tuple[SearchTerm | None, YearRange | None]:
        """
        Parse a field search token like "title:keyword" or 'title:"phrase"'.

        Returns (SearchTerm, YearRange) tuple. One may be None.
        """
        # Split on first colon
        parts = token.split(":", 1)
        if len(parts) != 2:
            return None, None

        field_str = parts[0].lower()
        value = parts[1].strip()

        if not value:
            return None, None

        # Get field type
        field_type = cls._FIELD_TYPE_MAP.get(field_str)
        if field_type is None:
            # Unknown field, treat as keyword
            return SearchTerm(value=token, is_negated=is_negated), None

        # Handle year specially
        if field_type == FieldType.YEAR:
            year_range = cls._parse_year_range(value)
            return None, year_range

        # Handle quoted value
        is_exact = False
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].strip()
            is_exact = True

        return SearchTerm(
            value=value, field=field_type, is_exact=is_exact, is_negated=is_negated
        ), None

    @classmethod
    def _parse_year_range(cls, value: str) -> YearRange | None:
        """Parse year range from string like '2020' or '2020-2024'."""
        match = cls._YEAR_RANGE.match(value)
        if not match:
            return None

        year_from = int(match.group(1))
        year_to_str = match.group(2)

        if year_to_str:
            year_to = int(year_to_str)
        else:
            year_to = year_from

        # Validate years
        if year_from < 1900 or year_from > 2100:
            return None
        if year_to < 1900 or year_to > 2100:
            return None
        if year_from > year_to:
            return None

        return YearRange(year_from=year_from, year_to=year_to)

    @classmethod
    def _is_operator(cls, word: str) -> bool:
        """Check if a word is a boolean operator."""
        return word.upper() in ("AND", "OR", "NOT")


# Convenience function
def parse_query(query: str) -> ParsedQuery:
    """Parse a search query and return structured components."""
    return QueryParser.parse(query)
