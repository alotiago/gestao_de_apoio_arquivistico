"""Rate limiting simples em memória para endpoints da API."""

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """Aplica limite de requisições por janela para rotas /api/v1."""

    def __init__(self, app, limit_per_window: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limit_per_window = limit_per_window
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    @staticmethod
    def _request_identity(request: Request) -> str:
        auth = request.headers.get("authorization")
        if auth:
            return auth
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        identity = self._request_identity(request)
        now = time.time()
        bucket = self._buckets[identity]

        while bucket and (now - bucket[0]) >= self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.limit_per_window:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit excedido para a janela atual"},
                headers={
                    "X-RateLimit-Limit": str(self.limit_per_window),
                    "X-RateLimit-Remaining": "0",
                },
            )

        bucket.append(now)
        response = await call_next(request)
        remaining = max(0, self.limit_per_window - len(bucket))
        response.headers["X-RateLimit-Limit"] = str(self.limit_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
