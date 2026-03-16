"""
Router: Health Check
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.ciclo_vida import WorkflowTarefa
from app.models.dados_migracao import InventarioQualidade, OndaMigracao
from app.models.governanca import MatrizRastreabilidade
from app.models.integracao import ImportacaoAcervo
from app.models.pcd import PcdNivel
from app.models.ttd import RegraRetencao
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.backup import backup_store
from app.services.conhecimento import knowledge_base_store
from app.services.observability import observability_store

router = APIRouter()
settings = get_settings()


class BackupSnapshotCreate(BaseModel):
    pcd_nivel_id: uuid.UUID | None = None
    regra_retencao_id: uuid.UUID | None = None


class BackupRestoreResponse(BaseModel):
    snapshot_id: str
    restaurados: dict[str, int]
    detalhes: list[str]


async def _count_model(db: AsyncSession, model: type[object]) -> int:
    result = await db.execute(select(model))
    return len(result.scalars().all())


@router.get("/health")
async def health_check():
    """Verificação de saúde da aplicação."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/", include_in_schema=False)
async def service_index():
    """Endpoint raiz para operação interna e discovery básico."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


@router.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
async def robots_txt() -> PlainTextResponse:
    """Robots mínimo para evitar 404 no baseline de segurança."""
    return PlainTextResponse("User-agent: *\nDisallow:\n")


@router.get("/sitemap.xml", response_class=Response, include_in_schema=False)
async def sitemap_xml() -> Response:
    """Sitemap mínimo para descoberta de endpoints públicos."""
    content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
  <url><loc>http://localhost:8000/</loc></url>
  <url><loc>http://localhost:8000/docs</loc></url>
  <url><loc>http://localhost:8000/health</loc></url>
  <url><loc>http://localhost:8000/ready</loc></url>
</urlset>"""
    return Response(content=content, media_type="application/xml")


@router.get("/ready")
async def readiness_check():
    """Verificação de prontidão (banco, cache, etc)."""
    # TODO: Verificar conexão com PostgreSQL, Redis, MinIO
    return {"status": "ready"}


@router.get("/metrics/summary")
async def metrics_summary():
    """Resumo de métricas operacionais e SLOs (US-070)."""
    return observability_store.summary()


@router.get("/health/smoke")
async def executar_smoke_check_operacional(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executar smoke check de operação interna por módulo (Sprint 15)."""
    checks: dict[str, dict] = {}
    failures: list[str] = []

    async def run_check(nome: str, callback):
        try:
            detalhe = await callback()
            checks[nome] = {"status": "ok", **detalhe}
        except Exception as exc:  # pragma: no cover - caminho defensivo
            checks[nome] = {"status": "fail", "erro": str(exc)}
            failures.append(nome)

    async def check_pcd():
        return {"niveis": await _count_model(db, PcdNivel)}

    async def check_ttd():
        return {"regras": await _count_model(db, RegraRetencao)}

    async def check_ciclo_vida():
        return {"workflows": await _count_model(db, WorkflowTarefa)}

    async def check_governanca():
        return {"matriz": await _count_model(db, MatrizRastreabilidade)}

    async def check_integracao():
        return {"importacoes": await _count_model(db, ImportacaoAcervo)}

    async def check_dados_migracao():
        return {
            "inventarios": await _count_model(db, InventarioQualidade),
            "ondas": await _count_model(db, OndaMigracao),
        }

    async def check_conhecimento():
        return {
            "templates": len(knowledge_base_store.search_templates(None)),
            "trilhas": len(knowledge_base_store.list_trilhas(str(current_user.id))),
        }

    async def check_observabilidade():
        summary = observability_store.summary()
        return {
            "requests_total": summary.get("requests_total", 0),
            "incidents_open": summary.get("incidents_open", 0),
            "availability_pct": summary.get("availability_pct", 100),
        }

    async def check_backup():
        return {"snapshots": len(backup_store.list_snapshots())}

    await run_check("pcd", check_pcd)
    await run_check("ttd", check_ttd)
    await run_check("ciclo_vida", check_ciclo_vida)
    await run_check("governanca", check_governanca)
    await run_check("integracao", check_integracao)
    await run_check("dados_migracao", check_dados_migracao)
    await run_check("conhecimento", check_conhecimento)
    await run_check("observabilidade", check_observabilidade)
    await run_check("backup", check_backup)

    return {
        "overall_status": "ok" if not failures else "degraded",
        "checked_at": datetime.now(UTC).isoformat(),
        "total_checks": len(checks),
        "failed_checks": failures,
        "checks": checks,
    }


@router.get("/backup/snapshots")
async def listar_backups(
    current_user: User = Depends(get_current_user),
):
    """Listar snapshots de backup incremental (US-071)."""
    return backup_store.list_snapshots()


@router.post("/backup/snapshots", status_code=status.HTTP_201_CREATED)
async def criar_backup_incremental(
    data: BackupSnapshotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar backup incremental por classe/regra para restauração parcial (US-071)."""
    if not data.pcd_nivel_id and not data.regra_retencao_id:
        raise HTTPException(status_code=400, detail="Informe ao menos um identificador para o backup")

    pcd_snapshot = None
    regra_snapshot = None

    if data.pcd_nivel_id:
        nivel = await db.get(PcdNivel, data.pcd_nivel_id)
        if not nivel:
            raise HTTPException(status_code=404, detail="Nível PCD não encontrado")
        pcd_snapshot = {
            "id": str(nivel.id),
            "pai_id": str(nivel.pai_id) if nivel.pai_id else None,
            "tipo": nivel.tipo,
            "codigo": nivel.codigo,
            "titulo": nivel.titulo,
            "descricao": nivel.descricao,
            "codigo_conarq": nivel.codigo_conarq,
            "nivel_sigilo": nivel.nivel_sigilo,
            "metadados": nivel.metadados,
            "status": nivel.status,
        }

    if data.regra_retencao_id:
        regra = await db.get(RegraRetencao, data.regra_retencao_id)
        if not regra:
            raise HTTPException(status_code=404, detail="Regra de retenção não encontrada")
        regra_snapshot = {
            "id": str(regra.id),
            "pcd_nivel_id": str(regra.pcd_nivel_id),
            "evento_inicio": regra.evento_inicio,
            "prazo_dias": regra.prazo_dias,
            "fase_corrente": regra.fase_corrente,
            "fase_intermediaria": regra.fase_intermediaria,
            "destinacao_final": regra.destinacao_final,
            "base_legal": regra.base_legal,
            "legislacao_ref": regra.legislacao_ref,
            "observacoes": regra.observacoes,
        }

    return backup_store.create_snapshot(
        {
            "escopo": {
                "pcd_nivel_id": str(data.pcd_nivel_id) if data.pcd_nivel_id else None,
                "regra_retencao_id": str(data.regra_retencao_id) if data.regra_retencao_id else None,
            },
            "pcd_snapshot": pcd_snapshot,
            "regra_snapshot": regra_snapshot,
            "criado_por": str(current_user.id),
        }
    )


@router.post("/backup/snapshots/{snapshot_id}/restore", response_model=BackupRestoreResponse)
async def restaurar_backup_parcial(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restaurar parcialmente itens por classe e/ou regra a partir de backup incremental (US-071)."""
    snapshot = backup_store.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot não encontrado")

    restaurados = {"pcd": 0, "regras": 0}
    detalhes: list[str] = []

    pcd_snapshot = snapshot.get("pcd_snapshot")
    if pcd_snapshot and not await db.get(PcdNivel, uuid.UUID(pcd_snapshot["id"])):
        db.add(
            PcdNivel(
                id=uuid.UUID(pcd_snapshot["id"]),
                pai_id=uuid.UUID(pcd_snapshot["pai_id"]) if pcd_snapshot["pai_id"] else None,
                tipo=pcd_snapshot["tipo"],
                codigo=pcd_snapshot["codigo"],
                titulo=pcd_snapshot["titulo"],
                descricao=pcd_snapshot["descricao"],
                codigo_conarq=pcd_snapshot["codigo_conarq"],
                nivel_sigilo=pcd_snapshot["nivel_sigilo"],
                metadados=pcd_snapshot["metadados"],
                status=pcd_snapshot["status"],
                filhos=[],
            )
        )
        restaurados["pcd"] += 1
        detalhes.append("Classe PCD restaurada com sucesso")

    regra_snapshot = snapshot.get("regra_snapshot")
    if regra_snapshot and not await db.get(RegraRetencao, uuid.UUID(regra_snapshot["id"])):
        db.add(
            RegraRetencao(
                id=uuid.UUID(regra_snapshot["id"]),
                pcd_nivel_id=uuid.UUID(regra_snapshot["pcd_nivel_id"]),
                evento_inicio=regra_snapshot["evento_inicio"],
                prazo_dias=regra_snapshot["prazo_dias"],
                fase_corrente=regra_snapshot["fase_corrente"],
                fase_intermediaria=regra_snapshot["fase_intermediaria"],
                destinacao_final=regra_snapshot["destinacao_final"],
                base_legal=regra_snapshot["base_legal"],
                legislacao_ref=regra_snapshot["legislacao_ref"],
                observacoes=regra_snapshot["observacoes"],
            )
        )
        restaurados["regras"] += 1
        detalhes.append("Regra de retenção restaurada com sucesso")

    await db.flush()
    return BackupRestoreResponse(snapshot_id=snapshot_id, restaurados=restaurados, detalhes=detalhes)
