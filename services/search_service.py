from __future__ import annotations

import asyncio
import time
from typing import Literal

from loguru import logger

from app.core.http import HTTPClientManager
from connectors.base import BaseConnector
from connectors.registry import ConnectorRegistry
from schemas.paper import PaperDTO
from schemas.search import SearchFilters
from services.ai_service import AIService
from services.cache_service import get_search_cache
from services.dedup_service import get_dedup_service
from services.query_parser import FieldType, ParsedQuery, QueryParser, YearRange
from services.ranking_service import RankingService
from services.spell_checker import get_spell_checker

SortOption = Literal["relevance", "year_desc", "year_asc", "citations"]

# Maximum seconds to wait for a single connector before giving up
CONNECTOR_TIMEOUT_SECONDS = 10

# Number of results to fetch from each connector per search
CONNECTOR_FETCH_LIMIT = 100


# ── Helpers ───────────────────────────────────────────────────────────────────


def _sort_papers(papers: list[PaperDTO], sort_by: SortOption) -> list[PaperDTO]:
    if sort_by == "year_desc":
        return sorted(papers, key=lambda p: p.year or 0, reverse=True)
    if sort_by == "year_asc":
        return sorted(papers, key=lambda p: p.year or 0)
    if sort_by == "citations":
        return sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)
    return papers  # "relevance" — already sorted by score


def _build_connector_query(parsed: ParsedQuery) -> str:
    """
    Build optimized query string for academic API connectors.

    Most academic APIs (Crossref, OpenAlex, PubMed, etc.) support:
    - Simple keyword search
    - Quoted phrases for exact match
    - Boolean operators (AND, OR, NOT)

    This function converts parsed query to API-friendly format.
    """
    parts = []

    for term in parsed.terms:
        if term.is_negated:
            # APIs typically don't support NOT well, handle in post-filter
            continue

        if term.is_exact:
            parts.append(f'"{term.value}"')
        elif term.field == FieldType.TITLE:
            # Most APIs don't support title: prefix, use quote for emphasis
            parts.append(f'"{term.value}"')
        elif term.field == FieldType.AUTHOR:
            # Some APIs support author: prefix
            parts.append(f"author:{term.value}")
        elif term.field == FieldType.ABSTRACT or term.field == FieldType.VENUE:
            parts.append(f'"{term.value}"')
        else:
            parts.append(term.value)

    return " ".join(parts)


def _merge_year_ranges(
    filter_range: YearRange | None,
    query_range: YearRange | None,
) -> tuple[int | None, int | None]:
    """
    Merge year ranges from filters and query.

    Returns (year_from, year_to) with the most restrictive bounds.
    """
    year_from = None
    year_to = None

    if filter_range:
        year_from = filter_range.year_from
        year_to = filter_range.year_to

    if query_range:
        # Query year range is more specific, use it if filter is not set
        if year_from is None or (query_range.year_from and query_range.year_from > year_from):
            year_from = query_range.year_from
        if year_to is None or (query_range.year_to and query_range.year_to < year_to):
            year_to = query_range.year_to

    return year_from, year_to


def _post_filter_negated(papers: list[PaperDTO], negated_terms: list[str]) -> list[PaperDTO]:
    """
    Filter out papers matching negated terms.

    Checks title, abstract, and author fields.
    """
    if not negated_terms:
        return papers

    filtered = []
    for paper in papers:
        skip = False
        text_to_check = f"{paper.title or ''} {paper.abstract or ''}".lower()

        # Check authors too
        author_names = " ".join(a.name.lower() for a in paper.authors)
        text_to_check += f" {author_names}"

        for term in negated_terms:
            if term.lower() in text_to_check:
                skip = True
                break

        if not skip:
            filtered.append(paper)

    return filtered


async def _fetch_connector(
    connector: BaseConnector,
    query: str,
    filters: SearchFilters,
    limit: int,
) -> tuple[list[PaperDTO], int]:
    """Wrap a single connector call with a hard per-connector timeout."""
    return await asyncio.wait_for(
        connector.search(query, filters, limit=limit, offset=0),
        timeout=CONNECTOR_TIMEOUT_SECONDS,
    )


# ── Service ───────────────────────────────────────────────────────────────────


class SearchService:
    """Orchestrates multi-source search: fetch → dedup → filter → rank → cache → paginate."""

    async def run(
        self,
        query: str,
        filters: SearchFilters,
        limit: int = 25,
        offset: int = 0,
        sort_by: SortOption = "relevance",
    ) -> tuple[list[PaperDTO], int, int, list[str]]:
        """
        Execute a search and return (page_results, latency_ms, total_count, warnings).

        Supports advanced syntax:
        - "exact phrases"
        - title:, author:, abstract:, venue:, year:
        - AND, OR, NOT operators
        - Automatic spell correction suggestions

        Results are cached after the first fetch so subsequent page requests are instant.
        """
        start = time.perf_counter()
        warnings: list[str] = []

        # ── 0. Spell check and suggestions ─────────────────────────────────
        spell_checker = get_spell_checker()
        spell_result = spell_checker.check(query, auto_correct=False)

        # Add spell suggestions to warnings
        if spell_result.corrections:
            for original, corrected in spell_result.corrections:
                warnings.append(f"Did you mean '{corrected}' instead of '{original}'?")

        # ── 1. Parse query ─────────────────────────────────────────────────
        try:
            parsed = QueryParser.parse(query)
        except ValueError as e:
            logger.warning(f"Invalid query: {e}")
            return [], 0, 0, [f"Invalid query: {e}"]

        # Merge year ranges from query and filters
        query_year_range = parsed.year_range
        filter_year_range = None
        if filters.year_from is not None or filters.year_to is not None:
            filter_year_range = YearRange(
                year_from=filters.year_from,
                year_to=filters.year_to,
            )

        merged_year_from, merged_year_to = _merge_year_ranges(filter_year_range, query_year_range)

        # Update filters with merged year range
        updated_filters = filters.model_copy(
            update={
                "year_from": merged_year_from,
                "year_to": merged_year_to,
            }
        )

        # Build query for connectors
        connector_query = _build_connector_query(parsed)

        # ── 1. Cache hit — fast path ──────────────────────────────────────────
        cache = get_search_cache()
        filters_dict = updated_filters.model_dump()
        cached = cache.get(connector_query, filters_dict, sort_by)
        if cached is not None:
            cached_results, cached_total = cached
            logger.info(f"Cache hit for query='{query}' offset={offset}")
            page = cached_results[offset : offset + limit]
            return page, int((time.perf_counter() - start) * 1000), cached_total, warnings

        # ── 2. Fetch from all connectors in parallel ──────────────────────────
        papers, global_total, fetch_warnings = await self._fetch_all(
            connector_query, updated_filters
        )
        warnings.extend(fetch_warnings)

        # ── 3. Dedup + filter ─────────────────────────────────────────────────
        deduped = get_dedup_service().dedupe(papers)
        filtered = [p for p in deduped if updated_filters.match(p)]

        # ── 4. Post-filter negated terms ──────────────────────────────────────
        if parsed.negated_terms:
            before_count = len(filtered)
            filtered = _post_filter_negated(filtered, parsed.negated_terms)
            logger.info(f"Negated terms removed {before_count - len(filtered)} papers")

        logger.info(
            f"query='{query}' raw={len(papers)} deduped={len(deduped)} filtered={len(filtered)}"
        )

        # ── 5. Score + sort ───────────────────────────────────────────────────
        sorted_papers = await self._score_and_sort(query, filtered, sort_by)

        # ── 6. Cache full result set ──────────────────────────────────────────
        cache.set(connector_query, filters_dict, sort_by, sorted_papers, global_total)
        logger.info(f"Cached {len(sorted_papers)} results, global_total={global_total}")

        # ── 7. Paginate ───────────────────────────────────────────────────────
        page = sorted_papers[offset : offset + limit]
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(f"Returning {len(page)} results, total={global_total}, latency={latency_ms}ms")
        return page, latency_ms, global_total, warnings

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _fetch_all(
        self,
        query: str,
        filters: SearchFilters,
    ) -> tuple[list[PaperDTO], int, list[str]]:
        """
        Dispatch search to all active connectors in parallel.
        Returns (papers, global_total, warnings).
        Each connector is given CONNECTOR_TIMEOUT_SECONDS before being abandoned.
        """
        registry = ConnectorRegistry(http_client=HTTPClientManager.get_client())
        connectors = registry.active_connectors(filters)
        if not connectors:
            return [], 0, []

        logger.info(
            f"Fetching from {len(connectors)} connectors "
            f"(limit={CONNECTOR_FETCH_LIMIT}, timeout={CONNECTOR_TIMEOUT_SECONDS}s each)"
        )
        tasks = [_fetch_connector(c, query, filters, CONNECTOR_FETCH_LIMIT) for c in connectors]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        papers: list[PaperDTO] = []
        global_total = 0
        warnings: list[str] = []

        for connector, response in zip(connectors, responses, strict=True):
            if isinstance(response, Exception):
                warnings.extend(self._handle_connector_error(connector.name, response))
                continue
            connector_papers, connector_total = response
            papers.extend(connector_papers)
            global_total += connector_total
            logger.info(
                f"Connector {connector.name}: {len(connector_papers)} papers, total={connector_total}"
            )

        return papers, global_total, warnings

    @staticmethod
    def _handle_connector_error(name: str, exc: Exception) -> list[str]:
        """Log a connector failure and return a user-facing warning if appropriate."""
        if isinstance(exc, asyncio.TimeoutError):
            logger.warning(f"Connector '{name}' timed out after {CONNECTOR_TIMEOUT_SECONDS}s")
            return [f"Source {name.capitalize()} timed out."]
        if "429" in str(exc):
            # Rate-limited — silent, don't bother the user
            logger.warning(f"Connector '{name}' rate-limited (429)")
            return []
        logger.exception(f"Connector '{name}' failed unexpectedly")
        return [f"Source {name.capitalize()} is currently unavailable."]

    @staticmethod
    async def _score_and_sort(
        query: str,
        papers: list[PaperDTO],
        sort_by: SortOption,
    ) -> list[PaperDTO]:
        """Apply semantic reranking (if relevance sort), composite scoring, and sort."""
        semantic_scores: list[float] | None = None
        if papers and sort_by == "relevance":
            ai_svc = AIService()
            semantic_scores = await ai_svc.rerank_papers(query, papers[:100])
            # Pad to full length if AI returned fewer scores than papers
            if len(semantic_scores) < len(papers):
                semantic_scores += [0.0] * (len(papers) - len(semantic_scores))

        scored = RankingService.score(papers, query=query, semantic_scores=semantic_scores)
        scored.sort(key=lambda p: p.final_score or 0, reverse=True)
        return _sort_papers(scored, sort_by)
