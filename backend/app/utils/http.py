import httpx
from typing import Optional
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

class HTTPClient:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            timeout = httpx.Timeout(10.0, connect=5.0, read=30.0)
            cls._client = httpx.AsyncClient(limits=limits, timeout=timeout)
        return cls._client

    @classmethod
    async def close_client(cls):
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None

http_client = HTTPClient()
