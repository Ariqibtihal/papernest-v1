from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.paper import AuthorDTO


class SavedPaperCreate(BaseModel):
    doi: str | None = None
    arxiv_id: str | None = None
    pubmed_id: str | None = None
    title: str
    authors: list[AuthorDTO] = []
    abstract: str | None = None
    year: int | None = None
    venue: str | None = None
    publisher: str | None = None
    source: str | None = None
    citation_count: int | None = None
    is_open_access: bool = False
    landing_url: str | None = None
    oa_url: str | None = None
    topics: list[str] = []
    notes: str | None = None


class SavedPaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doi: str | None
    arxiv_id: str | None
    pubmed_id: str | None
    title: str
    authors: list[AuthorDTO]
    abstract: str | None
    year: int | None
    venue: str | None
    publisher: str | None
    source: str | None
    citation_count: int | None
    is_open_access: bool
    landing_url: str | None
    oa_url: str | None
    topics: list[str]
    notes: str | None
    saved_at: datetime


class SavedPaperList(BaseModel):
    total: int
    items: list[SavedPaperOut]
