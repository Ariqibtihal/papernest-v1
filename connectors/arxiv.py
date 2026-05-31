from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_arxiv_id, normalize_doi


class ArxivConnector(BaseConnector):
    name = "arxiv"
    base_url = "http://export.arxiv.org/api"
    rate_limit_per_sec = 0.33  # arXiv polite limit: 1 req / 3 sec
    requires_api_key = False

    _ATOM = "{http://www.w3.org/2005/Atom}"
    _ARXIV = "{http://arxiv.org/schemas/atom}"

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers = {"User-Agent": settings.user_agent}

    async def search(
        self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0
    ) -> tuple[list[PaperDTO], int]:
        params: dict[str, Any] = {
            "search_query": f"all:{query}",
            "start": offset,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        data = await self._get_xml(f"{self.base_url}/query", params=params, headers=self.headers)

        # Parse total results
        opensearch = "{http://a9.com/-/spec/opensearch/1.1/}"
        total_el = data.find(f"{opensearch}totalResults")
        total_results = int(total_el.text) if total_el is not None and total_el.text else 0

        entries = data.findall(f".{self._ATOM}entry")
        papers = [self.normalize(ET.tostring(entry, encoding="unicode")) for entry in entries]
        filtered_papers = [paper for paper in papers if paper and filters.match(paper)]
        return filtered_papers, total_results

    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        params: dict[str, Any] = {
            "search_query": f"doi:{normalized}",
            "start": 0,
            "max_results": 1,
        }
        data = await self._get_xml(f"{self.base_url}/query", params=params, headers=self.headers)
        entries = data.findall(f".{self._ATOM}entry")
        if not entries:
            return None
        return self.normalize(ET.tostring(entries[0], encoding="unicode"))

    def normalize(self, raw: dict[str, Any] | str) -> PaperDTO | None:
        if isinstance(raw, str):
            root = ET.fromstring(raw)
        elif isinstance(raw, dict):
            # unexpected, but handle gracefully
            return None
        else:
            return None

        atom = self._ATOM
        arxiv = self._ARXIV

        title = self._text(root, f"{atom}title")
        if not title:
            return None

        summary = self._text(root, f"{atom}summary")
        published = self._text(root, f"{atom}published")
        entry_id = self._text(root, f"{atom}id") or ""
        arxiv_id = self._extract_arxiv_id(entry_id)

        authors: list[AuthorDTO] = []
        for author_el in root.findall(f"{atom}author"):
            name = self._text(author_el, f"{atom}name")
            aff = self._text(author_el, f"{arxiv}affiliation")
            if name:
                authors.append(AuthorDTO(name=name, affiliation=aff))

        categories: list[str] = []
        primary = root.find(f"{arxiv}primary_category")
        if primary is not None:
            term = primary.get("term")
            if term:
                categories.append(term)
        for cat in root.findall(f"{atom}category"):
            term = cat.get("term")
            if term and term not in categories:
                categories.append(term)

        pdf_url: str | None = None
        landing_url: str | None = None
        for link in root.findall(f"{atom}link"):
            href = link.get("href")
            rel = link.get("rel", "")
            title_attr = link.get("title", "")
            mime = link.get("type", "")
            if href:
                if title_attr.lower() == "pdf" or mime == "application/pdf":
                    pdf_url = href
                elif rel == "alternate" and not landing_url or not landing_url and not rel:
                    landing_url = href
        if not landing_url and entry_id:
            landing_url = entry_id

        doi = None
        doi_el = root.find(f"{arxiv}doi")
        if doi_el is not None and doi_el.text:
            doi = normalize_doi(doi_el.text)

        year: int | None = None
        pub_date: date | None = None
        if published:
            pub_date = self._parse_date(published)
            if pub_date:
                year = pub_date.year

        return PaperDTO(
            title=title,
            authors=authors,
            abstract=summary,
            year=year,
            publication_date=pub_date,
            doi=doi,
            arxiv_id=arxiv_id,
            source=self.name,
            sources=[self.name],
            venue="arXiv",
            publisher="arXiv",
            citation_count=None,
            reference_count=None,
            is_open_access=True,
            oa_url=pdf_url,
            landing_url=landing_url,
            topics=categories,
            raw=raw if isinstance(raw, dict) else {},
        )

    async def health_check(self) -> bool:
        params: dict[str, Any] = {"search_query": "all:machine+learning", "max_results": 1}
        try:
            data = await self._get_xml(
                f"{self.base_url}/query", params=params, headers=self.headers
            )
            entries = data.findall(f".{self._ATOM}entry")
            return len(entries) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _get_xml(self, url: str, **kwargs: Any) -> ET.Element:
        if self.http is None:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(url, **kwargs)
        else:
            response = await self.http.get(url, **kwargs)
        response.raise_for_status()
        return ET.fromstring(response.text)

    @staticmethod
    def _text(parent: ET.Element, tag: str) -> str | None:
        el = parent.find(tag)
        if el is None or el.text is None:
            return None
        return el.text.strip() or None

    @staticmethod
    def _extract_arxiv_id(entry_id: str) -> str | None:
        if not entry_id:
            return None
        value = entry_id.strip()
        if "/abs/" in value:
            return value.split("/abs/")[-1].split("v")[0]
        if "arxiv.org" in value:
            return value.split("/")[-1].split("v")[0]
        return normalize_arxiv_id(value)

    @staticmethod
    def _parse_date(value: str) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value.split("T")[0])
        except ValueError:
            return None
