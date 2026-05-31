from __future__ import annotations

import math
from datetime import datetime

from rapidfuzz import fuzz

from data.journal_models import JournalQuartile
from schemas.paper import PaperDTO
from services.field_citations import AcademicField, FieldNormalizedCitations
from services.journal_quality_service import JournalQualityService


class RankingService:
    """
    Ranking service with journal quality and field-normalized citations.

    Scoring dimensions:
    - relevance (0.25): Title + abstract match to query
    - semantic (0.20): AI-based semantic relevance (optional)
    - journal_quality (0.25): Journal quartile and metrics
    - recency (0.15): Publication date recency
    - citation (0.10): Field-normalized citation count
    - open_access (0.05): Open access bonus

    Journal quality is weighted heavily because it's a strong indicator
    of research validity and impact.
    """

    weights = {
        "relevance": 0.25,
        "semantic": 0.20,
        "journal_quality": 0.25,
        "recency": 0.15,
        "citation": 0.10,
        "open_access": 0.05,
    }

    @classmethod
    def score(
        cls, papers: list[PaperDTO], query: str, semantic_scores: list[float] | None = None
    ) -> list[PaperDTO]:
        if semantic_scores is None:
            semantic_scores = [0.0] * len(papers)
        return [
            cls.score_one(paper, query, s)
            for paper, s in zip(papers, semantic_scores, strict=False)
        ]

    @classmethod
    def score_one(cls, paper: PaperDTO, query: str, semantic_score: float = 0.0) -> PaperDTO:
        # Get journal quality score
        jq_service = JournalQualityService.instance()
        journal_quality = jq_service.score_journal(
            journal_title=paper.venue,
            issn=paper.venue_issn,
        )

        # Lookup the full journal record for quartile badge (UI consumption).
        # Cheap when journal_quality_score is non-default — same lookup
        # already happened inside score_journal but isn't returned.
        record = jq_service.get_record(
            journal_title=paper.venue,
            issn=paper.venue_issn,
        )
        quartile_value: str | None = None
        if record is not None and record.quartile != JournalQuartile.UNKNOWN:
            quartile_value = record.quartile.value  # "Q1" / "Q2" / "Q3" / "Q4"

        # Check if predatory
        is_predatory = jq_service.is_predatory(
            journal_title=paper.venue,
            publisher=paper.publisher,
            issn=paper.venue_issn,
        )

        # Detect field for citation normalization
        field = FieldNormalizedCitations.detect_field(
            venue=paper.venue,
            topics=paper.topics,
            abstract=paper.abstract,
        )

        # Calculate individual scores
        relevance = cls._relevance(query, paper)
        recency = cls._recency(paper.year)
        citation = cls._citation_field_normalized(paper.citation_count or 0, field)
        venue = cls._venue(paper.venue)
        open_access = 1.0 if paper.is_open_access else 0.0

        # Weighted average
        final = (
            relevance * cls.weights["relevance"]
            + semantic_score * cls.weights["semantic"]
            + journal_quality * cls.weights["journal_quality"]
            + recency * cls.weights["recency"]
            + citation * cls.weights["citation"]
            + open_access * cls.weights["open_access"]
        )

        # Apply predatory penalty (30% reduction)
        if is_predatory:
            final *= 0.7

        data = paper.model_dump()
        data.update(
            relevance_score=relevance,
            semantic_score=semantic_score,
            journal_quality_score=journal_quality,
            recency_score=recency,
            citation_score=citation,
            venue_score=venue,
            open_access_score=open_access,
            is_predatory=is_predatory,
            quartile=quartile_value,
            final_score=final,
        )
        return PaperDTO(**data)

    @staticmethod
    def _relevance(query: str, paper: PaperDTO) -> float:
        title_match = fuzz.token_set_ratio(query, paper.title) / 100
        abstract_match = (
            fuzz.token_set_ratio(query, paper.abstract or "") / 100 if paper.abstract else 0
        )
        return min(1.0, 0.7 * title_match + 0.3 * abstract_match)

    @staticmethod
    def _recency(year: int | None) -> float:
        if year is None:
            return 0.0
        age_years = max(0, datetime.now().year - year)
        return math.exp(-age_years / 5)

    @staticmethod
    def _citation(citation_count: int) -> float:
        """Simple citation scoring (legacy method)."""
        cap = 1000
        return min(1.0, math.log10(1 + citation_count) / math.log10(1 + cap))

    @staticmethod
    def _citation_field_normalized(citation_count: int, field: AcademicField) -> float:
        """
        Field-normalized citation scoring.

        Different fields have very different citation patterns.
        This method normalizes citations based on field averages.
        """
        return FieldNormalizedCitations.normalize_citations(citation_count, field)

    @staticmethod
    def _venue(venue: str | None) -> float:
        if not venue:
            return 0.4
        normalized = venue.lower()
        top_keywords = [
            # Multidisciplinary & General
            "nature",
            "science",
            "pnas",
            "cell",
            "plos",
            # CS & AI
            "neurips",
            "icml",
            "iclr",
            "cvpr",
            "acl",
            "jmlr",
            "tpami",
            "ieee",
            "acm",
            # Medicine & Health
            "lancet",
            "jama",
            "nejm",
            "bmj",
            "annals",
            # Physics & Math
            "phys",
            "math",
            "astron",
            # Chemistry & Biology
            "chem",
            "bio",
        ]
        if any(keyword in normalized for keyword in top_keywords):
            return 1.0
        return 0.6
