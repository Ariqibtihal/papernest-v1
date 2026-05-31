from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.rate_limit import RATE_LIMITS, limiter
from connectors.registry import ConnectorRegistry
from schemas.search import SearchRequest, SearchResponse
from services.search_service import SearchService

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
@limiter.limit(RATE_LIMITS["search"])
async def search_papers(request: Request, req: SearchRequest) -> SearchResponse:
    papers, latency_ms, total, warnings = await SearchService().run(
        query=req.query,
        filters=req.filters,
        limit=req.limit,
        offset=req.offset,
        sort_by=req.sort_by,
    )
    return SearchResponse(
        total=total,
        latency_ms=latency_ms,
        results=papers,
        offset=req.offset,
        has_more=(req.offset + len(papers)) < total,
        warnings=warnings,
    )


class SourceStatus(BaseModel):
    name: str
    healthy: bool
    latency_ms: int | None = None
    requires_api_key: bool = False


@router.get("/sources/status", response_model=list[SourceStatus])
async def sources_status() -> list[SourceStatus]:
    registry = ConnectorRegistry()
    results: list[SourceStatus] = []

    async def _check(name: str) -> SourceStatus:
        connector = registry._connectors[name]
        start = time.perf_counter()
        try:
            healthy = await connector.health_check()
            ms = int((time.perf_counter() - start) * 1000)
            return SourceStatus(
                name=name,
                healthy=healthy,
                latency_ms=ms,
                requires_api_key=connector.requires_api_key,
            )
        except Exception:
            ms = int((time.perf_counter() - start) * 1000)
            return SourceStatus(
                name=name, healthy=False, latency_ms=ms, requires_api_key=connector.requires_api_key
            )

    tasks = [_check(name) for name in registry.available_sources()]
    results = await asyncio.gather(*tasks)
    return list(results)
