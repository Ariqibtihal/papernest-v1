"""
Integration tests for the search flow.

Uses monkeypatching to avoid real external API calls while still exercising
the full request → service → response pipeline.
"""
from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from schemas.paper import AuthorDTO, PaperDTO
from services.search_service import SearchService

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_paper(title: str, year: int = 2023, source: str = "crossref") -> PaperDTO:
    return PaperDTO(
        title=title,
        source=source,
        sources=[source],
        year=year,
        citation_count=10,
        final_score=0.8,
        authors=[AuthorDTO(name="Test Author")],
    )


@pytest.fixture()
def mock_search(monkeypatch):
    """Replace SearchService.run with a fast fake that returns 3 papers."""
    papers = [
        _make_paper("Deep Learning for NLP", year=2023),
        _make_paper("Transformer Architectures", year=2022, source="openalex"),
        _make_paper("BERT Pre-training", year=2021, source="arxiv"),
    ]

    async def fake_run(self, query, filters, limit=25, offset=0, sort_by="relevance"):
        page = papers[offset: offset + limit]
        return page, 42, 3, []

    monkeypatch.setattr(SearchService, "run", fake_run)
    return papers


# ── Basic search ──────────────────────────────────────────────────────────────

class TestSearchEndpoint:
    def test_search_returns_200(self, mock_search):
        resp = client.post(
            "/api/v1/search",
            json={"query": "deep learning", "filters": {}, "limit": 25},
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_search_response_shape(self, mock_search):
        resp = client.post(
            "/api/v1/search",
            json={"query": "deep learning", "filters": {}, "limit": 25},
        )
        data = resp.json()
        assert "total" in data
        assert "results" in data
        assert "latency_ms" in data
        assert "has_more" in data
        assert "warnings" in data

    def test_search_returns_results(self, mock_search):
        resp = client.post(
            "/api/v1/search",
            json={"query": "deep learning", "filters": {}, "limit": 25},
        )
        data = resp.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3
        assert data["results"][0]["title"] == "Deep Learning for NLP"

    def test_search_pagination_offset(self, mock_search):
        resp = client.post(
            "/api/v1/search",
            json={"query": "deep learning", "filters": {}, "limit": 2, "offset": 1},
        )
        data = resp.json()
        # offset=1 → skip first paper
        assert data["results"][0]["title"] == "Transformer Architectures"

    def test_search_has_more_flag(self, mock_search):
        resp = client.post(
            "/api/v1/search",
            json={"query": "deep learning", "filters": {}, "limit": 2, "offset": 0},
        )
        data = resp.json()
        assert data["has_more"] is True

    def test_search_no_more_on_last_page(self, mock_search):
        resp = client.post(
            "/api/v1/search",
            json={"query": "deep learning", "filters": {}, "limit": 25, "offset": 0},
        )
        data = resp.json()
        assert data["has_more"] is False


# ── Input validation ──────────────────────────────────────────────────────────

class TestSearchValidation:
    def test_empty_query_rejected(self):
        resp = client.post(
            "/api/v1/search",
            json={"query": "", "filters": {}, "limit": 10},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_too_long_rejected(self):
        resp = client.post(
            "/api/v1/search",
            json={"query": "x" * 501, "filters": {}, "limit": 10},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_limit_above_max_rejected(self):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test", "filters": {}, "limit": 101},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_negative_limit_rejected(self):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test", "filters": {}, "limit": 0},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_sort_by_rejected(self):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test", "filters": {}, "sort_by": "invalid_sort"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_year_filter_out_of_range_rejected(self):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test", "filters": {"year_from": 1800}, "limit": 10},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ── Sort options ──────────────────────────────────────────────────────────────

class TestSearchSortOptions:
    @pytest.mark.parametrize("sort_by", ["relevance", "year_desc", "year_asc", "citations"])
    def test_valid_sort_options_accepted(self, mock_search, sort_by):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test", "filters": {}, "sort_by": sort_by},
        )
        assert resp.status_code == status.HTTP_200_OK


# ── Sources status ────────────────────────────────────────────────────────────

class TestSourcesStatus:
    def test_sources_status_returns_list(self):
        resp = client.get("/api/v1/sources/status")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_sources_status_shape(self):
        resp = client.get("/api/v1/sources/status")
        data = resp.json()
        for source in data:
            assert "name" in source
            assert "healthy" in source
            assert "requires_api_key" in source
