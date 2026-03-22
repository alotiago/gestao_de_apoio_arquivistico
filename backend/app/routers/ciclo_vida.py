"""
Router EP4: Ciclo de Vida — Jobs de Retenção e Workflows.
"""

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.ciclo_vida import EventoInterno, JobRetencao, SeloEvidencia, WorkflowTarefa
from app.models.ttd import LegalHold, OrdemDestinacao, RegraRetencao
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()
settings = get_settings()


# ===== Schemas =====

class WorkflowTarefaResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    estado: str
    item_id: uuid.UUID
    item_tipo: str
    atribuido_a: uuid.UUID | None
    sla_horas: int
    comentario: str | None
    escalado: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class WorkflowTransicao(BaseModel):
    novo_estado: str  # em_avaliacao, aprovado, rejeitado, executado
    comentario: str | None = None


class JobRetencaoResponse(BaseModel):
    id: uuid.UUID
    janela_inicio: datetime
    janela_fim: datetime
    status: str
    total_analisados: int
    total_ordens: int
    idempotency_key: str
    log_execucao: dict = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None
    model_config = {"from_attributes": True}


class JobRetencaoCreate(BaseModel):
    janela_inicio: datetime
    janela_fim: datetime
    idempotency_key: str | None = None


class SeloEvidenciaCreate(BaseModel):
    entidade: str  # job_retencao, workflow_tarefa, ordem_destinacao
    entidade_id: uuid.UUID
    razao: str
    contexto: dict = Field(default_factory=dict)


class SeloEvidenciaResponse(BaseModel):
    id: uuid.UUID
    entidade: str
    entidade_id: uuid.UUID
    razao: str
    criado_por: uuid.UUID
    hash_selo: str
    carimbo_tempo: datetime
    metadados: dict
    created_at: datetime
    model_config = {"from_attributes": True}


class EventoInternoCreate(BaseModel):
    tipo: str
    origem: str
    referencia_id: uuid.UUID | None = None
    payload: dict = Field(default_factory=dict)


class EventoInternoResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    origem: str
    referencia_id: uuid.UUID | None
    payload: dict
    assinatura: str
    status: str
    tentativas: int
    proxima_tentativa: datetime | None
    enviado_em: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


def _mapear_tipo_ordem(destinacao_final: str) -> str:
    mapping = {
        "eliminacao": "eliminacao",
        "guarda_permanente": "recolhimento",
        "microfilmagem": "transferencia",
    }
    return mapping.get(destinacao_final, "transferencia")


def _modelo_por_entidade(entidade: str) -> type[object] | None:
    mapping: dict[str, type[object]] = {
        "job_retencao": JobRetencao,
        "workflow_tarefa": WorkflowTarefa,
        "ordem_destinacao": OrdemDestinacao,
    }
    return mapping.get(entidade)


def _snapshot_entidade(item: object) -> dict:
    if isinstance(item, JobRetencao):
        return {
            "id": str(item.id),
            "status": item.status,
            "janela_inicio": item.janela_inicio.isoformat(),
            "janela_fim": item.janela_fim.isoformat(),
            "total_analisados": item.total_analisados,
            "total_ordens": item.total_ordens,
            "idempotency_key": item.idempotency_key,
        }

    if isinstance(item, WorkflowTarefa):
        return {
            "id": str(item.id),
            "tipo": item.tipo,
            "estado": item.estado,
            "item_id": str(item.item_id),
            "item_tipo": item.item_tipo,
            "sla_horas": item.sla_horas,
            "comentario": item.comentario,
        }

    if isinstance(item, OrdemDestinacao):
        return {
            "id": str(item.id),
            "tipo": item.tipo,
            "status": item.status,
            "aprovador_1_id": str(item.aprovador_1_id) if item.aprovador_1_id else None,
            "aprovador_2_id": str(item.aprovador_2_id) if item.aprovador_2_id else None,
            "hash_termo": item.hash_termo,
        }

    return {}


def _assinar_payload_evento(payload: dict) -> str:
    payload_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def _novo_evento_interno(
    *,
    tipo: str,
    origem: str,
    referencia_id: uuid.UUID | None,
    payload: dict,
) -> EventoInterno:
    assinatura = _assinar_payload_evento(payload)
    return EventoInterno(
        tipo=tipo,
        origem=origem,
        referencia_id=referencia_id,
        payload=payload,
        assinatura=assinatura,
        status="enviado",
        tentativas=1,
        enviado_em=datetime.now(UTC),
    )


def _registrar_log_job(
    job: JobRetencao,
    *,
    status_execucao: str,
    mensagem: str,
    ordens_geradas: int,
) -> None:
    log = job.log_execucao or {}
    execucoes = list(log.get("execucoes", []))
    ordens_ids = list(log.get("ordens_geradas_ids", []))

    hash_anterior = execucoes[-1].get("hash_atual") if execucoes else None
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "status": status_execucao,
        "mensagem": mensagem,
        "total_analisados": job.total_analisados,
        "total_ordens": job.total_ordens,
        "ordens_geradas": ordens_geradas,
        "hash_anterior": hash_anterior,
    }
    hash_atual = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    payload["hash_atual"] = hash_atual
    execucoes.append(payload)
    job.log_execucao = {
        "execucoes": execucoes,
        "ordens_geradas_ids": ordens_ids,
    }


# ===== Endpoints — Workflows =====

@router.get("/workflows", response_model=list[WorkflowTarefaResponse])
async def listar_workflows(
    estado: str | None = None,
    tipo: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar tarefas de workflow (US-031)."""
    query = select(WorkflowTarefa)
    if estado:
        query = query.where(WorkflowTarefa.estado == estado)
    if tipo:
        query = query.where(WorkflowTarefa.tipo == tipo)
    result = await db.execute(query.order_by(WorkflowTarefa.created_at.desc()))
    return result.scalars().all()


@router.patch("/workflows/{tarefa_id}/transicao", response_model=WorkflowTarefaResponse)
async def transicionar_workflow(
    tarefa_id: uuid.UUID,
    data: WorkflowTransicao,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Avançar estado do workflow: Pendente → Avaliação → Aprovado/Rejeitado → Executado (US-031)."""
    tarefa = await db.get(WorkflowTarefa, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    # Validar transições válidas
    transicoes_validas = {
        "pendente": ["em_avaliacao"],
        "em_avaliacao": ["aprovado", "rejeitado"],
        "aprovado": ["executado"],
        "rejeitado": ["pendente"],  # Permite re-submissão
    }

    estados_permitidos = transicoes_validas.get(tarefa.estado, [])
    if data.novo_estado not in estados_permitidos:
        raise HTTPException(
            status_code=400,
            detail=f"Transição inválida: {tarefa.estado} → {data.novo_estado}. Permitidos: {estados_permitidos}",
        )

    tarefa.estado = data.novo_estado
    tarefa.comentario = data.comentario
    tarefa.atribuido_a = current_user.id

    if data.novo_estado == "aprovado":
        evento_payload = {
            "workflow_id": str(tarefa.id),
            "item_id": str(tarefa.item_id),
            "item_tipo": tarefa.item_tipo,
            "estado": tarefa.estado,
            "comentario": tarefa.comentario,
            "usuario_id": str(current_user.id),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        db.add(
            _novo_evento_interno(
                tipo="workflow.aprovado",
                origem="ciclo_vida",
                referencia_id=tarefa.id,
                payload=evento_payload,
            )
        )

    await db.flush()
    await db.refresh(tarefa)
    return tarefa


# ===== Endpoints — Jobs de Retenção =====

@router.get("/jobs", response_model=list[JobRetencaoResponse])
async def listar_jobs(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar jobs de retenção (US-030)."""
    query = select(JobRetencao)
    if status_filter:
        query = query.where(JobRetencao.status == status_filter)
    result = await db.execute(query.order_by(JobRetencao.created_at.desc()))
    return result.scalars().all()


@router.post("/jobs", response_model=JobRetencaoResponse, status_code=status.HTTP_201_CREATED)
async def agendar_job_retencao(
    data: JobRetencaoCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agendar janela de retenção com chave de idempotência (US-030)."""
    if data.janela_fim <= data.janela_inicio:
        raise HTTPException(status_code=400, detail="janela_fim deve ser maior que janela_inicio")

    idempotency_key = data.idempotency_key or (
        f"{data.janela_inicio.astimezone(UTC).isoformat()}::{data.janela_fim.astimezone(UTC).isoformat()}"
    )

    existente_result = await db.execute(select(JobRetencao).where(JobRetencao.idempotency_key == idempotency_key))
    existente = existente_result.scalar_one_or_none()
    if not existente:
        todos_jobs = (await db.execute(select(JobRetencao))).scalars().all()
        existente = next((item for item in todos_jobs if item.idempotency_key == idempotency_key), None)
    if existente:
        response.status_code = status.HTTP_200_OK
        return existente

    job = JobRetencao(
        janela_inicio=data.janela_inicio,
        janela_fim=data.janela_fim,
        status="agendado",
        total_analisados=0,
        total_ordens=0,
        idempotency_key=idempotency_key,
        log_execucao={"execucoes": [], "ordens_geradas_ids": []},
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


@router.post("/jobs/{job_id}/executar", response_model=JobRetencaoResponse)
async def executar_job_retencao(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executar (ou reprocessar) um job de retenção sem duplicar ordens (US-030)."""
    job = await db.get(JobRetencao, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    log = job.log_execucao or {}
    ordens_geradas_ids = list(log.get("ordens_geradas_ids", []))
    if job.status == "concluido":
        _registrar_log_job(
            job,
            status_execucao="sucesso",
            mensagem="Reprocessamento idempotente executado sem duplicação de ordens",
            ordens_geradas=0,
        )
        await db.flush()
        await db.refresh(job)
        return job

    job.status = "executando"
    await db.flush()

    regras_result = await db.execute(select(RegraRetencao))
    regras = regras_result.scalars().all()
    holds_result = await db.execute(select(LegalHold).where(LegalHold.status == "ativo"))
    holds_ativos = holds_result.scalars().all()
    niveis_com_hold = {hold.pcd_nivel_id for hold in holds_ativos}

    novas_ordens: list[OrdemDestinacao] = []
    for regra in regras:
        if regra.pcd_nivel_id in niveis_com_hold:
            continue

        ordem = OrdemDestinacao(
            tipo=_mapear_tipo_ordem(regra.destinacao_final),
            status="pendente",
            items=[
                {
                    "regra_retencao_id": str(regra.id),
                    "pcd_nivel_id": str(regra.pcd_nivel_id),
                    "destinacao_final": regra.destinacao_final,
                }
            ],
        )
        db.add(ordem)
        novas_ordens.append(ordem)

    await db.flush()

    job.total_analisados = len(regras)
    if ordens_geradas_ids:
        job.total_ordens = len(ordens_geradas_ids)
    else:
        ordens_geradas_ids = [str(ordem.id) for ordem in novas_ordens]
        job.total_ordens = len(ordens_geradas_ids)
    job.status = "concluido"
    job.completed_at = datetime.now(UTC)

    job.log_execucao = {
        "execucoes": list((job.log_execucao or {}).get("execucoes", [])),
        "ordens_geradas_ids": ordens_geradas_ids,
    }
    _registrar_log_job(
        job,
        status_execucao="sucesso",
        mensagem="Execução concluída com processamento idempotente",
        ordens_geradas=len(novas_ordens),
    )

    await db.flush()
    await db.refresh(job)
    return job


@router.patch("/jobs/{job_id}/cancelar", response_model=JobRetencaoResponse)
async def cancelar_job_retencao(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancelar job agendado antes da execução."""
    job = await db.get(JobRetencao, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    if job.status != "agendado":
        raise HTTPException(status_code=400, detail="Somente jobs agendados podem ser cancelados")

    job.status = "cancelado"
    _registrar_log_job(
        job,
        status_execucao="cancelado",
        mensagem="Job cancelado manualmente",
        ordens_geradas=0,
    )
    await db.flush()
    await db.refresh(job)
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_job_retencao(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir job apenas quando não concluído/executado."""
    job = await db.get(JobRetencao, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    if job.status in {"executando", "concluido"}:
        raise HTTPException(status_code=400, detail="Job concluído/em execução não pode ser excluído")

    await db.delete(job)
    await db.flush()
    return None


# ===== Endpoints — Selo de Evidência e Pacote =====

@router.get("/selos", response_model=list[SeloEvidenciaResponse])
async def listar_selos(
    entidade: str | None = None,
    entidade_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar selos de evidência (US-032)."""
    query = select(SeloEvidencia)
    if entidade:
        query = query.where(SeloEvidencia.entidade == entidade)
    if entidade_id:
        query = query.where(SeloEvidencia.entidade_id == entidade_id)
    result = await db.execute(query.order_by(SeloEvidencia.created_at.desc()))
    return result.scalars().all()


@router.post("/selos", response_model=SeloEvidenciaResponse, status_code=status.HTTP_201_CREATED)
async def criar_selo_evidencia(
    data: SeloEvidenciaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gerar selo de evidência com hash, carimbo de tempo, usuário e razão (US-032)."""
    model = _modelo_por_entidade(data.entidade)
    if not model:
        raise HTTPException(status_code=400, detail=f"Entidade inválida: {data.entidade}")

    entidade = await db.get(model, data.entidade_id)
    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade alvo não encontrada")

    carimbo_tempo = datetime.now(UTC)
    snapshot = _snapshot_entidade(entidade)
    payload_hash = {
        "entidade": data.entidade,
        "entidade_id": str(data.entidade_id),
        "razao": data.razao,
        "criado_por": str(current_user.id),
        "carimbo_tempo": carimbo_tempo.isoformat(),
        "snapshot": snapshot,
        "contexto": data.contexto,
    }
    hash_selo = hashlib.sha256(json.dumps(payload_hash, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    selo = SeloEvidencia(
        entidade=data.entidade,
        entidade_id=data.entidade_id,
        razao=data.razao,
        criado_por=current_user.id,
        hash_selo=hash_selo,
        carimbo_tempo=carimbo_tempo,
        metadados={
            "contexto": data.contexto,
            "snapshot": snapshot,
        },
    )
    db.add(selo)
    await db.flush()
    await db.refresh(selo)
    return selo


@router.delete("/selos/{selo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_selo_evidencia(
    selo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir selo apenas em rascunho; selos finalizados são imutáveis."""
    selo = await db.get(SeloEvidencia, selo_id)
    if not selo:
        raise HTTPException(status_code=404, detail="Selo não encontrado")

    status_selo = str((selo.metadados or {}).get("status_selo", "finalizado"))
    if status_selo != "rascunho":
        raise HTTPException(status_code=400, detail="Somente selos em rascunho podem ser excluídos")

    await db.delete(selo)
    await db.flush()
    return None


@router.get("/auditoria/pacote")
async def consultar_pacote_auditoria(
    entidade: str | None = None,
    entidade_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gerar pacote JSON com trilhas e metadados de auditoria (US-032)."""
    if entidade and not _modelo_por_entidade(entidade):
        raise HTTPException(status_code=400, detail=f"Entidade inválida: {entidade}")

    query_selos = select(SeloEvidencia)
    if entidade:
        query_selos = query_selos.where(SeloEvidencia.entidade == entidade)
    if entidade_id:
        query_selos = query_selos.where(SeloEvidencia.entidade_id == entidade_id)
    selos = (await db.execute(query_selos.order_by(SeloEvidencia.created_at.desc()))).scalars().all()

    workflows: list[WorkflowTarefa] = []
    jobs: list[JobRetencao] = []
    ordens: list[OrdemDestinacao] = []

    if entidade in {None, "workflow_tarefa"}:
        query = select(WorkflowTarefa)
        if entidade == "workflow_tarefa" and entidade_id:
            query = query.where(WorkflowTarefa.id == entidade_id)
        workflows = (await db.execute(query.order_by(WorkflowTarefa.updated_at.desc()))).scalars().all()

    if entidade in {None, "job_retencao"}:
        query = select(JobRetencao)
        if entidade == "job_retencao" and entidade_id:
            query = query.where(JobRetencao.id == entidade_id)
        jobs = (await db.execute(query.order_by(JobRetencao.created_at.desc()))).scalars().all()

    if entidade in {None, "ordem_destinacao"}:
        query = select(OrdemDestinacao)
        if entidade == "ordem_destinacao" and entidade_id:
            query = query.where(OrdemDestinacao.id == entidade_id)
        ordens = (await db.execute(query.order_by(OrdemDestinacao.created_at.desc()))).scalars().all()

    return {
        "gerado_em": datetime.now(UTC).isoformat(),
        "gerado_por": str(current_user.id),
        "filtros": {
            "entidade": entidade,
            "entidade_id": str(entidade_id) if entidade_id else None,
        },
        "resumo": {
            "selos": len(selos),
            "workflows": len(workflows),
            "jobs": len(jobs),
            "ordens": len(ordens),
        },
        "trilhas": {
            "selos": [
                {
                    "id": str(selo.id),
                    "entidade": selo.entidade,
                    "entidade_id": str(selo.entidade_id),
                    "razao": selo.razao,
                    "hash_selo": selo.hash_selo,
                    "carimbo_tempo": selo.carimbo_tempo.isoformat(),
                    "metadados": selo.metadados,
                }
                for selo in selos
            ],
            "workflows": [
                {
                    "id": str(workflow.id),
                    "tipo": workflow.tipo,
                    "estado": workflow.estado,
                    "item_id": str(workflow.item_id),
                    "item_tipo": workflow.item_tipo,
                    "updated_at": workflow.updated_at.isoformat(),
                }
                for workflow in workflows
            ],
            "jobs": [
                {
                    "id": str(job.id),
                    "status": job.status,
                    "idempotency_key": job.idempotency_key,
                    "total_analisados": job.total_analisados,
                    "total_ordens": job.total_ordens,
                    "log_execucao": job.log_execucao,
                }
                for job in jobs
            ],
            "ordens": [
                {
                    "id": str(ordem.id),
                    "tipo": ordem.tipo,
                    "status": ordem.status,
                    "hash_termo": ordem.hash_termo,
                    "carimbo_tempo": ordem.carimbo_tempo.isoformat() if ordem.carimbo_tempo else None,
                }
                for ordem in ordens
            ],
        },
    }


# ===== Endpoints — Eventos Internos =====

@router.get("/eventos", response_model=list[EventoInternoResponse])
async def listar_eventos_internos(
    tipo: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar eventos internos assinados (US-051)."""
    query = select(EventoInterno)
    if tipo:
        query = query.where(EventoInterno.tipo == tipo)
    if status_filter:
        query = query.where(EventoInterno.status == status_filter)
    result = await db.execute(query.order_by(EventoInterno.created_at.desc()))
    return result.scalars().all()


@router.post("/eventos/disparar", response_model=EventoInternoResponse, status_code=status.HTTP_201_CREATED)
async def disparar_evento_interno(
    data: EventoInternoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disparar evento interno com payload assinado (US-051)."""
    payload = {
        **data.payload,
        "triggered_by": str(current_user.id),
        "triggered_at": datetime.now(UTC).isoformat(),
    }
    evento = _novo_evento_interno(
        tipo=data.tipo,
        origem=data.origem,
        referencia_id=data.referencia_id,
        payload=payload,
    )
    db.add(evento)
    await db.flush()
    await db.refresh(evento)
    return evento


@router.post("/eventos/{evento_id}/retry", response_model=EventoInternoResponse)
async def retry_evento_interno(
    evento_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reprocessar evento interno com nova assinatura e incremento de tentativa (US-051)."""
    evento = await db.get(EventoInterno, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    evento.tentativas += 1
    evento.enviado_em = datetime.now(UTC)
    evento.proxima_tentativa = None
    evento.status = "enviado"
    evento.assinatura = _assinar_payload_evento(evento.payload)

    await db.flush()
    await db.refresh(evento)
    return evento
