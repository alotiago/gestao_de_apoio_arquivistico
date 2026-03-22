"""Middleware de observabilidade para captura de métricas HTTP."""

import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.services.observability import observability_store


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in {"/health", "/ready", "/metrics/summary",
                                   "/api/v1/health", "/api/v1/ready", "/api/v1/metrics/summary"}:
            return await call_next(request)

        started_at = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - started_at) * 1000
        observability_store.record(latency_ms=latency_ms, status_code=response.status_code)
        return response
