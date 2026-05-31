from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_doi


class OpenAlexConnector(BaseConnector):
    name = "openalex"
    base_url = "https://api.openalex.org"
    rate_limit_per_sec = 10.0
    requires_api_key = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers = {"User-Agent": settings.user_agent}
        self.mailto = settings.contact_email

    async def search(
        self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0
    ) -> tuple[list[PaperDTO], int]:
        # OpenAlex uses 1-indexed pages
        page = (offset // limit) + 1
        params: dict[str, Any] = {
            "search": query,
            "per-page": limit,
            "page": page,
            "mailto": self.mailto,
        }
        filter_parts: list[str] = []
        if filters.year_from is not None:
            filter_parts.append(f"from_publication_date:{filters.year_from}-01-01")
        if filters.year_to is not None:
            filter_parts.append(f"to_publication_date:{filters.year_to}-12-31")
        if filters.open_access is True:
            filter_parts.append("is_oa:true")
        if filter_parts:
            params["filter"] = ",".join(filter_parts)
        data = await self._get_json(f"{self.base_url}/works", params=params, headers=self.headers)

        meta = data.get("meta", {})
        total_results = meta.get("count", 0)
        items = data.get("results", [])

        papers = [self.normalize(item) for item in items if item.get("title")]
        filtered_papers = [paper for paper in papers if filters.match(paper)]
        return filtered_papers, total_results

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        data = await self._get_json(
            f"{self.base_url}/works/doi:{normalized}",
            params={"mailto": self.mailto},
            headers=self.headers,
        )
        return self.normalize(data) if data else None

    def normalize(self, raw: dict[str, Any]) -> PaperDTO:
        title = raw.get("title") or raw.get("display_name") or "Untitled"
        ids = raw.get("ids") or {}
        doi = normalize_doi(ids.get("doi") or raw.get("doi"))
        primary_location = raw.get("primary_location") or {}
        source = primary_location.get("source") or {}
        open_access = raw.get("open_access") or {}
        best_oa_location = raw.get("best_oa_location") or {}
        publication_date = self._parse_date(raw.get("publication_date"))
        abstract = self._abstract_from_inverted_index(raw.get("abstract_inverted_index"))
        authors = [self._normalize_author(authorship) for authorship in raw.get("authorships", [])]
        topics = [
            concept.get("display_name")
            for concept in raw.get("concepts", [])
            if concept.get("display_name")
        ]
        landing_url = primary_location.get("landing_page_url") or ids.get("doi") or raw.get("id")
        oa_url = best_oa_location.get("pdf_url") or best_oa_location.get("landing_page_url")
        return PaperDTO(
            title=title,
            authors=authors,
            abstract=abstract,
            year=raw.get("publication_year"),
            publication_date=publication_date,
            doi=doi,
            source=self.name,
            sources=[self.name],
            venue=source.get("display_name"),
            venue_issn=self._first(source.get("issn")),
            publisher=source.get("host_organization_name"),
            citation_count=raw.get("cited_by_count"),
            reference_count=len(raw.get("referenced_works") or []),
            is_open_access=bool(open_access.get("is_oa")),
            oa_url=oa_url,
            landing_url=landing_url,
            topics=topics,
            raw=raw,
        )

    async def health_check(self) -> bool:
        data = await self._get_json(
            f"{self.base_url}/works",
            params={"per-page": 1, "mailto": self.mailto},
            headers=self.headers,
        )
        return "results" in data

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            year, month, day = value.split("-")
            return date(int(year), int(month), int(day))
        except ValueError:
            return None

    @staticmethod
    def _first(value: Any) -> str | None:
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _normalize_author(authorship: dict[str, Any]) -> AuthorDTO:
        author = authorship.get("author") or {}
        institutions = authorship.get("institutions") or []
        affiliation = None
        if institutions:
            affiliation = institutions[0].get("display_name")
        return AuthorDTO(
            name=author.get("display_name") or "Unknown Author",
            orcid=author.get("orcid"),
            affiliation=affiliation,
        )

    @staticmethod
    def _abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str | None:
        if not index:
            return None
        positioned_words: list[tuple[int, str]] = []
        for word, positions in index.items():
            for position in positions:
                positioned_words.append((position, word))
        positioned_words.sort(key=lambda item: item[0])
        return " ".join(word for _, word in positioned_words)
