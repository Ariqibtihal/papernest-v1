from connectors.registry import ConnectorRegistry
from schemas.search import SearchFilters


def test_registry_exposes_all_sources() -> None:
    registry = ConnectorRegistry()
    assert registry.available_sources() == ["arxiv", "core", "crossref", "doaj", "europepmc", "openalex", "pubmed", "semantic_scholar"]


def test_registry_filters_requested_sources() -> None:
    registry = ConnectorRegistry()
    connectors = registry.active_connectors(SearchFilters(sources=["openalex"]))
    assert [connector.name for connector in connectors] == ["openalex"]
