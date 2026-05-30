from fastapi.testclient import TestClient

from app.main import app
from schemas.paper import PaperDTO
from services.search_service import SearchService


def test_search_route_returns_results(monkeypatch) -> None:
    """
    Smoke test for /api/v1/search.

    SearchService.run signature: (query, filters, limit, offset, sort_by)
    Returns: tuple of (papers, latency_ms, total, warnings).
    """

    async def fake_run(self, query, filters, limit, offset, sort_by):  # noqa: ARG001
        papers = [
            PaperDTO(
                title="Graph Neural Networks for Drug Discovery",
                source="crossref",
                sources=["crossref"],
                year=2024,
                citation_count=12,
                final_score=0.8,
            )
        ]
        latency_ms = 12
        total = 1
        warnings: list[str] = []
        return papers, latency_ms, total, warnings

    monkeypatch.setattr(SearchService, "run", fake_run)
    client = TestClient(app)
    response = client.post(
        "/api/v1/search",
        json={"query": "graph neural network", "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["latency_ms"] == 12
    assert data["results"][0]["source"] == "crossref"
