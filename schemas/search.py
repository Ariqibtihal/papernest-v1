from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.paper import PaperDTO


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    sources: list[str] | None = None
    open_access: bool | None = None
    min_citations: int | None = Field(default=None, ge=0, le=1000000)
    venue_contains: str | None = Field(default=None, max_length=200)
    topic: str | None = Field(default=None, max_length=100)
    institution: str | None = Field(default=None, max_length=200)
    type: str | None = None

    @field_validator("year_from", "year_to")
    @classmethod
    def validate_year_range(cls, v: int | None) -> int | None:
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v

    @field_validator("venue_contains", "topic", "institution")
    @classmethod
    def sanitize_text_filter(cls, v: str | None) -> str | None:
        """
        Sanitize text filters: strip HTML and trim whitespace.

        We intentionally do NOT blacklist SQL keywords ('drop', 'delete', etc.).
        Reasons:
          1. All DB queries are parametrized via SQLAlchemy — SQL injection
             is impossible regardless of input content.
          2. External API calls send these as URL params or JSON, not raw SQL.
          3. Academic queries legitimately contain these words: "drop in CO2",
             "gene deletion studies", "update on COVID vaccine".
        """
        if v:
            v = re.sub(r"<[^>]+>", "", v)
            v = v.strip()
        return v

    def match(self, paper: PaperDTO) -> bool:
        if self.year_from is not None and paper.year is not None and paper.year < self.year_from:
            return False
        if self.year_to is not None and paper.year is not None and paper.year > self.year_to:
            return False
        if self.open_access is not None and paper.is_open_access != self.open_access:
            return False
        if self.min_citations is not None and (paper.citation_count or 0) < self.min_citations:
            return False
        if self.venue_contains and self.venue_contains.lower() not in (paper.venue or "").lower():
            return False
        if self.topic and not any(self.topic.lower() in t.lower() for t in paper.topics):
            return False
        if self.institution:
            has_inst = any(
                a.affiliation and self.institution.lower() in a.affiliation.lower()
                for a in paper.authors
            )
            if not has_inst:
                return False
        if self.type:
            # Derived paper type logic for filtering
            paper_type = "other"
            venue_lower = (paper.venue or "").lower()
            if (
                "journal" in venue_lower
                or "conference" in venue_lower
                or paper.arxiv_id
                or paper.pubmed_id
            ):
                paper_type = "article"
            elif "book" in venue_lower:
                paper_type = "book-chapter"
            if paper_type != self.type:
                return False
        return True


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=500)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=10000)
    sort_by: Literal["relevance", "year_desc", "year_asc", "citations"] = "relevance"

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """
        Sanitize search query: strip HTML and whitespace.

        Same rationale as `sanitize_text_filter` — blacklisting SQL keywords
        would reject legitimate academic queries ("drop in CO2", "gene
        deletion") while providing zero security benefit. SQL injection is
        prevented by SQLAlchemy parametrized queries; external API calls
        forward the query string as URL/JSON params, not raw SQL.
        """
        v = re.sub(r"<[^>]+>", "", v)
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty after sanitization")
        return v


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    latency_ms: int
    results: list[PaperDTO]
    offset: int = 0
    has_more: bool = False
    warnings: list[str] = Field(default_factory=list)
