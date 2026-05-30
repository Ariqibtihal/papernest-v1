from __future__ import annotations

import httpx

from app.config import get_settings
from connectors.base import BaseConnector
from connectors.arxiv import ArxivConnector
from connectors.core import CoreConnector
from connectors.crossref import CrossrefConnector
from connectors.doaj import DoajConnector
from connectors.europepmc import EuropePmcConnector
from connectors.openalex import OpenAlexConnector
from connectors.pubmed import PubmedConnector
from connectors.semantic_scholar import SemanticScholarConnector
from schemas.search import SearchFilters


class ConnectorRegistry:
    def __init__(self, http_client: httpx.AsyncClient | None = None):
        settings = get_settings()
        self._connectors: dict[str, BaseConnector] = {
            "crossref": CrossrefConnector(http_client=http_client),
            "core": CoreConnector(http_client=http_client),
            "openalex": OpenAlexConnector(http_client=http_client),
            "arxiv": ArxivConnector(http_client=http_client),
            "semantic_scholar": SemanticScholarConnector(http_client=http_client),
            "doaj": DoajConnector(http_client=http_client),
            "europepmc": EuropePmcConnector(http_client=http_client),
            "pubmed": PubmedConnector(http_client=http_client),
        }

    def active_connectors(self, filters: SearchFilters) -> list[BaseConnector]:
        requested = set(filters.sources or self._connectors.keys())
        return [connector for name, connector in self._connectors.items() if name in requested]

    def available_sources(self) -> list[str]:
        return sorted(self._connectors.keys())
