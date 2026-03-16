"""Middleware para aplicar headers básicos de hardening HTTP."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Aplica headers defensivos sem interferir no fluxo da API."""

    DOCS_PATHS = {
        "/",
        "/docs",
        "/docs/swagger-initializer.js",
        "/openapi.json",
        "/redoc",
        "/robots.txt",
        "/sitemap.xml",
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), geolocation=(), microphone=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Embedder-Policy", "credentialless")

        if request.url.path == "/docs":
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; "
                "img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self' data:; connect-src 'self'",
            )
        else:
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
            )

        if request.url.path in self.DOCS_PATHS:
            response.headers.setdefault("Cache-Control", "no-store")

        return response