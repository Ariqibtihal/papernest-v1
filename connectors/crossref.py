from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters


class CrossrefConnector(BaseConnector):
    name = "crossref"
    base_url = "https://api.crossref.org"
    rate_limit_per_sec = 1.0
    requires_api_key = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers = {"User-Agent": settings.user_agent}
        self.mailto = settings.contact_email

    async def search(self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0) -> tuple[list[PaperDTO], int]:
        params: dict[str, Any] = {
            "query": query,
            "rows": limit,
            "offset": offset,
            "mailto": self.mailto,
        }
        filter_parts: list[str] = []
        if filters.year_from is not None:
            filter_parts.append(f"from-pub-date:{filters.year_from}-01-01")
        if filters.year_to is not None:
            filter_parts.append(f"until-pub-date:{filters.year_to}-12-31")
        if filter_parts:
            params["filter"] = ",".join(filter_parts)
        data = await self._get_json(f"{self.base_url}/works", params=params, headers=self.headers)
        
        message = data.get("message", {})
        total_results = message.get("total-results", 0)
        items = message.get("items", [])
        
        papers = [self.normalize(item) for item in items if item.get("title")]
        filtered_papers = [paper for paper in papers if filters.match(paper)]
        return filtered_papers, total_results

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        safe_doi = doi.strip()
        data = await self._get_json(f"{self.base_url}/works/{safe_doi}", headers=self.headers)
        item = data.get("message")
        if not item:
            return None
        return self.normalize(item)

    def normalize(self, raw: dict[str, Any]) -> PaperDTO:
        title = self._first(raw.get("title")) or "Untitled"
        container_title = self._first(raw.get("container-title"))
        issued_date = self._date_from_parts(raw.get("published-print") or raw.get("published-online") or raw.get("issued"))
        authors = [self._normalize_author(author) for author in raw.get("author", [])]
        doi = raw.get("DOI")
        url = raw.get("URL")
        topics = [str(topic) for topic in raw.get("subject", []) if topic]
        issn = self._first(raw.get("ISSN"))
        abstract = raw.get("abstract")
        year = issued_date.year if issued_date else None
        return PaperDTO(
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            publication_date=issued_date,
            doi=doi,
            source=self.name,
            sources=[self.name],
            venue=container_title,
            venue_issn=issn,
            publisher=raw.get("publisher"),
            citation_count=raw.get("is-referenced-by-count"),
            reference_count=raw.get("reference-count"),
            is_open_access=False,
            landing_url=url,
            topics=topics,
            raw=raw,
        )

    async def health_check(self) -> bool:
        data = await self._get_json(f"{self.base_url}/works", params={"rows": 0, "mailto": self.mailto}, headers=self.headers)
        return data.get("status") == "ok"

    @staticmethod
    def _first(value: Any) -> str | None:
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _date_from_parts(value: dict[str, Any] | None) -> date | None:
        if not value:
            return None
        parts = value.get("date-parts") or []
        if not parts or not parts[0] or parts[0][0] is None:
            return None
        try:
            year = int(parts[0][0])
            month = int(parts[0][1]) if len(parts[0]) > 1 and parts[0][1] is not None else 1
            day = int(parts[0][2]) if len(parts[0]) > 2 and parts[0][2] is not None else 1
            return date(year, month, day)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize_author(raw_author: dict[str, Any]) -> AuthorDTO:
        given = raw_author.get("given") or ""
        family = raw_author.get("family") or ""
        name = f"{given} {family}".strip() or raw_author.get("name") or "Unknown Author"
        return AuthorDTO(name=name, orcid=raw_author.get("ORCID"), affiliation=None)
