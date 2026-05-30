"""
Tests for Query Parser.

These tests validate the advanced search query parsing functionality.
"""

from __future__ import annotations

import pytest

from services.query_parser import (
    FieldType,
    ParsedQuery,
    QueryParser,
    SearchTerm,
    YearRange,
)


class TestSearchTerm:
    """Test SearchTerm dataclass."""

    def test_default_values(self):
        """Test SearchTerm default values."""
        term = SearchTerm(value="test")
        assert term.value == "test"
        assert term.field == FieldType.KEYWORD
        assert term.is_exact is False
        assert term.is_negated is False

    def test_custom_values(self):
        """Test SearchTerm with custom values."""
        term = SearchTerm(
            value="machine learning",
            field=FieldType.TITLE,
            is_exact=True,
            is_negated=True,
        )
        assert term.value == "machine learning"
        assert term.field == FieldType.TITLE
        assert term.is_exact is True
        assert term.is_negated is True


class TestYearRange:
    """Test YearRange dataclass."""

    def test_year_range_creation(self):
        """Test YearRange creation."""
        yr = YearRange(year_from=2020, year_to=2024)
        assert yr.year_from == 2020
        assert yr.year_to == 2024

    def test_year_range_partial(self):
        """Test YearRange with partial values."""
        yr = YearRange(year_from=2020)
        assert yr.year_from == 2020
        assert yr.year_to is None


class TestQueryParser:
    """Test QueryParser functionality."""

    def test_simple_query(self):
        """Test simple keyword query."""
        parsed = QueryParser.parse("machine learning")

        assert parsed.raw == "machine learning"
        assert len(parsed.terms) == 2
        assert parsed.terms[0].value == "machine"
        assert parsed.terms[1].value == "learning"
        assert parsed.has_exact_phrases is False
        assert parsed.has_field_searches is False
        assert parsed.has_boolean_operators is False

    def test_quoted_phrase(self):
        """Test quoted phrase parsing."""
        parsed = QueryParser.parse('"deep learning"')

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "deep learning"
        assert parsed.terms[0].is_exact is True
        assert parsed.has_exact_phrases is True

    def test_field_search_title(self):
        """Test title: field search."""
        parsed = QueryParser.parse("title:neural")

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "neural"
        assert parsed.terms[0].field == FieldType.TITLE
        assert parsed.has_field_searches is True

    def test_field_search_title_quoted(self):
        """Test title:"phrase" field search."""
        parsed = QueryParser.parse('title:"neural network"')

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "neural network"
        assert parsed.terms[0].field == FieldType.TITLE
        assert parsed.terms[0].is_exact is True
        assert parsed.has_field_searches is True

    def test_field_search_author(self):
        """Test author: field search."""
        parsed = QueryParser.parse("author:smith")

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "smith"
        assert parsed.terms[0].field == FieldType.AUTHOR
        assert parsed.has_field_searches is True

    def test_field_search_abstract(self):
        """Test abstract: field search."""
        parsed = QueryParser.parse("abstract:neural")

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "neural"
        assert parsed.terms[0].field == FieldType.ABSTRACT

    def test_field_search_abstract_quoted(self):
        """Test abstract:"phrase" field search."""
        parsed = QueryParser.parse('abstract:"neural network"')

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "neural network"
        assert parsed.terms[0].field == FieldType.ABSTRACT
        assert parsed.terms[0].is_exact is True

    def test_field_search_venue(self):
        """Test venue: field search."""
        parsed = QueryParser.parse("venue:nature")

        assert len(parsed.terms) == 1
        assert parsed.terms[0].value == "nature"
        assert parsed.terms[0].field == FieldType.VENUE

    def test_year_specific(self):
        """Test year:YYYY syntax."""
        parsed = QueryParser.parse("year:2023")

        assert parsed.year_range is not None
        assert parsed.year_range.year_from == 2023
        assert parsed.year_range.year_to == 2023

    def test_year_range(self):
        """Test year:YYYY-YYYY syntax."""
        parsed = QueryParser.parse("year:2020-2024")

        assert parsed.year_range is not None
        assert parsed.year_range.year_from == 2020
        assert parsed.year_range.year_to == 2024

    def test_not_operator(self):
        """Test NOT operator."""
        parsed = QueryParser.parse("machine learning NOT deep")

        # Should have 3 terms: machine, learning, deep (negated)
        assert len(parsed.terms) == 3
        assert parsed.terms[0].value == "machine"
        assert parsed.terms[0].is_negated is False
        assert parsed.terms[1].value == "learning"
        assert parsed.terms[1].is_negated is False
        assert parsed.terms[2].value == "deep"
        assert parsed.terms[2].is_negated is True
        assert parsed.has_boolean_operators is True
        assert parsed.negated_terms == ["deep"]

    def test_and_operator(self):
        """Test AND operator."""
        parsed = QueryParser.parse("machine AND learning")

        assert len(parsed.terms) == 2
        assert parsed.has_boolean_operators is True

    def test_or_operator(self):
        """Test OR operator."""
        parsed = QueryParser.parse("neural OR deep")

        assert len(parsed.terms) == 2
        assert parsed.has_boolean_operators is True

    def test_complex_query(self):
        """Test complex query with multiple features."""
        parsed = QueryParser.parse('"deep learning" title:neural NOT survey author:smith')

        assert parsed.has_exact_phrases is True
        assert parsed.has_field_searches is True
        assert len(parsed.negated_terms) == 1
        assert "survey" in parsed.negated_terms

    def test_mixed_query(self):
        """Test mixed query with keywords and field searches."""
        parsed = QueryParser.parse("machine learning title:deep author:lecun")

        # Should have 4 terms total
        assert len(parsed.terms) == 4

        # Check fields
        fields = [t.field for t in parsed.terms]
        assert FieldType.KEYWORD in fields
        assert FieldType.TITLE in fields
        assert FieldType.AUTHOR in fields

    def test_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            QueryParser.parse("")

    def test_whitespace_only_query_raises(self):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            QueryParser.parse("   ")

    def test_invalid_year_format(self):
        """Test invalid year format is ignored."""
        parsed = QueryParser.parse("year:invalid")

        # Invalid year should be ignored, "year:invalid" stays as keyword
        assert parsed.year_range is None

    def test_year_out_of_range(self):
        """Test year out of valid range is ignored."""
        parsed = QueryParser.parse("year:1800")

        assert parsed.year_range is None

    def test_keywords_property(self):
        """Test keywords property."""
        parsed = QueryParser.parse("machine learning deep")

        assert parsed.keywords == ["machine", "learning", "deep"]

    def test_title_terms_property(self):
        """Test title_terms property."""
        parsed = QueryParser.parse("title:neural title:network")

        assert parsed.title_terms == ["neural", "network"]

    def test_author_terms_property(self):
        """Test author_terms property."""
        parsed = QueryParser.parse("author:smith author:jones")

        assert parsed.author_terms == ["smith", "jones"]

    def test_to_simple_query(self):
        """Test to_simple_query conversion."""
        parsed = QueryParser.parse('"deep learning" title:neural NOT exclude')

        simple = parsed.to_simple_query()

        # Should not include negated terms
        assert "exclude" not in simple
        # Should include exact phrases
        assert '"deep learning"' in simple


class TestQueryParserEdgeCases:
    """Test edge cases and robustness."""

    def test_multiple_quotes(self):
        """Test multiple quoted phrases."""
        parsed = QueryParser.parse('"machine learning" "deep learning"')

        assert len(parsed.terms) == 2
        assert parsed.terms[0].is_exact is True
        assert parsed.terms[1].is_exact is True

    def test_special_characters(self):
        """Test special characters in query."""
        parsed = QueryParser.parse("C++ Java# Python")

        # Should handle special characters
        assert len(parsed.terms) == 3

    def test_unicode_characters(self):
        """Test unicode characters in query."""
        parsed = QueryParser.parse("café résumé")

        # Should handle unicode
        assert len(parsed.terms) == 2

    def test_long_query(self):
        """Test long query performance."""
        long_query = " ".join([f"word{i}" for i in range(100)])

        parsed = QueryParser.parse(long_query)

        assert len(parsed.terms) == 100

    def test_case_insensitive_operators(self):
        """Test that operators are case-insensitive."""
        parsed1 = QueryParser.parse("NOT keyword")
        parsed2 = QueryParser.parse("not keyword")
        parsed3 = QueryParser.parse("Not keyword")

        assert len(parsed1.negated_terms) == 1
        assert len(parsed2.negated_terms) == 1
        assert len(parsed3.negated_terms) == 1


class TestQueryParserIntegration:
    """Integration tests with realistic queries."""

    def test_academic_search_example(self):
        """Test realistic academic search query."""
        query = '"convolutional neural network" author:lecun year:2015-2024 NOT survey'

        parsed = QueryParser.parse(query)

        assert parsed.has_exact_phrases is True
        assert parsed.has_field_searches is True
        assert parsed.year_range is not None
        assert parsed.year_range.year_from == 2015
        assert parsed.year_range.year_to == 2024
        assert len(parsed.negated_terms) == 1
        assert parsed.negated_terms[0] == "survey"

    def test_medical_research_query(self):
        """Test medical research query."""
        query = "COVID-19 vaccine author:fauci venue:NEJM year:2020-2023"

        parsed = QueryParser.parse(query)

        assert parsed.year_range is not None
        assert parsed.author_terms == ["fauci"]
        assert parsed.venue_terms == ["NEJM"]

    def test_computer_science_query(self):
        """Test computer science query."""
        query = '"transformer" title:attention NOT BERT year:2017-2024'

        parsed = QueryParser.parse(query)

        assert parsed.has_exact_phrases is True
        assert parsed.title_terms == ["attention"]
        assert parsed.year_range.year_from == 2017
        assert "BERT" in parsed.negated_terms

    def test_multi_field_query(self):
        """Test query with multiple field searches."""
        query = 'title:"deep learning" abstract:"neural network" author:hinton'

        parsed = QueryParser.parse(query)

        assert len(parsed.title_terms) == 1
        assert parsed.title_terms[0] == "deep learning"
        assert len(parsed.abstract_terms) == 1
        assert parsed.abstract_terms[0] == "neural network"
        assert len(parsed.author_terms) == 1
        assert parsed.author_terms[0] == "hinton"


class TestFieldType:
    """Test FieldType enum."""

    def test_field_types(self):
        """Test all field types exist."""
        assert FieldType.TITLE.value == "title"
        assert FieldType.AUTHOR.value == "author"
        assert FieldType.ABSTRACT.value == "abstract"
        assert FieldType.VENUE.value == "venue"
        assert FieldType.YEAR.value == "year"
        assert FieldType.KEYWORD.value == "keyword"


class TestConvenienceFunction:
    """Test parse_query convenience function."""

    def test_parse_query_function(self):
        """Test parse_query function works."""
        from services.query_parser import parse_query

        parsed = parse_query('"test query" author:smith')

        assert isinstance(parsed, ParsedQuery)
        assert parsed.has_exact_phrases is True
        assert parsed.has_field_searches is True
