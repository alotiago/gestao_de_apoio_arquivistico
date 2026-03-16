"""Router EP9: inventário, cleansing e score de qualidade para migração."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.dados_migracao import DependenciaMigracao, FaseMigracao, InventarioQualidade, OndaMigracao, RegraCleansing
from app.models.integracao import ImportacaoAcervo
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.data_quality import DEFAULT_RULES, summarize_quality

router = APIRouter()


class RegraCleansingCreate(BaseModel):
    nome: str
    tipo: str
    campo: str | None = None
    configuracao: dict = Field(default_factory=dict)
    ativo: bool = True


class RegraCleansingResponse(BaseModel):
    id: uuid.UUID
    nome: str
    tipo: str
    campo: str | None
    configuracao: dict
    ativo: bool
    criado_por: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


class InventarioScanRequest(BaseModel):
    importacao_id: uuid.UUID
    regra_ids: list[uuid.UUID] = Field(default_factory=list)
    incluir_apenas_sucesso: bool = False


class InventarioQualidadeResponse(BaseModel):
    id: uuid.UUID
    importacao_id: uuid.UUID
    total_registros: int
    score_geral: float
    score_completude: float
    score_unicidade: float
    score_conformidade: float
    status_qualidade: str
    regras_aplicadas: list[dict] = Field(default_factory=list)
    indicadores: dict = Field(default_factory=dict)
    inconsistencias: list[dict] = Field(default_factory=list)
    recomendacoes: list[str] = Field(default_factory=list)
    comparativo_anterior: dict | None
    criado_por: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


class FaseMigracaoCreate(BaseModel):
    nome: str
    ordem: int = Field(default=1, ge=1)
    rollback_script: list[str] = Field(default_factory=list)


class FaseMigracaoResponse(BaseModel):
    id: uuid.UUID
    onda_id: uuid.UUID
    nome: str
    ordem: int
    status: str
    rollback_script: list[str] = Field(default_factory=list)
    created_at: datetime
    model_config = {"from_attributes": True}


class OndaMigracaoCreate(BaseModel):
    nome: str
    unidade: str
    processo: str
    ordem: int = Field(default=1, ge=1)
    estrategia_corte: str = "ondas"
    data_corte_planejada: datetime | None = None
    inventario_id: uuid.UUID | None = None
    dependencia_ids: list[uuid.UUID] = Field(default_factory=list)
    fases: list[FaseMigracaoCreate] = Field(default_factory=list)


class OndaMigracaoStatusUpdate(BaseModel):
    status: str


class RollbackOndaRequest(BaseModel):
    fase_id: uuid.UUID | None = None
    motivo: str | None = None


class OndaMigracaoResponse(BaseModel):
    id: uuid.UUID
    nome: str
    unidade: str
    processo: str
    ordem: int
    status: str
    estrategia_corte: str
    data_corte_planejada: datetime | None
    inventario_id: uuid.UUID | None
    dependencias: list[dict] = Field(default_factory=list)
    fases: list[FaseMigracaoResponse] = Field(default_factory=list)
    historico: list[dict] = Field(default_factory=list)
    criado_por: uuid.UUID | None
    created_at: datetime


class OndaValidacaoResponse(BaseModel):
    onda_id: uuid.UUID
    pronta: bool
    status_planejamento: str
    score_qualidade: float | None
    dependencias_pendentes: list[str] = Field(default_factory=list)
    fases_pendentes: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


class RollbackOndaResponse(BaseModel):
    onda_id: uuid.UUID
    status: str
    fases_afetadas: list[str] = Field(default_factory=list)
    script: list[str] = Field(default_factory=list)
    motivo: str | None


def _regras_padrao_payload() -> list[dict]:
    return [dict(rule) for rule in DEFAULT_RULES]


async def _obter_regras_ativas(db: AsyncSession, regra_ids: list[uuid.UUID]) -> list[RegraCleansing]:
    result = await db.execute(select(RegraCleansing))
    regras = result.scalars().all()
    regras = [regra for regra in regras if regra.ativo]
    if regra_ids:
        regras = [regra for regra in regras if regra.id in set(regra_ids)]
    return regras


async def _listar_fases(db: AsyncSession, onda_id: uuid.UUID) -> list[FaseMigracao]:
    result = await db.execute(select(FaseMigracao))
    fases = [fase for fase in result.scalars().all() if fase.onda_id == onda_id]
    return sorted(fases, key=lambda item: (item.ordem, item.created_at))


async def _listar_dependencias(db: AsyncSession, onda_id: uuid.UUID) -> list[DependenciaMigracao]:
    result = await db.execute(select(DependenciaMigracao))
    dependencias = [item for item in result.scalars().all() if item.onda_id == onda_id]
    return sorted(dependencias, key=lambda item: item.created_at)


def _registrar_historico(onda: OndaMigracao, evento: str, payload: dict | None = None) -> None:
    historico = list(onda.historico or [])
    historico.append(
        {
            "evento": evento,
            "payload": payload or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    onda.historico = historico


async def _montar_onda_response(db: AsyncSession, onda: OndaMigracao) -> OndaMigracaoResponse:
    dependencias = await _listar_dependencias(db, onda.id)
    fases = await _listar_fases(db, onda.id)
    ondas_relacionadas = []
    for dependencia in dependencias:
        onda_dependente = await db.get(OndaMigracao, dependencia.depende_de_onda_id)
        ondas_relacionadas.append(
            {
                "id": str(dependencia.depende_de_onda_id),
                "nome": onda_dependente.nome if onda_dependente else str(dependencia.depende_de_onda_id),
                "status": onda_dependente.status if onda_dependente else "desconhecida",
                "tipo": dependencia.tipo,
            }
        )

    return OndaMigracaoResponse(
        id=onda.id,
        nome=onda.nome,
        unidade=onda.unidade,
        processo=onda.processo,
        ordem=onda.ordem,
        status=onda.status,
        estrategia_corte=onda.estrategia_corte,
        data_corte_planejada=onda.data_corte_planejada,
        inventario_id=onda.inventario_id,
        dependencias=ondas_relacionadas,
        fases=[FaseMigracaoResponse.model_validate(fase) for fase in fases],
        historico=list(onda.historico or []),
        criado_por=onda.criado_por,
        created_at=onda.created_at,
    )


async def _obter_score_inventario(db: AsyncSession, inventario_id: uuid.UUID | None) -> float | None:
    if not inventario_id:
        return None
    inventario = await db.get(InventarioQualidade, inventario_id)
    return inventario.score_geral if inventario else None


@router.get("/regras-cleansing", response_model=list[RegraCleansingResponse])
async def listar_regras_cleansing(
    ativo: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar regras de cleansing cadastradas para inventário de qualidade (US-080)."""
    result = await db.execute(select(RegraCleansing))
    regras = result.scalars().all()
    if ativo is not None:
        regras = [regra for regra in regras if regra.ativo is ativo]
    return sorted(regras, key=lambda item: item.created_at, reverse=True)


@router.post("/regras-cleansing", response_model=RegraCleansingResponse, status_code=status.HTTP_201_CREATED)
async def criar_regra_cleansing(
    data: RegraCleansingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar regra operacional de cleansing para scans de qualidade (US-080)."""
    tipos_suportados = {"trim", "collapse_spaces", "upper", "title_case"}
    if data.tipo not in tipos_suportados:
        raise HTTPException(status_code=400, detail=f"Tipo de regra inválido. Tipos suportados: {sorted(tipos_suportados)}")

    regra = RegraCleansing(
        nome=data.nome,
        tipo=data.tipo,
        campo=data.campo,
        configuracao=data.configuracao,
        ativo=data.ativo,
        criado_por=current_user.id,
    )
    db.add(regra)
    await db.flush()
    await db.refresh(regra)
    return regra


@router.get("/inventarios", response_model=list[InventarioQualidadeResponse])
async def listar_inventarios(
    importacao_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar histórico de inventários de qualidade gerados (US-080)."""
    result = await db.execute(select(InventarioQualidade))
    inventarios = result.scalars().all()
    if importacao_id:
        inventarios = [item for item in inventarios if item.importacao_id == importacao_id]
    return sorted(inventarios, key=lambda item: item.created_at, reverse=True)


@router.get("/inventarios/{inventario_id}", response_model=InventarioQualidadeResponse)
async def obter_inventario(
    inventario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter detalhe de um inventário específico (US-080)."""
    inventario = await db.get(InventarioQualidade, inventario_id)
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")
    return inventario


@router.post("/inventarios/scan", response_model=InventarioQualidadeResponse, status_code=status.HTTP_201_CREATED)
async def gerar_inventario_qualidade(
    data: InventarioScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executar scan de qualidade sobre acervo importado com score e recomendações (US-080)."""
    importacao = await db.get(ImportacaoAcervo, data.importacao_id)
    if not importacao:
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    resultados = list(importacao.resultados or [])
    if data.incluir_apenas_sucesso:
        resultados = [item for item in resultados if item.get("status") == "sucesso"]

    regras_cadastradas = await _obter_regras_ativas(db, data.regra_ids)
    regras_payload = [
        {
            "id": str(regra.id),
            "nome": regra.nome,
            "tipo": regra.tipo,
            "campo": regra.campo,
            "configuracao": regra.configuracao or {},
        }
        for regra in regras_cadastradas
    ] or _regras_padrao_payload()

    result = await db.execute(select(InventarioQualidade))
    anteriores = [item for item in result.scalars().all() if item.importacao_id == importacao.id]
    anterior = max(anteriores, key=lambda item: item.created_at) if anteriores else None
    previous = None
    if anterior:
        previous = {
            "score_geral": anterior.score_geral,
            "score_completude": anterior.score_completude,
            "score_unicidade": anterior.score_unicidade,
            "score_conformidade": anterior.score_conformidade,
        }

    resumo = summarize_quality(resultados, regras_payload, previous=previous)
    inventario = InventarioQualidade(
        importacao_id=importacao.id,
        total_registros=resumo["total_registros"],
        score_geral=resumo["score_geral"],
        score_completude=resumo["score_completude"],
        score_unicidade=resumo["score_unicidade"],
        score_conformidade=resumo["score_conformidade"],
        status_qualidade=resumo["status_qualidade"],
        regras_aplicadas=resumo["regras_aplicadas"],
        indicadores=resumo["indicadores"],
        inconsistencias=resumo["inconsistencias"],
        recomendacoes=resumo["recomendacoes"],
        comparativo_anterior=resumo["comparativo_anterior"],
        criado_por=current_user.id,
    )
    db.add(inventario)
    await db.flush()
    await db.refresh(inventario)
    return inventario


@router.get("/ondas", response_model=list[OndaMigracaoResponse])
async def listar_ondas_migracao(
    unidade: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar cronograma de ondas de migração com fases e dependências (US-081)."""
    result = await db.execute(select(OndaMigracao))
    ondas = result.scalars().all()
    if unidade:
        ondas = [onda for onda in ondas if onda.unidade == unidade]
    if status_filter:
        ondas = [onda for onda in ondas if onda.status == status_filter]

    ondas = sorted(ondas, key=lambda item: (item.ordem, item.data_corte_planejada or item.created_at, item.created_at))
    return [await _montar_onda_response(db, onda) for onda in ondas]


@router.post("/ondas", response_model=OndaMigracaoResponse, status_code=status.HTTP_201_CREATED)
async def criar_onda_migracao(
    data: OndaMigracaoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar onda de migração com fases padrão, dependências e vínculo ao inventário (US-081)."""
    if data.estrategia_corte not in {"ondas", "big_bang"}:
        raise HTTPException(status_code=400, detail="Estratégia de corte inválida")

    if data.inventario_id and not await db.get(InventarioQualidade, data.inventario_id):
        raise HTTPException(status_code=404, detail="Inventário de qualidade não encontrado")

    onda = OndaMigracao(
        nome=data.nome,
        unidade=data.unidade,
        processo=data.processo,
        ordem=data.ordem,
        estrategia_corte=data.estrategia_corte,
        data_corte_planejada=data.data_corte_planejada,
        inventario_id=data.inventario_id,
        criado_por=current_user.id,
        historico=[],
    )
    _registrar_historico(onda, "criada", {"ordem": data.ordem, "unidade": data.unidade, "processo": data.processo})
    db.add(onda)
    await db.flush()

    fases = data.fases or [
        FaseMigracaoCreate(nome="Preparação", ordem=1, rollback_script=["restaurar snapshot operacional"]),
        FaseMigracaoCreate(nome="Carga", ordem=2, rollback_script=["reverter lote importado", "restaurar índices"]),
        FaseMigracaoCreate(nome="Validação", ordem=3, rollback_script=["reabrir execução para conferência"]),
    ]
    for fase in fases:
        db.add(
            FaseMigracao(
                onda_id=onda.id,
                nome=fase.nome,
                ordem=fase.ordem,
                rollback_script=fase.rollback_script or [f"rollback manual da fase {fase.nome.lower()}"],
            )
        )

    for dependencia_id in data.dependencia_ids:
        if dependencia_id == onda.id:
            raise HTTPException(status_code=400, detail="Uma onda não pode depender dela mesma")
        onda_dependencia = await db.get(OndaMigracao, dependencia_id)
        if not onda_dependencia:
            raise HTTPException(status_code=404, detail=f"Onda dependente {dependencia_id} não encontrada")
        db.add(DependenciaMigracao(onda_id=onda.id, depende_de_onda_id=dependencia_id))

    await db.flush()
    await db.refresh(onda)
    return await _montar_onda_response(db, onda)


@router.patch("/ondas/{onda_id}/status", response_model=OndaMigracaoResponse)
async def atualizar_status_onda(
    onda_id: uuid.UUID,
    data: OndaMigracaoStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar status da onda e propagar conclusão para fases planejadas (US-081)."""
    onda = await db.get(OndaMigracao, onda_id)
    if not onda:
        raise HTTPException(status_code=404, detail="Onda não encontrada")

    status_validos = {"planejada", "pronta", "em_execucao", "concluida", "bloqueada", "rollback_executado"}
    if data.status not in status_validos:
        raise HTTPException(status_code=400, detail=f"Status inválido. Valores suportados: {sorted(status_validos)}")

    onda.status = data.status
    if data.status == "concluida":
        fases = await _listar_fases(db, onda.id)
        for fase in fases:
            fase.status = "concluida"

    _registrar_historico(onda, "status_atualizado", {"status": data.status, "usuario_id": str(current_user.id)})
    await db.flush()
    await db.refresh(onda)
    return await _montar_onda_response(db, onda)


@router.post("/ondas/{onda_id}/validar", response_model=OndaValidacaoResponse)
async def validar_onda_migracao(
    onda_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validar prontidão de uma onda considerando dependências, fases e score de inventário (US-081)."""
    onda = await db.get(OndaMigracao, onda_id)
    if not onda:
        raise HTTPException(status_code=404, detail="Onda não encontrada")

    score_qualidade = await _obter_score_inventario(db, onda.inventario_id)
    dependencias = await _listar_dependencias(db, onda.id)
    fases = await _listar_fases(db, onda.id)

    dependencias_pendentes: list[str] = []
    for dependencia in dependencias:
        onda_dependente = await db.get(OndaMigracao, dependencia.depende_de_onda_id)
        if onda_dependente and onda_dependente.status != "concluida":
            dependencias_pendentes.append(onda_dependente.nome)

    fases_pendentes = [fase.nome for fase in fases if fase.status not in {"concluida", "rollback_executado"}]

    pronta = not dependencias_pendentes and (score_qualidade is None or score_qualidade >= 80)
    onda.status = "pronta" if pronta else "bloqueada"
    checklist = [
        "Inventário acima do threshold mínimo" if score_qualidade is None or score_qualidade >= 80 else "Reforçar cleansing antes do corte",
        "Dependências concluídas" if not dependencias_pendentes else "Concluir ondas predecessoras",
        "Fases estruturadas no cronograma" if fases else "Cadastrar fases operacionais",
    ]
    _registrar_historico(onda, "validada", {"pronta": pronta, "score_qualidade": score_qualidade})
    await db.flush()

    return OndaValidacaoResponse(
        onda_id=onda.id,
        pronta=pronta,
        status_planejamento=onda.status,
        score_qualidade=score_qualidade,
        dependencias_pendentes=dependencias_pendentes,
        fases_pendentes=fases_pendentes,
        checklist=checklist,
    )


@router.post("/ondas/{onda_id}/rollback", response_model=RollbackOndaResponse)
async def executar_rollback_onda(
    onda_id: uuid.UUID,
    data: RollbackOndaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executar rollback total ou por fase em uma onda planejada (US-081)."""
    onda = await db.get(OndaMigracao, onda_id)
    if not onda:
        raise HTTPException(status_code=404, detail="Onda não encontrada")

    fases = await _listar_fases(db, onda.id)
    if not fases:
        raise HTTPException(status_code=400, detail="A onda não possui fases para rollback")

    fases_alvo = fases
    if data.fase_id:
        fases_alvo = [fase for fase in fases if fase.id == data.fase_id]
        if not fases_alvo:
            raise HTTPException(status_code=404, detail="Fase não encontrada para a onda informada")

    script: list[str] = []
    fases_afetadas: list[str] = []
    for fase in fases_alvo:
        fase.status = "rollback_executado"
        fases_afetadas.append(fase.nome)
        script.extend(list(fase.rollback_script or [f"rollback manual da fase {fase.nome.lower()}"]))

    onda.status = "rollback_executado"
    _registrar_historico(
        onda,
        "rollback_executado",
        {"fases": fases_afetadas, "motivo": data.motivo, "usuario_id": str(current_user.id)},
    )
    await db.flush()

    return RollbackOndaResponse(
        onda_id=onda.id,
        status=onda.status,
        fases_afetadas=fases_afetadas,
        script=script,
        motivo=data.motivo,
    )
