"""
Search Analytics Service for PaperLens

Provides tracking and analytics for:
- Search queries
- Paper clicks
- User behavior patterns
- Popular queries

Features:
- Click-through rate tracking
- Query popularity ranking
- User engagement metrics
- Search result quality signals

Uses in-memory storage with optional Redis persistence.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class SearchEvent:
    """Single search event."""

    query: str
    user_id: int | None = None
    results_count: int = 0
    timestamp: float = field(default_factory=time.time)
    session_id: str | None = None


@dataclass
class ClickEvent:
    """Single paper click event."""

    query: str
    paper_id: str  # DOI or arXiv ID
    position: int  # Position in search results
    user_id: int | None = None
    timestamp: float = field(default_factory=time.time)
    session_id: str | None = None


@dataclass
class QueryStats:
    """Statistics for a search query."""

    query: str
    search_count: int = 0
    click_count: int = 0
    avg_click_position: float = 0.0
    avg_results_count: float = 0.0
    last_searched: float = 0.0
    ctr: float = 0.0  # Click-through rate


@dataclass
class PaperStats:
    """Statistics for a paper."""

    paper_id: str
    click_count: int = 0
    avg_position: float = 0.0
    last_clicked: float = 0.0
    queries: list[str] = field(default_factory=list)


class SearchAnalytics:
    """
    Search analytics service.

    Tracks user behavior to improve search quality:
    - Popular queries for autocomplete
    - Click-through rates for ranking
    - User engagement metrics
    """

    def __init__(self):
        """Initialize analytics service."""
        self._search_events: list[SearchEvent] = []
        self._click_events: list[ClickEvent] = []

        # Aggregated stats
        self._query_stats: dict[str, QueryStats] = {}
        self._paper_stats: dict[str, PaperStats] = {}

        # Time-windowed data (last 24h, 7d, 30d)
        self._window_hours = [24, 168, 720]  # 24h, 7d, 30d

        logger.info("Search analytics initialized")

    def log_search(
        self,
        query: str,
        results_count: int,
        user_id: int | None = None,
        session_id: str | None = None,
    ) -> None:
        """
        Log a search event.

        Args:
            query: Search query
            results_count: Number of results returned
            user_id: Optional user ID
            session_id: Optional session ID
        """
        event = SearchEvent(
            query=query.lower().strip(),
            user_id=user_id,
            results_count=results_count,
            session_id=session_id,
        )
        self._search_events.append(event)

        # Update query stats
        stats = self._get_or_create_query_stats(event.query)
        stats.search_count += 1
        stats.last_searched = event.timestamp
        stats.avg_results_count = (
            stats.avg_results_count * (stats.search_count - 1) + results_count
        ) / stats.search_count

        # Keep only recent events (last 30 days)
        cutoff = time.time() - 30 * 24 * 3600
        self._search_events = [e for e in self._search_events if e.timestamp > cutoff]

    def log_click(
        self,
        query: str,
        paper_id: str,
        position: int,
        user_id: int | None = None,
        session_id: str | None = None,
    ) -> None:
        """
        Log a paper click event.

        Args:
            query: Search query
            paper_id: Paper identifier (DOI or arXiv ID)
            position: Position in search results
            user_id: Optional user ID
            session_id: Optional session ID
        """
        event = ClickEvent(
            query=query.lower().strip(),
            paper_id=paper_id,
            position=position,
            user_id=user_id,
            session_id=session_id,
        )
        self._click_events.append(event)

        # Update query stats
        stats = self._get_or_create_query_stats(event.query)
        stats.click_count += 1
        # Update average position
        total_clicks = stats.click_count
        stats.avg_click_position = (
            stats.avg_click_position * (total_clicks - 1) + position
        ) / total_clicks
        # Update CTR
        if stats.search_count > 0:
            stats.ctr = stats.click_count / stats.search_count

        # Update paper stats
        paper_stats = self._get_or_create_paper_stats(paper_id)
        paper_stats.click_count += 1
        paper_stats.last_clicked = event.timestamp
        # Update average position
        total = paper_stats.click_count
        paper_stats.avg_position = (paper_stats.avg_position * (total - 1) + position) / total
        if event.query not in paper_stats.queries:
            paper_stats.queries.append(event.query)

        # Keep only recent events (last 30 days)
        cutoff = time.time() - 30 * 24 * 3600
        self._click_events = [e for e in self._click_events if e.timestamp > cutoff]

    def get_popular_queries(
        self,
        limit: int = 10,
        hours: int = 24,
    ) -> list[QueryStats]:
        """
        Get popular queries in time window.

        Args:
            limit: Maximum number of queries
            hours: Time window in hours

        Returns:
            List of QueryStats sorted by search count
        """
        cutoff = time.time() - hours * 3600

        # Aggregate recent searches
        recent_counts: dict[str, int] = defaultdict(int)
        for event in self._search_events:
            if event.timestamp > cutoff:
                recent_counts[event.query] += 1

        # Sort by count
        sorted_queries = sorted(recent_counts.items(), key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for query, count in sorted_queries[:limit]:
            stats = self._query_stats.get(query)
            if stats:
                results.append(stats)
            else:
                results.append(QueryStats(query=query, search_count=count))

        return results

    def get_click_through_rates(
        self,
        limit: int = 10,
        hours: int = 24,
    ) -> list[QueryStats]:
        """
        Get queries with highest click-through rates.

        Args:
            limit: Maximum number of queries
            hours: Time window in hours

        Returns:
            List of QueryStats sorted by CTR
        """
        cutoff = time.time() - hours * 3600

        # Aggregate recent clicks
        recent_clicks: dict[str, int] = defaultdict(int)
        for event in self._click_events:
            if event.timestamp > cutoff:
                recent_clicks[event.query] += 1

        # Calculate CTR
        results = []
        for stats in self._query_stats.values():
            if stats.search_count > 0:
                # Recalculate CTR for time window
                clicks = recent_clicks.get(stats.query, 0)
                stats.ctr = clicks / stats.search_count
                results.append(stats)

        # Sort by CTR
        results.sort(key=lambda x: x.ctr, reverse=True)

        return results[:limit]

    def get_popular_papers(
        self,
        limit: int = 10,
        hours: int = 24,
    ) -> list[PaperStats]:
        """
        Get most clicked papers in time window.

        Args:
            limit: Maximum number of papers
            hours: Time window in hours

        Returns:
            List of PaperStats sorted by click count
        """
        cutoff = time.time() - hours * 3600

        # Aggregate recent clicks
        recent_clicks: dict[str, int] = defaultdict(int)
        for event in self._click_events:
            if event.timestamp > cutoff:
                recent_clicks[event.paper_id] += 1

        # Sort by count
        sorted_papers = sorted(recent_clicks.items(), key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for paper_id, count in sorted_papers[:limit]:
            stats = self._paper_stats.get(paper_id)
            if stats:
                results.append(stats)
            else:
                results.append(PaperStats(paper_id=paper_id, click_count=count))

        return results

    def get_suggestions(
        self,
        prefix: str,
        limit: int = 5,
    ) -> list[str]:
        """
        Get query suggestions based on prefix.

        Args:
            prefix: Query prefix
            limit: Maximum suggestions

        Returns:
            List of suggested queries
        """
        prefix_lower = prefix.lower().strip()

        # Find matching queries
        matches = []
        for stats in self._query_stats.values():
            if stats.query.startswith(prefix_lower):
                matches.append((stats.query, stats.search_count))

        # Sort by popularity
        matches.sort(key=lambda x: x[1], reverse=True)

        return [query for query, _ in matches[:limit]]

    def get_stats_summary(self, hours: int = 24) -> dict:
        """
        Get analytics summary.

        Args:
            hours: Time window

        Returns:
            Dictionary with summary statistics
        """
        cutoff = time.time() - hours * 3600

        # Count recent events
        recent_searches = sum(1 for e in self._search_events if e.timestamp > cutoff)
        recent_clicks = sum(1 for e in self._click_events if e.timestamp > cutoff)

        # Calculate metrics
        ctr = recent_clicks / recent_searches if recent_searches > 0 else 0
        avg_results = 0
        if self._search_events:
            recent = [e for e in self._search_events if e.timestamp > cutoff]
            if recent:
                avg_results = sum(e.results_count for e in recent) / len(recent)

        return {
            "time_window_hours": hours,
            "total_searches": recent_searches,
            "total_clicks": recent_clicks,
            "click_through_rate": round(ctr, 3),
            "avg_results_per_search": round(avg_results, 1),
            "unique_queries": len(
                set(e.query for e in self._search_events if e.timestamp > cutoff)
            ),
        }

    def _get_or_create_query_stats(self, query: str) -> QueryStats:
        """Get or create query stats."""
        if query not in self._query_stats:
            self._query_stats[query] = QueryStats(query=query)
        return self._query_stats[query]

    def _get_or_create_paper_stats(self, paper_id: str) -> PaperStats:
        """Get or create paper stats."""
        if paper_id not in self._paper_stats:
            self._paper_stats[paper_id] = PaperStats(paper_id=paper_id)
        return self._paper_stats[paper_id]


# Module-level singleton
_search_analytics: SearchAnalytics | None = None


def get_search_analytics() -> SearchAnalytics:
    """Get the singleton SearchAnalytics instance."""
    global _search_analytics
    if _search_analytics is None:
        _search_analytics = SearchAnalytics()
    return _search_analytics
