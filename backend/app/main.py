"""
FastAPI Application — Gestão de Apoio Arquivístico
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.middlewares.observability import ObservabilityMiddleware
from app.middlewares.rate_limit import InMemoryRateLimitMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware
from fastapi import Depends

from app.routers import auth, roteiros, pcd, ttd, ciclo_vida, governanca, admin, health, integracao, dados_migracao, conhecimento, portal, relatorios
from app.routers.auth import require_internal

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle."""
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} — Iniciando...")
    print(f"📦 Ambiente: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    yield
    # Shutdown
    print("🛑 Desligando aplicação...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para gestão documental com entrevistas assistidas, PCD, TTD e ciclo de vida.",
    docs_url=None,
    redoc_url="/redoc",
    lifespan=lifespan,
)

swagger_static_dir = Path(__file__).parent / "static" / "swagger-ui"
app.mount("/_static/swagger-ui", StaticFiles(directory=str(swagger_static_dir)), name="swagger-ui")

# ===== Middleware =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ObservabilityMiddleware)

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        InMemoryRateLimitMiddleware,
        limit_per_window=settings.RATE_LIMIT_PER_WINDOW,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )


@app.get("/docs", include_in_schema=False)
async def custom_swagger_docs() -> HTMLResponse:
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>Swagger UI</title>
    <link rel=\"icon\" type=\"image/png\" href=\"/_static/swagger-ui/favicon-32x32.png\" sizes=\"32x32\" />
    <link rel=\"stylesheet\" type=\"text/css\" href=\"/_static/swagger-ui/swagger-ui.css\" />
</head>
<body>
    <div id=\"swagger-ui\"></div>
    <script src=\"/_static/swagger-ui/swagger-ui-bundle.js\"></script>
    <script src=\"/_static/swagger-ui/swagger-ui-standalone-preset.js\"></script>
    <script src=\"/docs/swagger-initializer.js\"></script>
</body>
</html>
"""
        return HTMLResponse(content=html)


@app.get("/docs/swagger-initializer.js", include_in_schema=False)
async def swagger_initializer() -> Response:
        script = """
window.onload = function () {
    window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],
        layout: 'BaseLayout'
    });
};
"""
        return Response(content=script, media_type="application/javascript")


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
        return get_swagger_ui_oauth2_redirect_html()

# ===== Routers =====
_internal = [Depends(require_internal)]

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(roteiros.router, prefix="/api/v1/roteiros", tags=["EP1 — Roteiros"], dependencies=_internal)
app.include_router(pcd.router, prefix="/api/v1/pcd", tags=["EP2 — PCD"], dependencies=_internal)
app.include_router(ttd.router, prefix="/api/v1/ttd", tags=["EP3 — TTD"], dependencies=_internal)
app.include_router(ciclo_vida.router, prefix="/api/v1/ciclo-vida", tags=["EP4 — Ciclo de Vida"], dependencies=_internal)
app.include_router(governanca.router, prefix="/api/v1/governanca", tags=["EP5 — Governança"], dependencies=_internal)
app.include_router(integracao.router, prefix="/api/v1/integracao", tags=["EP6 — Integração"], dependencies=_internal)
app.include_router(dados_migracao.router, prefix="/api/v1/dados-migracao", tags=["EP9 — Dados e Migração"], dependencies=_internal)
app.include_router(conhecimento.router, prefix="/api/v1/conhecimento", tags=["EP10 — Conhecimento"], dependencies=_internal)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administração"], dependencies=_internal)
app.include_router(relatorios.router, prefix="/api/v1/relatorios", tags=["Relatórios e Exportação"], dependencies=_internal)
app.include_router(portal.router, prefix="/api/v1/portal", tags=["Portal do Cliente"])
