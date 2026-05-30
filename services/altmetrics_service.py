"""
Altmetrics Integration for PaperLens

Provides alternative metrics (altmetrics) from social media and news:
- Twitter/X mentions
- Blog posts
- News coverage
- Wikipedia references
- Mendeley readers
- Reddit discussions

Data Sources:
- Altmetric API (https://www.altmetric.com/)
- Semantic Scholar (includes some altmetrics)
- OpenAlex (includes some social metrics)

Note: Altmetric API requires API key for full access.
Free tier available with rate limits.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from loguru import logger


@dataclass
class AltmetricsData:
    """
    Altmetrics data for a paper.

    Attributes:
        doi: Paper DOI
        score: Altmetric Attention Score (0-100+)
        rank: Percentile rank (1-100)
        sources: Breakdown by source
        mentions: Total social mentions
        readers: Mendeley readers
        captures: Bookmarks/saves
        shares: Social shares
        citations: Traditional citations
        news: News mentions
        blogs: Blog mentions
        twitter: Twitter mentions
        reddit: Reddit mentions
        wikipedia: Wikipedia references
        timestamp: When data was fetched
    """

    doi: str
    score: float = 0.0
    rank: int = 0
    sources: dict[str, int] = field(default_factory=dict)
    mentions: int = 0
    readers: int = 0
    captures: int = 0
    shares: int = 0
    citations: int = 0
    news: int = 0
    blogs: int = 0
    twitter: int = 0
    reddit: int = 0
    wikipedia: int = 0
    timestamp: float = field(default_factory=time.time)


class AltmetricsService:
    """
    Altmetrics integration service.

    Fetches alternative metrics for papers to complement traditional citations.
    Provides:
    - Social media attention scores
    - News coverage tracking
    - Open access impact metrics
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize Altmetrics service.

        Args:
            api_key: Altmetric API key (optional, free tier available)
        """
        self._api_key = api_key
        self._base_url = "https://api.altmetric.com/v1"
        self._cache: dict[str, AltmetricsData] = {}
        self._cache_ttl = 3600  # 1 hour
        self._last_fetch: dict[str, float] = {}

        # Rate limiting
        self._last_request_time = 0.0
        self._min_request_interval = 1.0  # 1 second between requests

        logger.info(
            f"Altmetrics service initialized (API key: {'configured' if api_key else 'not configured'})"
        )

    async def get_altmetrics(
        self,
        doi: str | None = None,
        arxiv_id: str | None = None,
    ) -> AltmetricsData | None:
        """
        Get altmetrics for a paper.

        Args:
            doi: Paper DOI
            arxiv_id: arXiv ID

        Returns:
            AltmetricsData or None if not available
        """
        # Build identifier
        identifier = doi or arxiv_id
        if not identifier:
            return None

        # Check cache
        cached = self._get_from_cache(identifier)
        if cached:
            return cached

        # Check rate limiting
        if not self._check_rate_limit():
            logger.debug("Altmetrics rate limit reached")
            return None

        # Fetch from API
        if doi:
            data = await self._fetch_by_doi(doi)
        else:
            data = await self._fetch_by_arxiv(arxiv_id)

        if data:
            self._put_to_cache(identifier, data)

        return data

    async def _fetch_by_doi(self, doi: str) -> AltmetricsData | None:
        """Fetch altmetrics by DOI."""
        try:
            # Clean DOI
            clean_doi = doi.strip()
            if clean_doi.startswith("https://doi.org/"):
                clean_doi = clean_doi[16:]

            url = f"{self._base_url}/doi/{clean_doi}"
            headers = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_altmetric_response(data, doi)
                elif response.status_code == 404:
                    logger.debug(f"No altmetrics found for DOI: {doi}")
                    return None
                else:
                    logger.warning(f"Altmetric API error: {response.status_code}")
                    return None

        except Exception as e:
            logger.debug(f"Failed to fetch altmetrics for DOI {doi}: {e}")
            return None

    async def _fetch_by_arxiv(self, arxiv_id: str) -> AltmetricsData | None:
        """Fetch altmetrics by arXiv ID."""
        try:
            url = f"{self._base_url}/arxiv/{arxiv_id}"
            headers = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_altmetric_response(data, arxiv_id)
                elif response.status_code == 404:
                    logger.debug(f"No altmetrics found for arXiv: {arxiv_id}")
                    return None
                else:
                    logger.warning(f"Altmetric API error: {response.status_code}")
                    return None

        except Exception as e:
            logger.debug(f"Failed to fetch altmetrics for arXiv {arxiv_id}: {e}")
            return None

    def _parse_altmetric_response(self, data: dict, identifier: str) -> AltmetricsData:
        """Parse Altmetric API response."""
        # Extract DOI
        doi = data.get("doi") or identifier

        # Extract scores
        score = data.get("score", 0.0)
        rank = data.get("rank", 0)

        # Extract source breakdown
        sources = {}
        for source_name in ["twitter", "facebook", "blogs", "news", "reddit", "wikipedia"]:
            count = (
                data.get(f"mendeley", 0) if source_name == "mendeley" else data.get(source_name, 0)
            )
            if count:
                sources[source_name] = count

        # Extract totals
        readers = data.get("readers_count", 0)
        mentions = data.get("cited_by_posts_count", 0)

        return AltmetricsData(
            doi=doi,
            score=score,
            rank=rank,
            sources=sources,
            mentions=mentions,
            readers=readers,
            captures=data.get("cited_by_msm_count", 0),
            shares=data.get("cited_by_tweeters_count", 0),
            citations=data.get("cited_by_fbwalls_count", 0),
            news=data.get("cited_by_msm_count", 0),
            blogs=data.get("cited_by_feeds_count", 0),
            twitter=data.get("cited_by_tweeters_count", 0),
            reddit=data.get("cited_by_rdts_count", 0),
            wikipedia=data.get("cited_by_wikipedia_count", 0),
        )

    def _get_from_cache(self, identifier: str) -> AltmetricsData | None:
        """Get data from cache if valid."""
        if identifier not in self._cache:
            return None

        last_fetch = self._last_fetch.get(identifier, 0)
        if time.time() - last_fetch > self._cache_ttl:
            del self._cache[identifier]
            del self._last_fetch[identifier]
            return None

        return self._cache[identifier]

    def _put_to_cache(self, identifier: str, data: AltmetricsData) -> None:
        """Put data in cache."""
        self._cache[identifier] = data
        self._last_fetch[identifier] = time.time()

        # Evict old entries if cache is too large
        if len(self._cache) > 1000:
            oldest = min(self._last_fetch.items(), key=lambda x: x[1])
            del self._cache[oldest[0]]
            del self._last_fetch[oldest[0]]

    def _check_rate_limit(self) -> bool:
        """Check if we can make another request."""
        now = time.time()
        if now - self._last_request_time < self._min_request_interval:
            return False
        self._last_request_time = now
        return True

    def score_altmetrics(self, data: AltmetricsData | None) -> float:
        """
        Convert altmetrics to a 0-1 score.

        Uses Altmetric Attention Score normalization:
        - 0-1: Low attention
        - 1-10: Medium attention
        - 10-50: High attention
        - 50+: Very high attention
        """
        if data is None:
            return 0.0

        score = data.score

        # Normalize using log scale
        if score <= 0:
            return 0.0
        elif score < 1:
            return score * 0.5  # Low attention
        elif score < 10:
            return 0.5 + (score - 1) * 0.05  # 0.5 - 0.95
        else:
            return min(1.0, 0.95 + (score - 10) * 0.005)  # 0.95 - 1.0


# Module-level singleton
_altmetrics_service: AltmetricsService | None = None


def get_altmetrics_service() -> AltmetricsService:
    """Get the singleton AltmetricsService instance."""
    global _altmetrics_service
    if _altmetrics_service is None:
        try:
            from app.config import get_settings

            settings = get_settings()
            api_key = getattr(settings, "altmetric_api_key", None)
        except Exception:
            api_key = None

        _altmetrics_service = AltmetricsService(api_key=api_key)
    return _altmetrics_service
