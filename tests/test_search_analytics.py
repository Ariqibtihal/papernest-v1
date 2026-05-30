"""
Tests for Search Analytics Service.

These tests validate the search analytics functionality.
"""

from __future__ import annotations

import time
import pytest

from services.search_analytics import SearchAnalytics, get_search_analytics


class TestSearchAnalytics:
    """Test SearchAnalytics functionality."""

    def test_log_search(self):
        """Test logging a search event."""
        analytics = SearchAnalytics()

        analytics.log_search(
            query="machine learning",
            results_count=100,
            user_id=1,
        )

        assert len(analytics._search_events) == 1
        assert analytics._search_events[0].query == "machine learning"

    def test_log_click(self):
        """Test logging a click event."""
        analytics = SearchAnalytics()

        analytics.log_click(
            query="machine learning",
            paper_id="10.1234/test",
            position=3,
            user_id=1,
        )

        assert len(analytics._click_events) == 1
        assert analytics._click_events[0].paper_id == "10.1234/test"

    def test_query_stats_updated(self):
        """Test that query stats are updated on events."""
        analytics = SearchAnalytics()

        analytics.log_search(query="test query", results_count=50)
        analytics.log_click(query="test query", paper_id="123", position=1)

        stats = analytics._query_stats.get("test query")
        assert stats is not None
        assert stats.search_count == 1
        assert stats.click_count == 1
        assert stats.ctr == 1.0

    def test_popular_queries(self):
        """Test getting popular queries."""
        analytics = SearchAnalytics()

        # Log multiple searches
        for _ in range(5):
            analytics.log_search(query="popular query", results_count=10)
        analytics.log_search(query="less popular", results_count=10)

        popular = analytics.get_popular_queries(limit=5)

        assert len(popular) >= 1
        assert popular[0].query == "popular query"

    def test_get_suggestions(self):
        """Test getting query suggestions."""
        analytics = SearchAnalytics()

        analytics.log_search(query="machine learning", results_count=10)
        analytics.log_search(query="machine vision", results_count=10)
        analytics.log_search(query="deep learning", results_count=10)

        suggestions = analytics.get_suggestions("machine")

        assert len(suggestions) >= 1
        assert any("machine" in s for s in suggestions)

    def test_get_stats_summary(self):
        """Test getting analytics summary."""
        analytics = SearchAnalytics()

        analytics.log_search(query="test", results_count=10)
        analytics.log_click(query="test", paper_id="123", position=1)

        summary = analytics.get_stats_summary(hours=24)

        assert summary["total_searches"] == 1
        assert summary["total_clicks"] == 1
        assert summary["click_through_rate"] == 1.0

    def test_get_popular_papers(self):
        """Test getting popular papers."""
        analytics = SearchAnalytics()

        # Click same paper multiple times
        for _ in range(3):
            analytics.log_click(query="test", paper_id="10.1234/test", position=1)
        analytics.log_click(query="test", paper_id="10.5678/other", position=2)

        popular = analytics.get_popular_papers(limit=5)

        assert len(popular) >= 1
        assert popular[0].paper_id == "10.1234/test"

    def test_ctr_calculation(self):
        """Test click-through rate calculation."""
        analytics = SearchAnalytics()

        # 2 searches, 1 click
        analytics.log_search(query="test", results_count=10)
        analytics.log_search(query="test", results_count=10)
        analytics.log_click(query="test", paper_id="123", position=1)

        ctrs = analytics.get_click_through_rates(limit=5)

        assert len(ctrs) >= 1
        assert ctrs[0].ctr == 0.5


class TestSearchAnalyticsIntegration:
    """Integration tests for search analytics."""

    def test_get_analytics_singleton(self):
        """Test that get_search_analytics returns singleton."""
        analytics1 = get_search_analytics()
        analytics2 = get_search_analytics()

        assert analytics1 is analytics2

    def test_user_flow(self):
        """Test typical user flow."""
        analytics = SearchAnalytics()

        # User searches
        analytics.log_search(
            query="neural networks",
            results_count=250,
            user_id=1,
            session_id="abc123",
        )

        # User clicks result
        analytics.log_click(
            query="neural networks",
            paper_id="10.1234/test",
            position=3,
            user_id=1,
            session_id="abc123",
        )

        # Verify tracking
        assert len(analytics._search_events) == 1
        assert len(analytics._click_events) == 1

        # Get stats
        summary = analytics.get_stats_summary()
        assert summary["total_searches"] == 1
        assert summary["total_clicks"] == 1
