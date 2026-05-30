from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_doi


class CoreConnector(BaseConnector):
    name = "core"
    base_url = "https://api.core.ac.uk/v3"
    rate_limit_per_sec = 1.0
    requires_api_key = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        key = api_key or settings.core_api_key
        self.headers = {"User-Agent": settings.user_agent}
        if key:
            self.headers["Authorization"] = f"Bearer {key}"

    async def search(self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0) -> tuple[list[PaperDTO], int]:
        params: dict[str, Any] = {
            "q": query,
            "limit": limit,
            "offset": offset,
        }
        data = await self._get_json(f"{self.base_url}/search/works", params=params, headers=self.headers)
        
        total_hits = data.get("totalHits", 0)
        items = data.get("results", [])
        papers = [paper for item in items if (paper := self.normalize(item)) is not None]
        filtered_papers = [paper for paper in papers if filters.match(paper)]
        return filtered_papers, total_hits

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        params: dict[str, Any] = {"q": f'doi:"{normalized}"', "limit": 1, "offset": 0}
        data = await self._get_json(f"{self.base_url}/search/works", params=params, headers=self.headers)
        items = data.get("results", [])
        if not items:
            return None
        return self.normalize(items[0])

    def normalize(self, raw: dict[str, Any]) -> PaperDTO | None:
        title = raw.get("title")
        if isinstance(title, list):
            title = title[0] if title else None
        if not title:
            return None

        authors: list[AuthorDTO] = []
        for author in raw.get("authors") or []:
            if isinstance(author, str):
                name = author
                affiliation = None
            else:
                name = author.get("name") or author.get("fullName")
                affiliation = author.get("affiliation")
            if name:
                authors.append(AuthorDTO(name=name, affiliation=affiliation))

        year = self._extract_year(raw)
        publication_date = date(year, 1, 1) if year else None
        doi = self._extract_doi(raw)
        oa_url = self._extract_oa_url(raw)
        landing_url = raw.get("downloadUrl") or raw.get("url") or raw.get("sourceFulltextUrls", [None])[0]

        topics: list[str] = []
        for field in ("topics", "subjects", "fieldOfStudy", "keywords"):
            value = raw.get(field)
            if isinstance(value, list):
                for item in value:
                    text = item.get("name") if isinstance(item, dict) else item
                    if text and text not in topics:
                        topics.append(str(text))
            elif isinstance(value, str) and value not in topics:
                topics.append(value)

        venue = raw.get("publisher") or raw.get("journal") or raw.get("containerTitle")
        if isinstance(venue, dict):
            venue = venue.get("title") or venue.get("name")

        return PaperDTO(
            title=str(title),
            authors=authors,
            abstract=raw.get("abstract"),
            year=year,
            publication_date=publication_date,
            doi=doi,
            source=self.name,
            sources=[self.name],
            venue=venue,
            publisher=raw.get("publisher") if isinstance(raw.get("publisher"), str) else None,
            citation_count=raw.get("citationCount") or raw.get("citationsCount"),
            reference_count=raw.get("referenceCount") or raw.get("referencesCount"),
            is_open_access=bool(oa_url or raw.get("isOpenAccess") or raw.get("openAccess")),
            oa_url=oa_url,
            landing_url=landing_url,
            topics=topics,
            raw=raw,
        )

    def _extract_year(self, raw: dict[str, Any]) -> int | None:
        for key in ("yearPublished", "publishedYear", "year"):
            value = raw.get(key)
            if value:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass
        for key in ("publishedDate", "datePublished", "createdDate"):
            value = raw.get(key)
            if isinstance(value, str) and len(value) >= 4:
                try:
                    return int(value[:4])
                except ValueError:
                    pass
        return None

    def _extract_doi(self, raw: dict[str, Any]) -> str | None:
        doi = normalize_doi(raw.get("doi"))
        if doi:
            return doi
        identifiers = raw.get("identifiers") or []
        if isinstance(identifiers, list):
            for item in identifiers:
                if isinstance(item, str):
                    doi = normalize_doi(item)
                else:
                    value = item.get("identifier") or item.get("value") or item.get("id")
                    item_type = str(item.get("type") or "").lower()
                    doi = normalize_doi(value) if item_type == "doi" or "doi" in str(value).lower() else None
                if doi:
                    return doi
        return None

    def _extract_oa_url(self, raw: dict[str, Any]) -> str | None:
        for key in ("downloadUrl", "fullTextLink", "pdfUrl"):
            value = raw.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        for key in ("fullTextLinks", "sourceFulltextUrls", "links"):
            value = raw.get(key)
            if isinstance(value, list):
                for item in value:
                    url = item.get("url") if isinstance(item, dict) else item
                    if isinstance(url, str) and url.startswith(("http://", "https://")):
                        return url
        return None

    async def health_check(self) -> bool:
        try:
            data = await self._get_json(
                f"{self.base_url}/search/works",
                params={"q": "machine learning", "limit": 1},
                headers=self.headers,
            )
            return "results" in data
        except Exception:
            return False
