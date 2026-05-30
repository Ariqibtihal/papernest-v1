"""
Field-Normalized Citation Scoring

Different academic fields have very different citation patterns:
- Physics: ~50-100 average citations
- Biomedicine: ~20-50 average citations
- Computer Science: ~10-30 average citations
- Mathematics: ~2-10 average citations
- Social Sciences: ~5-20 average citations

This module normalizes citation counts based on field averages
to enable fair comparison across disciplines.

Data Sources:
- Scopus citation statistics by field
- Web of Science citation reports
- Google Scholar metrics

Reference:
- Hirsch, J. E. (2005). An index to quantify an individual's scientific research output.
- Bornmann, L., & Daniel, H. D. (2008). What do citation counts measure?
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger


class AcademicField(Enum):
    """Academic fields for citation normalization."""

    PHYSICS = "physics"
    BIOMEDICINE = "biomedicine"
    COMPUTER_SCIENCE = "computer_science"
    MATHEMATICS = "mathematics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    ENGINEERING = "engineering"
    SOCIAL_SCIENCE = "social_science"
    HUMANITIES = "humanities"
    MULTIDISCIPLINARY = "multidisciplinary"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FieldCitationStats:
    """
    Citation statistics for an academic field.

    Attributes:
        field: Academic field
        avg_citations: Average citations per paper (5-year window)
        median_citations: Median citations (more robust to outliers)
        top_10_percent: Citations threshold for top 10% papers
        top_1_percent: Citations threshold for top 1% papers
        source: Data source
        year: Year of data
    """

    field: AcademicField
    avg_citations: float
    median_citations: float
    top_10_percent: float
    top_1_percent: float
    source: str = "Scopus"
    year: int = 2024


# Field citation statistics (based on Scopus/WoS data)
# These are approximate values for normalization
FIELD_STATS: dict[AcademicField, FieldCitationStats] = {
    AcademicField.PHYSICS: FieldCitationStats(
        field=AcademicField.PHYSICS,
        avg_citations=45.0,
        median_citations=25.0,
        top_10_percent=120.0,
        top_1_percent=500.0,
    ),
    AcademicField.BIOMEDICINE: FieldCitationStats(
        field=AcademicField.BIOMEDICINE,
        avg_citations=35.0,
        median_citations=18.0,
        top_10_percent=95.0,
        top_1_percent=400.0,
    ),
    AcademicField.COMPUTER_SCIENCE: FieldCitationStats(
        field=AcademicField.COMPUTER_SCIENCE,
        avg_citations=18.0,
        median_citations=8.0,
        top_10_percent=50.0,
        top_1_percent=200.0,
    ),
    AcademicField.MATHEMATICS: FieldCitationStats(
        field=AcademicField.MATHEMATICS,
        avg_citations=8.0,
        median_citations=3.0,
        top_10_percent=25.0,
        top_1_percent=100.0,
    ),
    AcademicField.CHEMISTRY: FieldCitationStats(
        field=AcademicField.CHEMISTRY,
        avg_citations=30.0,
        median_citations=15.0,
        top_10_percent=80.0,
        top_1_percent=350.0,
    ),
    AcademicField.BIOLOGY: FieldCitationStats(
        field=AcademicField.BIOLOGY,
        avg_citations=40.0,
        median_citations=20.0,
        top_10_percent=100.0,
        top_1_percent=450.0,
    ),
    AcademicField.ENGINEERING: FieldCitationStats(
        field=AcademicField.ENGINEERING,
        avg_citations=15.0,
        median_citations=7.0,
        top_10_percent=40.0,
        top_1_percent=150.0,
    ),
    AcademicField.SOCIAL_SCIENCE: FieldCitationStats(
        field=AcademicField.SOCIAL_SCIENCE,
        avg_citations=12.0,
        median_citations=5.0,
        top_10_percent=35.0,
        top_1_percent=120.0,
    ),
    AcademicField.HUMANITIES: FieldCitationStats(
        field=AcademicField.HUMANITIES,
        avg_citations=5.0,
        median_citations=2.0,
        top_10_percent=15.0,
        top_1_percent=50.0,
    ),
    AcademicField.MULTIDISCIPLINARY: FieldCitationStats(
        field=AcademicField.MULTIDISCIPLINARY,
        avg_citations=25.0,
        median_citations=12.0,
        top_10_percent=70.0,
        top_1_percent=300.0,
    ),
}


# Field detection keywords
FIELD_KEYWORDS: dict[AcademicField, list[str]] = {
    AcademicField.PHYSICS: [
        "physics",
        "physical",
        "quantum",
        "particle",
        "nuclear",
        "astrophysics",
        "cosmology",
        "optics",
        "acoustics",
        "thermodynamics",
        "mechanics",
    ],
    AcademicField.BIOMEDICINE: [
        "medical",
        "medicine",
        "clinical",
        "patient",
        "disease",
        "therapy",
        "pharmacology",
        "pathology",
        "oncology",
        "cardiology",
        "neurology",
    ],
    AcademicField.COMPUTER_SCIENCE: [
        "computer",
        "computing",
        "software",
        "algorithm",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "data science",
        "programming",
        "database",
        "network",
        "security",
    ],
    AcademicField.MATHEMATICS: [
        "mathematics",
        "mathematical",
        "theorem",
        "proof",
        "algebra",
        "geometry",
        "topology",
        "analysis",
        "probability",
        "statistics",
    ],
    AcademicField.CHEMISTRY: [
        "chemistry",
        "chemical",
        "molecule",
        "compound",
        "reaction",
        "organic",
        "inorganic",
        "polymer",
        "catalyst",
        "synthesis",
    ],
    AcademicField.BIOLOGY: [
        "biology",
        "biological",
        "gene",
        "cell",
        "organism",
        "evolution",
        "ecology",
        "genetics",
        "molecular",
        "protein",
        "enzyme",
    ],
    AcademicField.ENGINEERING: [
        "engineering",
        "engineer",
        "design",
        "manufacturing",
        "materials",
        "robotics",
        "control",
        "signal",
        "electrical",
        "mechanical",
    ],
    AcademicField.SOCIAL_SCIENCE: [
        "social",
        "society",
        "psychology",
        "economics",
        "political",
        "education",
        "culture",
        "behavior",
        "survey",
        "policy",
    ],
    AcademicField.HUMANITIES: [
        "humanities",
        "history",
        "philosophy",
        "literature",
        "language",
        "linguistics",
        "archaeology",
        "anthropology",
        "theology",
    ],
}


class FieldNormalizedCitations:
    """
    Field-normalized citation scoring.

    Normalizes citation counts based on field averages to enable
    fair comparison across disciplines.
    """

    @staticmethod
    def detect_field(
        venue: str | None = None,
        topics: list[str] | None = None,
        abstract: str | None = None,
    ) -> AcademicField:
        """
        Detect academic field from paper metadata.

        Args:
            venue: Journal/venue name
            topics: List of topics/keywords
            abstract: Paper abstract

        Returns:
            Detected AcademicField
        """
        # Combine all text for detection
        text_parts = []
        if venue:
            text_parts.append(venue.lower())
        if topics:
            text_parts.extend([t.lower() for t in topics])
        if abstract:
            text_parts.append(abstract.lower())

        text = " ".join(text_parts)

        # Count matches for each field
        field_scores: dict[AcademicField, int] = {}

        for field, keywords in FIELD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                field_scores[field] = score

        if not field_scores:
            return AcademicField.UNKNOWN

        # Return field with highest score
        return max(field_scores, key=field_scores.get)  # type: ignore

    @staticmethod
    def normalize_citations(
        citation_count: int,
        field: AcademicField,
    ) -> float:
        """
        Normalize citation count based on field.

        Returns value between 0.0 and 1.0, where:
        - 0.0 = below average
        - 0.5 = average
        - 1.0 = top 1% in field

        Args:
            citation_count: Raw citation count
            field: Academic field

        Returns:
            Normalized citation score (0.0 - 1.0)
        """
        stats = FIELD_STATS.get(field)
        if stats is None:
            stats = FIELD_STATS[AcademicField.MULTIDISCIPLINARY]

        # Log-normalize to handle wide range
        # Using log scale to compress high citation counts
        if citation_count <= 0:
            return 0.0

        # Calculate percentile based on field statistics
        # Using log-normal distribution approximation
        avg = stats.avg_citations
        top_10 = stats.top_10_percent
        top_1 = stats.top_1_percent

        # Map to 0-1 scale
        if citation_count >= top_1:
            return 1.0
        elif citation_count >= top_10:
            # Map top_10 to top_1 range
            ratio = (citation_count - top_10) / (top_1 - top_10)
            return 0.8 + 0.2 * ratio
        elif citation_count >= avg:
            # Map average to top_10 range
            ratio = (citation_count - avg) / (top_10 - avg)
            return 0.5 + 0.3 * ratio
        else:
            # Below average
            ratio = citation_count / avg
            return 0.5 * ratio

    @staticmethod
    def get_field_stats(field: AcademicField) -> FieldCitationStats:
        """Get citation statistics for a field."""
        return FIELD_STATS.get(field, FIELD_STATS[AcademicField.MULTIDISCIPLINARY])

    @staticmethod
    def citation_percentile(
        citation_count: int,
        field: AcademicField,
    ) -> float:
        """
        Calculate citation percentile within field.

        Returns percentile (0-100) of citations within the field.
        """
        stats = FIELD_STATS.get(field)
        if stats is None:
            stats = FIELD_STATS[AcademicField.MULTIDISCIPLINARY]

        # Simple percentile approximation
        if citation_count <= 0:
            return 0.0

        avg = stats.avg_citations
        top_10 = stats.top_10_percent
        top_1 = stats.top_1_percent

        if citation_count >= top_1:
            return 99.0
        elif citation_count >= top_10:
            return 90.0 + 9.0 * (citation_count - top_10) / (top_1 - top_10)
        elif citation_count >= avg:
            return 50.0 + 40.0 * (citation_count - avg) / (top_10 - avg)
        else:
            return 50.0 * citation_count / avg


# Module-level singleton
_field_citations: FieldNormalizedCitations | None = None


def get_field_citations() -> FieldNormalizedCitations:
    """Get the singleton FieldNormalizedCitations instance."""
    global _field_citations
    if _field_citations is None:
        _field_citations = FieldNormalizedCitations()
    return _field_citations
