"""
Router EP2: Plano de Classificação de Documentos (PCD) — CRUD Hierárquico.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.pcd import PcdNivel, PcdVersao
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# ===== Schemas =====

class PcdNivelCreate(BaseModel):
    pai_id: uuid.UUID | None = None
    tipo: str  # funcao, atividade, serie, classe
    codigo: str
    titulo: str
    descricao: str | None = None
    codigo_conarq: str | None = None
    nivel_sigilo: str = "publico"
    metadados: dict = Field(default_factory=dict)


class PcdNivelUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    codigo_conarq: str | None = None
    nivel_sigilo: str | None = None
    metadados: dict | None = None
    status: str | None = None


class PcdNivelResponse(BaseModel):
    id: uuid.UUID
    pai_id: uuid.UUID | None
    tipo: str
    codigo: str
    titulo: str
    descricao: str | None
    codigo_conarq: str | None
    versao: int
    status: str
    nivel_sigilo: str
    metadados: dict
    created_at: datetime
    updated_at: datetime
    filhos: list["PcdNivelResponse"] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class VersaoCreate(BaseModel):
    justificativa: str


class VersaoResponse(BaseModel):
    id: uuid.UUID
    pcd_nivel_id: uuid.UUID
    versao: int
    dados_snapshot: dict
    justificativa: str
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class VersaoStatusUpdate(BaseModel):
    status: str


class ControleSegurancaUpdate(BaseModel):
    metadados_obrigatorios: list[str] = Field(default_factory=list)
    permissoes_por_papel: dict[str, list[str]] = Field(default_factory=dict)
    unidades_autorizadas: list[str] = Field(default_factory=list)


class ControleSegurancaResponse(BaseModel):
    pcd_nivel_id: uuid.UUID
    metadados_obrigatorios: list[str] = Field(default_factory=list)
    permissoes_por_papel: dict[str, list[str]] = Field(default_factory=dict)
    unidades_autorizadas: list[str] = Field(default_factory=list)


class ValidarMetadadosRequest(BaseModel):
    metadados_documento: dict = Field(default_factory=dict)


class ValidarMetadadosResponse(BaseModel):
    pcd_nivel_id: uuid.UUID
    valido: bool
    faltantes: list[str] = Field(default_factory=list)


class ValidarAcessoRequest(BaseModel):
    acao: str = "ler"


class ValidarAcessoResponse(BaseModel):
    pcd_nivel_id: uuid.UUID
    permitido: bool
    acao: str
    papel: str
    unidade_usuario: str | None
    nivel_sigilo: str
    motivos: list[str] = Field(default_factory=list)


def _normalizar_metadados_obrigatorios(campos: list[str]) -> list[str]:
    vistos: set[str] = set()
    normalizados: list[str] = []
    for campo in campos:
        nome = campo.strip()
        if not nome or nome in vistos:
            continue
        vistos.add(nome)
        normalizados.append(nome)
    return normalizados


def _normalizar_permissoes_por_papel(permissoes: dict[str, list[str]]) -> dict[str, list[str]]:
    resultado: dict[str, list[str]] = {}

    for papel, acoes in permissoes.items():
        papel_normalizado = papel.strip()
        if not papel_normalizado:
            continue

        if not isinstance(acoes, list):
            raise HTTPException(status_code=400, detail=f"Permissões inválidas para papel '{papel_normalizado}'")

        acoes_vistas: set[str] = set()
        acoes_normalizadas: list[str] = []
        for acao in acoes:
            nome_acao = str(acao).strip()
            if not nome_acao or nome_acao in acoes_vistas:
                continue
            acoes_vistas.add(nome_acao)
            acoes_normalizadas.append(nome_acao)

        resultado[papel_normalizado] = acoes_normalizadas

    return resultado


def _normalizar_lista_texto(valores: list[str]) -> list[str]:
    vistos: set[str] = set()
    normalizados: list[str] = []
    for valor in valores:
        item = str(valor).strip()
        if not item or item in vistos:
            continue
        vistos.add(item)
        normalizados.append(item)
    return normalizados


def _sigilo_rank(sigilo: str) -> int:
    ranking = {
        "publico": 0,
        "interno": 1,
        "restrito": 2,
        "confidencial": 3,
        "secreto": 4,
    }
    return ranking.get(sigilo, 0)


def _sigilos_permitidos_usuario(current_user: User) -> list[str]:
    atributos = current_user.atributos or {}
    sigilos = atributos.get("sigilos_permitidos")
    if isinstance(sigilos, list):
        return _normalizar_lista_texto([str(item) for item in sigilos])

    defaults = {
        "admin": ["publico", "interno", "restrito", "confidencial", "secreto"],
        "arquivista": ["publico", "interno", "restrito"],
        "auditor": ["publico", "interno", "restrito"],
        "classificador": ["publico", "interno"],
        "gestor": ["publico", "interno"],
        "viewer": ["publico"],
    }
    return defaults.get(current_user.role, ["publico"])


def _avaliar_acesso_nivel(nivel: PcdNivel, current_user: User, acao: str) -> ValidarAcessoResponse:
    if current_user.role == "admin":
        return ValidarAcessoResponse(
            pcd_nivel_id=nivel.id,
            permitido=True,
            acao=acao,
            papel=current_user.role,
            unidade_usuario=current_user.unidade,
            nivel_sigilo=nivel.nivel_sigilo,
            motivos=[],
        )

    motivos: list[str] = []
    controle = _obter_controle_classe(nivel) if nivel.tipo == "classe" else ControleSegurancaResponse(pcd_nivel_id=nivel.id)
    bloco = (nivel.metadados or {}).get("_controle_classe", {}) if isinstance(nivel.metadados, dict) else {}
    unidades_autorizadas = controle.unidades_autorizadas
    sigilos_permitidos = _sigilos_permitidos_usuario(current_user)

    if _sigilo_rank(nivel.nivel_sigilo) > max((_sigilo_rank(sigilo) for sigilo in sigilos_permitidos), default=0):
        motivos.append(f"Papel '{current_user.role}' sem acesso ao sigilo '{nivel.nivel_sigilo}'")

    permissoes_papel = controle.permissoes_por_papel.get(current_user.role, [])
    if controle.permissoes_por_papel and acao not in permissoes_papel:
        motivos.append(f"Papel '{current_user.role}' sem permissão para ação '{acao}'")

    if unidades_autorizadas:
        unidades_usuario = _normalizar_lista_texto(
            [
                current_user.unidade or "",
                *([str(item) for item in (current_user.atributos or {}).get("unidades_autorizadas", [])] if isinstance((current_user.atributos or {}).get("unidades_autorizadas"), list) else []),
            ]
        )
        if not any(unidade in unidades_autorizadas for unidade in unidades_usuario):
            motivos.append("Unidade do usuário não autorizada para a classe")

    if isinstance(bloco, dict) and bloco.get("segregacao_funcoes"):
        funcoes_bloqueadas = _normalizar_lista_texto([str(item) for item in bloco.get("segregacao_funcoes", [])])
        if current_user.role in funcoes_bloqueadas:
            motivos.append(f"Papel '{current_user.role}' bloqueado por segregação de funções")

    return ValidarAcessoResponse(
        pcd_nivel_id=nivel.id,
        permitido=len(motivos) == 0,
        acao=acao,
        papel=current_user.role,
        unidade_usuario=current_user.unidade,
        nivel_sigilo=nivel.nivel_sigilo,
        motivos=motivos,
    )


def _obter_controle_classe(nivel: PcdNivel) -> ControleSegurancaResponse:
    bloco = (nivel.metadados or {}).get("_controle_classe", {})

    if not isinstance(bloco, dict):
        return ControleSegurancaResponse(pcd_nivel_id=nivel.id)

    metadados_obrigatorios = bloco.get("metadados_obrigatorios", [])
    permissoes_por_papel = bloco.get("permissoes_por_papel", {})
    unidades_autorizadas = bloco.get("unidades_autorizadas", [])

    if not isinstance(metadados_obrigatorios, list):
        metadados_obrigatorios = []
    if not isinstance(permissoes_por_papel, dict):
        permissoes_por_papel = {}
    if not isinstance(unidades_autorizadas, list):
        unidades_autorizadas = []

    return ControleSegurancaResponse(
        pcd_nivel_id=nivel.id,
        metadados_obrigatorios=_normalizar_metadados_obrigatorios([str(item) for item in metadados_obrigatorios]),
        permissoes_por_papel=_normalizar_permissoes_por_papel(permissoes_por_papel),
        unidades_autorizadas=_normalizar_lista_texto([str(item) for item in unidades_autorizadas]),
    )


# ===== Endpoints =====

@router.get("/arvore", response_model=list[PcdNivelResponse])
async def obter_arvore_pcd(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter árvore hierárquica completa do PCD (US-010)."""
    result = await db.execute(
        select(PcdNivel)
        .where(PcdNivel.pai_id.is_(None))
        .options(selectinload(PcdNivel.filhos).selectinload(PcdNivel.filhos).selectinload(PcdNivel.filhos))
    )
    raizes = result.scalars().all()
    return raizes


@router.post("", response_model=PcdNivelResponse, status_code=status.HTTP_201_CREATED)
async def criar_nivel(
    data: PcdNivelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar nível no PCD (Função, Atividade, Série, Classe) (US-010)."""
    # Verificar pai se informado
    if data.pai_id:
        pai = await db.get(PcdNivel, data.pai_id)
        if not pai:
            raise HTTPException(status_code=404, detail="Nível pai não encontrado")

    nivel = PcdNivel(
        pai_id=data.pai_id,
        tipo=data.tipo,
        codigo=data.codigo,
        titulo=data.titulo,
        descricao=data.descricao,
        codigo_conarq=data.codigo_conarq,
        nivel_sigilo=data.nivel_sigilo,
        metadados=data.metadados,
        responsavel_id=current_user.id,
    )
    db.add(nivel)
    await db.flush()
    await db.refresh(nivel, attribute_names=["filhos"])
    return nivel


@router.get("/{nivel_id}", response_model=PcdNivelResponse)
async def obter_nivel(
    nivel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter nível por ID com filhos."""
    result = await db.execute(
        select(PcdNivel)
        .where(PcdNivel.id == nivel_id)
        .options(selectinload(PcdNivel.filhos))
    )
    nivel = result.scalar_one_or_none()
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")
    return nivel


@router.patch("/{nivel_id}", response_model=PcdNivelResponse)
async def atualizar_nivel(
    nivel_id: uuid.UUID,
    data: PcdNivelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar nível do PCD."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(nivel, field, value)

    await db.flush()
    await db.refresh(nivel, attribute_names=["filhos"])
    return nivel


@router.delete("/{nivel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_nivel(
    nivel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletar nível do PCD (cascade remove filhos)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")
    await db.delete(nivel)


@router.post("/{nivel_id}/versao", response_model=VersaoResponse, status_code=status.HTTP_201_CREATED)
async def criar_versao(
    nivel_id: uuid.UUID,
    data: VersaoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar nova versão do PCD com justificativa (US-011)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")

    # Snapshot dos dados atuais
    snapshot = {
        "tipo": nivel.tipo,
        "codigo": nivel.codigo,
        "titulo": nivel.titulo,
        "descricao": nivel.descricao,
        "codigo_conarq": nivel.codigo_conarq,
        "metadados": nivel.metadados,
    }

    versao = PcdVersao(
        pcd_nivel_id=nivel.id,
        versao=nivel.versao,
        dados_snapshot=snapshot,
        justificativa=data.justificativa,
    )
    db.add(versao)

    # Incrementar versão
    nivel.versao += 1

    await db.flush()
    await db.refresh(versao)
    return versao


@router.get("/{nivel_id}/versoes", response_model=list[VersaoResponse])
async def listar_versoes(
    nivel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar histórico de versões de um nível (US-011)."""
    result = await db.execute(
        select(PcdVersao)
        .where(PcdVersao.pcd_nivel_id == nivel_id)
        .order_by(PcdVersao.versao.desc())
    )
    return result.scalars().all()


@router.patch("/{nivel_id}/versoes/{versao_id}/status", response_model=VersaoResponse)
async def atualizar_status_versao(
    nivel_id: uuid.UUID,
    versao_id: uuid.UUID,
    data: VersaoStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar status de uma versão do PCD (US-011)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")

    versao = await db.get(PcdVersao, versao_id)
    if not versao or versao.pcd_nivel_id != nivel.id:
        raise HTTPException(status_code=404, detail="Versão não encontrada para este nível")

    status_permitidos = {"pendente", "aprovado", "rejeitado"}
    if data.status not in status_permitidos:
        raise HTTPException(
            status_code=400,
            detail=f"Status inválido: {data.status}. Permitidos: {sorted(status_permitidos)}",
        )

    versao.status = data.status
    if data.status == "aprovado":
        nivel.status = "ativo"

    await db.flush()
    await db.refresh(versao)
    return versao


@router.get("/{nivel_id}/controle-seguranca", response_model=ControleSegurancaResponse)
async def obter_controle_seguranca(
    nivel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter configuração de metadados obrigatórios e permissões por classe (US-012)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")
    if nivel.tipo != "classe":
        raise HTTPException(status_code=400, detail="Configuração disponível apenas para tipo classe")

    return _obter_controle_classe(nivel)


@router.patch("/{nivel_id}/controle-seguranca", response_model=ControleSegurancaResponse)
async def atualizar_controle_seguranca(
    nivel_id: uuid.UUID,
    data: ControleSegurancaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Configurar metadados obrigatórios e permissões por papel para classe (US-012)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")
    if nivel.tipo != "classe":
        raise HTTPException(status_code=400, detail="Configuração disponível apenas para tipo classe")

    metadados_obrigatorios = _normalizar_metadados_obrigatorios(data.metadados_obrigatorios)
    permissoes_por_papel = _normalizar_permissoes_por_papel(data.permissoes_por_papel)
    unidades_autorizadas = _normalizar_lista_texto(data.unidades_autorizadas)

    nivel.metadados = {
        **(nivel.metadados or {}),
        "_controle_classe": {
            "metadados_obrigatorios": metadados_obrigatorios,
            "permissoes_por_papel": permissoes_por_papel,
            "unidades_autorizadas": unidades_autorizadas,
        },
    }

    await db.flush()
    await db.refresh(nivel)
    return _obter_controle_classe(nivel)


@router.post("/{nivel_id}/validar-metadados", response_model=ValidarMetadadosResponse)
async def validar_metadados_obrigatorios(
    nivel_id: uuid.UUID,
    data: ValidarMetadadosRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validar preenchimento de metadados obrigatórios definidos na classe (US-012)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")
    if nivel.tipo != "classe":
        raise HTTPException(status_code=400, detail="Validação disponível apenas para tipo classe")

    controle = _obter_controle_classe(nivel)
    faltantes: list[str] = []

    for campo in controle.metadados_obrigatorios:
        valor = data.metadados_documento.get(campo)
        if valor is None:
            faltantes.append(campo)
            continue
        if isinstance(valor, str) and not valor.strip():
            faltantes.append(campo)

    return ValidarMetadadosResponse(
        pcd_nivel_id=nivel.id,
        valido=len(faltantes) == 0,
        faltantes=faltantes,
    )


@router.post("/{nivel_id}/validar-acesso", response_model=ValidarAcessoResponse)
async def validar_acesso_nivel(
    nivel_id: uuid.UUID,
    data: ValidarAcessoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validar acesso por papel, sigilo e unidade para um nível do PCD (US-060)."""
    nivel = await db.get(PcdNivel, nivel_id)
    if not nivel:
        raise HTTPException(status_code=404, detail="Nível não encontrado")

    return _avaliar_acesso_nivel(nivel, current_user, data.acao)
