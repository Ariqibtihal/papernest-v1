from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from schemas.paper import AuthorDTO, PaperDTO
from schemas.search import SearchFilters
from utils.normalize import normalize_doi


class PubmedConnector(BaseConnector):
    name = "pubmed"
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    rate_limit_per_sec = 3.0  # 3/sec without key; 10/sec with key
    requires_api_key = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        super().__init__(api_key=api_key, http_client=http_client)
        settings = get_settings()
        self.headers = {"User-Agent": settings.user_agent}
        self.api_key = settings.ncbi_api_key or api_key

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    async def search(
        self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0
    ) -> tuple[list[PaperDTO], int]:
        # 1. esearch -> PMIDs
        search_params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "retstart": offset,
            "retmode": "json",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key

        search_data = await self._get_json(
            f"{self.base_url}/esearch.fcgi", params=search_params, headers=self.headers
        )
        esearch_result = search_data.get("esearchresult", {})
        total_results = int(esearch_result.get("count", 0))
        pmids = esearch_result.get("idlist", [])
        if not pmids:
            return [], total_results

        # 2. efetch -> XML abstracts + metadata
        fetch_params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "abstract",
            "retmode": "xml",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        xml_text = await self._get_text(
            f"{self.base_url}/efetch.fcgi", params=fetch_params, headers=self.headers
        )
        root = ET.fromstring(xml_text)
        self._strip_ns(root)

        papers = []
        for article in root.findall("PubmedArticle"):
            paper = self.normalize(ET.tostring(article, encoding="unicode"))
            if paper:
                papers.append(paper)
        filtered = [p for p in papers if filters.match(p)]
        return filtered, total_results

    # ------------------------------------------------------------------
    # Get by DOI
    # ------------------------------------------------------------------
    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None

        search_params: dict[str, Any] = {
            "db": "pubmed",
            "term": f'"{normalized}"[DOI]',
            "retmax": 1,
            "retmode": "json",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key

        search_data = await self._get_json(
            f"{self.base_url}/esearch.fcgi", params=search_params, headers=self.headers
        )
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return None

        fetch_params: dict[str, Any] = {
            "db": "pubmed",
            "id": pmids[0],
            "rettype": "abstract",
            "retmode": "xml",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        xml_text = await self._get_text(
            f"{self.base_url}/efetch.fcgi", params=fetch_params, headers=self.headers
        )
        root = ET.fromstring(xml_text)
        self._strip_ns(root)

        article = root.find("PubmedArticle")
        if article is None:
            return None
        return self.normalize(ET.tostring(article, encoding="unicode"))

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------
    def normalize(self, raw: dict[str, Any] | str) -> PaperDTO | None:
        if isinstance(raw, str):
            root = ET.fromstring(raw)
            self._strip_ns(root)
        else:
            return None

        medline = root.find("MedlineCitation")
        if medline is None:
            return None
        article = medline.find("Article")
        if article is None:
            return None

        title_el = article.find("ArticleTitle")
        title = title_el.text.strip() if title_el is not None and title_el.text else None
        if not title:
            return None

        # Abstract (may contain multiple AbstractText with labels)
        abstract_parts: list[str] = []
        abstract_el = article.find("Abstract")
        if abstract_el is not None:
            for abs_text in abstract_el.findall("AbstractText"):
                label = abs_text.get("Label", "")
                text = abs_text.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        abstract = " ".join(abstract_parts).strip() or None

        # Authors
        authors: list[AuthorDTO] = []
        author_list = article.find("AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                last = author.find("LastName")
                fore = author.find("ForeName")
                init = author.find("Initials")
                coll = author.find("CollectiveName")
                aff = author.find("AffiliationInfo/Affiliation")

                if coll is not None and coll.text:
                    name = coll.text.strip()
                elif last is not None and last.text:
                    if fore is not None and fore.text:
                        name = f"{fore.text.strip()} {last.text.strip()}"
                    elif init is not None and init.text:
                        name = f"{last.text.strip()} {init.text.strip()}"
                    else:
                        name = last.text.strip()
                else:
                    continue
                authors.append(
                    AuthorDTO(
                        name=name,
                        affiliation=aff.text.strip() if aff is not None and aff.text else None,
                    )
                )

        # Year / Date
        year: int | None = None
        pub_date: date | None = None
        pub_date_el = article.find("Journal/JournalIssue/PubDate")
        if pub_date_el is None:
            pub_date_el = article.find("ArticleDate")
        if pub_date_el is not None:
            y = pub_date_el.find("Year")
            m = pub_date_el.find("Month")
            d = pub_date_el.find("Day")
            if y is not None and y.text:
                try:
                    year = int(y.text)
                    month = 1
                    day = 1
                    if m is not None and m.text:
                        month_str = m.text.strip().lower()
                        month = self._parse_month(month_str)
                    if d is not None and d.text:
                        try:
                            day = int(d.text)
                        except ValueError:
                            day = 1
                    pub_date = date(year, month, day)
                except (ValueError, TypeError):
                    pass

        # DOI
        doi = None
        for eid in article.findall("ELocationID"):
            if eid.get("EIdType", "").lower() == "doi" and eid.text:
                doi = normalize_doi(eid.text)
                if doi:
                    break
        if not doi:
            for aid in medline.findall("ArticleIdList/ArticleId"):
                if aid.get("IdType", "").lower() == "doi" and aid.text:
                    doi = normalize_doi(aid.text)
                    if doi:
                        break

        # PMID / PMCID
        pmid = None
        pmcid = None
        for aid in medline.findall("ArticleIdList/ArticleId"):
            id_type = aid.get("IdType", "").lower()
            if id_type == "pubmed" and aid.text:
                pmid = aid.text.strip()
            elif id_type == "pmc" and aid.text:
                pmcid = aid.text.strip()

        # Journal / Venue
        journal_el = article.find("Journal")
        venue = None
        issn = None
        if journal_el is not None:
            title_el = journal_el.find("Title")
            if title_el is not None and title_el.text:
                venue = title_el.text.strip()
            iso_el = journal_el.find("ISOAbbreviation")
            if not venue and iso_el is not None and iso_el.text:
                venue = iso_el.text.strip()
            issn_el = journal_el.find("ISSN")
            if issn_el is not None and issn_el.text:
                issn = issn_el.text.strip()

        # Topics (MeSH + Keywords)
        topics: list[str] = []
        for mesh in medline.findall("MeshHeadingList/MeshHeading/DescriptorName"):
            if mesh.text and mesh.text not in topics:
                topics.append(mesh.text)
        for kw_list in medline.findall("KeywordList"):
            for kw in kw_list.findall("Keyword"):
                if kw.text and kw.text not in topics:
                    topics.append(kw.text)

        # Open access / URLs
        is_oa = bool(pmcid)
        landing_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
        oa_url = None
        if pmcid:
            oa_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"

        return PaperDTO(
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            publication_date=pub_date,
            doi=doi,
            pubmed_id=pmid,
            source=self.name,
            sources=[self.name],
            venue=venue,
            venue_issn=issn,
            publisher=None,
            citation_count=None,
            reference_count=None,
            is_open_access=is_oa,
            oa_url=oa_url,
            landing_url=landing_url,
            topics=topics,
            raw=raw if isinstance(raw, dict) else {},
        )

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": "machine learning",
            "retmax": 1,
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            data = await self._get_json(
                f"{self.base_url}/esearch.fcgi", params=params, headers=self.headers
            )
            return "esearchresult" in data
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _get_text(self, url: str, **kwargs: Any) -> str:
        if self.http is None:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, **kwargs)
        else:
            response = await self.http.get(url, **kwargs)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _strip_ns(elem: ET.Element) -> None:
        for el in elem.iter():
            if "}" in el.tag:
                el.tag = el.tag.split("}", 1)[1]

    @staticmethod
    def _parse_month(value: str) -> int:
        months = {
            "jan": 1,
            "january": 1,
            "feb": 2,
            "february": 2,
            "mar": 3,
            "march": 3,
            "apr": 4,
            "april": 4,
            "may": 5,
            "jun": 6,
            "june": 6,
            "jul": 7,
            "july": 7,
            "aug": 8,
            "august": 8,
            "sep": 9,
            "september": 9,
            "sept": 9,
            "oct": 10,
            "october": 10,
            "nov": 11,
            "november": 11,
            "dec": 12,
            "december": 12,
        }
        return months.get(value.lower(), 1)
