from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AuthorDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    orcid: str | None = None
    affiliation: str | None = None


class PaperDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    authors: list[AuthorDTO] = Field(default_factory=list)
    abstract: str | None = None
    year: int | None = None
    publication_date: date | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    pubmed_id: str | None = None
    source: str
    sources: list[str] = Field(default_factory=list)
    venue: str | None = None
    venue_issn: str | None = None
    publisher: str | None = None
    citation_count: int | None = None
    reference_count: int | None = None
    is_open_access: bool = False
    oa_url: HttpUrl | None = None
    landing_url: HttpUrl | None = None
    topics: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    relevance_score: float | None = None
    recency_score: float | None = None
    citation_score: float | None = None
    venue_score: float | None = None
    journal_quality_score: float | None = None
    open_access_score: float | None = None
    semantic_score: float | None = None
    is_predatory: bool = False
    quartile: str | None = None  # "Q1" | "Q2" | "Q3" | "Q4" — exposed for UI badges
    final_score: float | None = None
