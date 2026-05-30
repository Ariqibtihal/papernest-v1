from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_doi


class DoajConnector(BaseConnector):
    name = "doaj"
    base_url = "https://doaj.org/api/search/articles"
    rate_limit_per_sec = 2.0
    requires_api_key = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers = {"User-Agent": settings.user_agent}

    async def search(self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0) -> tuple[list[PaperDTO], int]:
        page = (offset // limit) + 1
        params: dict[str, Any] = {
            "pageSize": limit,
            "page": page,
        }
        url = f"{self.base_url}/{query}"
        data = await self._get_json(url, params=params, headers=self.headers)
        
        total_results = data.get("total", 0)
        items = data.get("results", [])
        
        papers = [self.normalize(item) for item in items]
        filtered_papers = [paper for paper in papers if paper and filters.match(paper)]
        return filtered_papers, total_results

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        url = f'{self.base_url}/doi:"{normalized}"'
        params: dict[str, Any] = {"pageSize": 1}
        data = await self._get_json(url, params=params, headers=self.headers)
        items = data.get("results", [])
        if not items:
            return None
        return self.normalize(items[0])

    def normalize(self, raw: dict[str, Any]) -> PaperDTO | None:
        bib = raw.get("bibjson") or {}
        title = bib.get("title")
        if not title:
            return None

        authors: list[AuthorDTO] = []
        for author in bib.get("author", []):
            name = author.get("name")
            if name:
                authors.append(AuthorDTO(name=name))

        doi = None
        for ident in bib.get("identifier", []):
            if ident.get("type", "").lower() == "doi":
                doi = normalize_doi(ident.get("id"))
                if doi:
                    break

        issn = None
        for ident in bib.get("identifier", []):
            if ident.get("type", "").lower() in ("pissn", "eissn"):
                issn = ident.get("id")
                if issn:
                    break

        year: int | None = None
        pub_date: date | None = None
        year_str = bib.get("year")
        month_str = bib.get("month")
        if year_str:
            try:
                year = int(year_str)
                if month_str:
                    try:
                        month = int(month_str)
                        pub_date = date(year, month, 1)
                    except (ValueError, TypeError):
                        pub_date = date(year, 1, 1)
                else:
                    pub_date = date(year, 1, 1)
            except (ValueError, TypeError):
                pass

        journal = bib.get("journal") or {}
        venue = journal.get("title")
        if not venue:
            venue = bib.get("journal_title")

        oa_url = None
        for link in bib.get("link", []):
            if link.get("type", "").lower() in ("fulltext", "article"):
                oa_url = link.get("url")
                if oa_url:
                    break

        topics: list[str] = []
        for subj in bib.get("subject", []):
            term = subj.get("term") or subj.get("scheme")
            if term and term not in topics:
                topics.append(term)
        for kw in bib.get("keywords", []):
            if kw and kw not in topics:
                topics.append(kw)

        return PaperDTO(
            title=title,
            authors=authors,
            abstract=bib.get("abstract"),
            year=year,
            publication_date=pub_date,
            doi=doi,
            source=self.name,
            sources=[self.name],
            venue=venue,
            venue_issn=issn,
            publisher=journal.get("publisher") or bib.get("publisher"),
            citation_count=None,
            reference_count=None,
            is_open_access=True,
            oa_url=oa_url,
            landing_url=oa_url,
            topics=topics,
            raw=raw,
        )

    async def health_check(self) -> bool:
        url = f'{self.base_url}/title:"machine learning"'
        params: dict[str, Any] = {"pageSize": 1}
        try:
            data = await self._get_json(url, params=params, headers=self.headers)
            return "results" in data
        except Exception:
            return False
