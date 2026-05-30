from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from schemas.paper import PaperDTO
from schemas.search import SearchFilters


def is_retryable_error(exception: BaseException) -> bool:
    """Check if an exception should trigger a retry."""
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on 429 (rate limit), 500, 502, 503, 504 (server errors)
        return exception.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exception, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    return False


class BaseConnector(ABC):
    name: str
    base_url: str
    rate_limit_per_sec: float = 1.0
    requires_api_key: bool = False

    def __init__(self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None):
        self.api_key = api_key
        self.http = http_client

    @abstractmethod
    async def search(self, query: str, filters: SearchFilters, limit: int = 25, offset: int = 0) -> tuple[list[PaperDTO], int]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_doi(self, doi: str) -> PaperDTO | None:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> PaperDTO:
        raise NotImplementedError

    async def handle_rate_limit(self) -> None:
        return None

    async def health_check(self) -> bool:
        return True

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def _get_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        if self.http is None:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(url, **kwargs)
        else:
            response = await self.http.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
