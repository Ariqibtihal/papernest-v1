from __future__ import annotations

from typing import Optional
import httpx

class HTTPClientManager:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            # Fallback if not initialized via lifespan, mainly for tests
            cls._client = httpx.AsyncClient(timeout=30, follow_redirects=True)
        return cls._client

    @classmethod
    def init_client(cls) -> None:
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=30, follow_redirects=True)

    @classmethod
    async def close_client(cls) -> None:
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
