from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_doi


class SemanticScholarConnector(BaseConnector):
    name = "semantic_scholar"
    base_url = "https://api.semanticscholar.org/graph/v1"
    rate_limit_per_sec = 0.1  # 1 req / 10 sec without key to avoid 429; higher with key
    requires_api_key = False

    _FIELDS = (
        "title,authors,year,citationCount,referenceCount,"
        "influentialCitationCount,isOpenAccess,openAccessPdf,"
        "fieldsOfStudy,publicationDate,venue,journal,externalIds,abstract"
    )

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers: dict[str, str] = {}
        if settings.semantic_scholar_api_key:
            self.headers["x-api-key"] = settings.semantic_scholar_api_key
        self.headers["User-Agent"] = settings.user_agent

    async def search(self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0) -> tuple[list[PaperDTO], int]:
        params: dict[str, Any] = {
            "query": query,
            "fields": self._FIELDS,
            "limit": limit,
            "offset": offset,
        }
        if filters.year_from is not None and filters.year_to is not None:
            params["publicationDateOrYear"] = f"{filters.year_from}:{filters.year_to}"
        elif filters.year_from is not None:
            params["publicationDateOrYear"] = f"{filters.year_from}:"

        data = await self._get_json(f"{self.base_url}/paper/search", params=params, headers=self.headers)
        
        total_hits = data.get("total", 0)
        items = data.get("data", [])
        papers = [self.normalize(item) for item in items if item.get("title")]
        filtered_papers = [paper for paper in papers if filters.match(paper)]
        return filtered_papers, total_hits

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        params: dict[str, Any] = {"fields": self._FIELDS}
        try:
            data = await self._get_json(
                f"{self.base_url}/paper/DOI:{normalized}",
                params=params,
                headers=self.headers,
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        return self.normalize(data) if data else None

    def normalize(self, raw: dict[str, Any]) -> PaperDTO:
        title = raw.get("title") or "Untitled"
        external_ids = raw.get("externalIds") or {}
        doi = normalize_doi(external_ids.get("DOI"))
        arxiv_id = external_ids.get("ArXiv")
        pubmed_id = external_ids.get("PubMed")

        authors = [
            AuthorDTO(name=author.get("name", "Unknown Author"))
            for author in raw.get("authors", [])
            if author.get("name")
        ]

        venue = raw.get("venue")
        journal = raw.get("journal") or {}
        if not venue and journal:
            venue = journal.get("name")

        oa_pdf = raw.get("openAccessPdf") or {}
        oa_url = oa_pdf.get("url")
        if not oa_url:
            oa_url = None
        is_oa = bool(raw.get("isOpenAccess"))

        pub_date: date | None = None
        year: int | None = raw.get("year")
        publication_date_str = raw.get("publicationDate")
        if publication_date_str:
            try:
                pub_date = date.fromisoformat(publication_date_str)
                if year is None:
                    year = pub_date.year
            except ValueError:
                pass

        return PaperDTO(
            title=title,
            authors=authors,
            abstract=raw.get("abstract"),
            year=year,
            publication_date=pub_date,
            doi=doi,
            arxiv_id=arxiv_id,
            pubmed_id=pubmed_id,
            source=self.name,
            sources=[self.name],
            venue=venue,
            publisher=journal.get("publisher") if journal else None,
            citation_count=raw.get("citationCount"),
            reference_count=raw.get("referenceCount"),
            is_open_access=is_oa,
            oa_url=oa_url,
            landing_url=raw.get("url") if raw.get("url") else None,
            topics=raw.get("fieldsOfStudy") or [],
            raw=raw,
        )

    async def health_check(self) -> bool:
        params: dict[str, Any] = {"query": "machine learning", "fields": "title", "limit": 1}
        try:
            data = await self._get_json(
                f"{self.base_url}/paper/search", params=params, headers=self.headers
            )
            return "data" in data
        except Exception:
            return False
