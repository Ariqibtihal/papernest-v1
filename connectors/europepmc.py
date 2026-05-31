from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_doi


class EuropePmcConnector(BaseConnector):
    name = "europepmc"
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    rate_limit_per_sec = 5.0
    requires_api_key = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers = {"User-Agent": settings.user_agent}

    async def search(
        self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0
    ) -> tuple[list[PaperDTO], int]:
        # EuropePMC uses cursorMark for pagination, which is token-based.
        # For simplicity, we only return the first page if offset == 0, else empty if we can't use offset easily.
        # But we still return total.
        if offset > 0:
            return [], 0

        params: dict[str, Any] = {
            "query": query,
            "pageSize": limit,
            "format": "json",
            "resultType": "lite",
            "cursorMark": "*",
        }
        data = await self._get_json(f"{self.base_url}/search", params=params, headers=self.headers)
        total_results = data.get("hitCount", 0)
        items = data.get("resultList", {}).get("result", [])
        papers = [self.normalize(item) for item in items if item.get("title")]
        filtered_papers = [paper for paper in papers if filters.match(paper)]
        return filtered_papers, total_results

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        params: dict[str, Any] = {
            "query": f'DOI:"{normalized}"',
            "pageSize": 1,
            "format": "json",
            "resultType": "lite",
        }
        data = await self._get_json(f"{self.base_url}/search", params=params, headers=self.headers)
        items = data.get("resultList", {}).get("result", [])
        if not items:
            return None
        return self.normalize(items[0])

    def normalize(self, raw: dict[str, Any]) -> PaperDTO:
        title = raw.get("title") or "Untitled"
        doi = normalize_doi(raw.get("doi"))
        pmid = raw.get("pmid")
        pmcid = raw.get("pmcid")

        authors: list[AuthorDTO] = []
        author_str = raw.get("authorString")
        if author_str:
            # "Smith J, Doe A" -> split by comma then strip
            for part in author_str.split(","):
                name = part.strip()
                if name:
                    authors.append(AuthorDTO(name=name))

        year: int | None = None
        pub_date: date | None = None
        year_str = raw.get("pubYear")
        if year_str:
            try:
                year = int(year_str)
                pub_date = date(year, 1, 1)
            except (ValueError, TypeError):
                pass

        is_oa = raw.get("isOpenAccess") == "Y"
        oa_url = None
        if pmcid and raw.get("hasPDF") == "Y":
            oa_url = f"https://europepmc.org/articles/{pmcid}?pdf=render"

        landing_url = None
        if pmcid:
            landing_url = f"https://europepmc.org/article/PMC/{pmcid}"
        elif pmid:
            landing_url = f"https://europepmc.org/article/MED/{pmid}"

        return PaperDTO(
            title=title,
            authors=authors,
            abstract=raw.get("abstractText"),
            year=year,
            publication_date=pub_date,
            doi=doi,
            pubmed_id=pmid,
            source=self.name,
            sources=[self.name],
            venue=raw.get("journalTitle"),
            publisher=None,
            citation_count=None,
            reference_count=None,
            is_open_access=is_oa,
            oa_url=oa_url,
            landing_url=landing_url,
            topics=[],
            raw=raw,
        )

    async def health_check(self) -> bool:
        params: dict[str, Any] = {
            "query": "machine learning",
            "pageSize": 1,
            "format": "json",
            "resultType": "lite",
        }
        try:
            data = await self._get_json(
                f"{self.base_url}/search", params=params, headers=self.headers
            )
            return "resultList" in data
        except Exception:
            return False
