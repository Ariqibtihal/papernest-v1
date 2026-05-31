"""
Tests for Field-Normalized Citations.

These tests validate the citation normalization functionality.
"""

from __future__ import annotations

from services.field_citations import (
    FIELD_STATS,
    AcademicField,
    FieldNormalizedCitations,
)


class TestAcademicField:
    """Test AcademicField enum."""

    def test_field_values(self):
        """Test all field types exist."""
        assert AcademicField.PHYSICS.value == "physics"
        assert AcademicField.BIOMEDICINE.value == "biomedicine"
        assert AcademicField.COMPUTER_SCIENCE.value == "computer_science"
        assert AcademicField.MATHEMATICS.value == "mathematics"


class TestFieldNormalizedCitations:
    """Test FieldNormalizedCitations functionality."""

    def test_normalize_citations_physics(self):
        """Test citation normalization for physics."""
        # Physics has high average citations
        normalized = FieldNormalizedCitations.normalize_citations(
            citation_count=50,
            field=AcademicField.PHYSICS,
        )

        # 50 citations in physics should be around average
        assert 0.3 <= normalized <= 0.7

    def test_normalize_citations_math(self):
        """Test citation normalization for mathematics."""
        # Mathematics has low average citations
        normalized = FieldNormalizedCitations.normalize_citations(
            citation_count=50,
            field=AcademicField.MATHEMATICS,
        )

        # 50 citations in math should be very high
        assert normalized >= 0.8

    def test_normalize_citations_zero(self):
        """Test zero citations."""
        normalized = FieldNormalizedCitations.normalize_citations(
            citation_count=0,
            field=AcademicField.PHYSICS,
        )

        assert normalized == 0.0

    def test_normalize_citations_top(self):
        """Test top citations."""
        normalized = FieldNormalizedCitations.normalize_citations(
            citation_count=1000,
            field=AcademicField.PHYSICS,
        )

        assert normalized >= 0.95

    def test_detect_field_from_venue(self):
        """Test field detection from venue name."""
        field = FieldNormalizedCitations.detect_field(venue="Journal of Machine Learning Research")

        assert field == AcademicField.COMPUTER_SCIENCE

    def test_detect_field_from_venue_physics(self):
        """Test field detection from physics venue."""
        field = FieldNormalizedCitations.detect_field(venue="Physical Review Letters")

        assert field == AcademicField.PHYSICS

    def test_detect_field_from_topics(self):
        """Test field detection from topics."""
        field = FieldNormalizedCitations.detect_field(topics=["quantum", "particle", "nuclear"])

        assert field == AcademicField.PHYSICS

    def test_detect_field_unknown(self):
        """Test field detection for unknown text."""
        field = FieldNormalizedCitations.detect_field(
            venue="Journal of Random Stuff", topics=["random", "stuff"]
        )

        # Should return unknown or multidisciplinary
        assert field in (AcademicField.UNKNOWN, AcademicField.MULTIDISCIPLINARY)

    def test_citation_percentile(self):
        """Test citation percentile calculation."""
        percentile = FieldNormalizedCitations.citation_percentile(
            citation_count=100,
            field=AcademicField.COMPUTER_SCIENCE,
        )

        # 100 citations in CS should be high percentile
        assert percentile >= 80

    def test_get_field_stats(self):
        """Test getting field statistics."""
        stats = FieldNormalizedCitations.get_field_stats(AcademicField.PHYSICS)

        assert stats.field == AcademicField.PHYSICS
        assert stats.avg_citations > 0

    def test_cross_field_comparison(self):
        """Test that same citations normalize differently across fields."""
        citations = 20

        physics_score = FieldNormalizedCitations.normalize_citations(
            citations, AcademicField.PHYSICS
        )
        math_score = FieldNormalizedCitations.normalize_citations(
            citations, AcademicField.MATHEMATICS
        )

        # 20 citations should be higher percentile in math than physics
        assert math_score > physics_score


class TestFieldStats:
    """Test field statistics data."""

    def test_all_fields_have_stats(self):
        """Test that all fields have statistics."""
        for field in AcademicField:
            if field not in (AcademicField.UNKNOWN,):
                assert field in FIELD_STATS

    def test_stats_positive(self):
        """Test that all stats are positive."""
        for field, stats in FIELD_STATS.items():
            assert stats.avg_citations > 0
            assert stats.median_citations > 0
            assert stats.top_10_percent > 0
            assert stats.top_1_percent > 0
