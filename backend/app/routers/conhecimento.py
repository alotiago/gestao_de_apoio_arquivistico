"""Router EP10: base de conhecimento com persistência em banco."""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conhecimento import TemplateConhecimento, TrilhaConhecimento, TrilhaProgresso
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


class TemplateConhecimentoResponse(BaseModel):
    slug: str
    titulo: str
    categoria: str
    descricao: str
    tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TemplateConhecimentoCreate(BaseModel):
    slug: str | None = None
    titulo: str
    categoria: str = "Geral"
    descricao: str
    tags: list[str] = Field(default_factory=list)
    template_content: str
    guide_content: str


class TemplateConhecimentoUpdate(BaseModel):
    titulo: str | None = None
    categoria: str | None = None
    descricao: str | None = None
    tags: list[str] | None = None
    template_content: str | None = None
    guide_content: str | None = None
    ativo: bool | None = None


class TemplateDownloadResponse(BaseModel):
    slug: str
    titulo: str
    tipo: str
    nome_arquivo: str
    mime_type: str
    conteudo: str


class TrilhaOnboardingResponse(BaseModel):
    id: str
    nome: str
    perfil: str
    duracao_estimada_min: int
    etapas: list[str] = Field(default_factory=list)
    etapas_concluidas: int = 0
    progresso_percentual: float = 0
    badge_emitido: bool = False


class TrilhaCreate(BaseModel):
    nome: str
    perfil: str = "Geral"
    duracao_estimada_min: int = 60
    etapas: list[str] = Field(default_factory=list)


class TrilhaUpdate(BaseModel):
    nome: str | None = None
    perfil: str | None = None
    duracao_estimada_min: int | None = None
    etapas: list[str] | None = None
    ativo: bool | None = None


class TrilhaProgressUpdate(BaseModel):
    etapas_concluidas: int = 0


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug or f"template-{uuid.uuid4().hex[:8]}"


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in tags:
        clean = item.strip()
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized


def _role_can_manage(current_user: User) -> bool:
    return current_user.role in {"admin", "gestor"}


async def _require_manager(current_user: User = Depends(get_current_user)) -> User:
    if not _role_can_manage(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas admin/gestor podem gerenciar conhecimento")
    return current_user


def _first_from_result(result: object) -> object | None:
    items = result.scalars().all()
    return items[0] if items else None


async def _ensure_seed_data(db: AsyncSession) -> None:
    templates = (await db.execute(select(TemplateConhecimento))).scalars().all()
    trilhas = (await db.execute(select(TrilhaConhecimento))).scalars().all()
    template_slugs = {item.slug for item in templates}
    trilha_nomes = {item.nome for item in trilhas}

    if "termo-eliminacao" not in template_slugs:
        db.add(
            TemplateConhecimento(
                slug="termo-eliminacao",
                titulo="Termo de Eliminação",
                categoria="TTD",
                descricao="Template oficial para formalizar eliminação documental com checklist de conformidade.",
                tags=["termo", "eliminação", "ttd"],
                template_content="# Termo de Eliminação\n\n## Identificação\n- Classe documental:\n- Base legal:\n- Responsável:\n",
                guide_content="# Guia de Preenchimento — Termo de Eliminação\n\n1. Informe a classe documental validada no PCD.\n2. Anexe a ordem de destinação assinada.\n3. Registre a base legal da eliminação.\n",
                ativo=True,
            )
        )

    if "plano-classificacao" not in template_slugs:
        db.add(
            TemplateConhecimento(
                slug="plano-classificacao",
                titulo="Template de Plano de Classificação",
                categoria="PCD",
                descricao="Modelo padrão para cadastro e revisão de classes e séries documentais.",
                tags=["pcd", "classificação", "template"],
                template_content="# Plano de Classificação\n\n| Código | Título | Nível | Responsável |\n|---|---|---|---|\n",
                guide_content="# Guia de Preenchimento — Plano de Classificação\n\n- Utilize códigos únicos por nível.\n- Valide sigilo e metadados obrigatórios.\n",
                ativo=True,
            )
        )

    if "Trilha do Arquivista" not in trilha_nomes:
        db.add(
            TrilhaConhecimento(
                nome="Trilha do Arquivista",
                perfil="Arquivista",
                duracao_estimada_min=90,
                etapas=["Conhecer o PCD", "Validar TTD", "Gerar termos", "Consultar auditoria"],
                ativo=True,
            )
        )

    if "Trilha do Analista de Migração" not in trilha_nomes:
        db.add(
            TrilhaConhecimento(
                nome="Trilha do Analista de Migração",
                perfil="Analista",
                duracao_estimada_min=75,
                etapas=["Importar acervo", "Gerar inventário", "Planejar ondas", "Executar rollback"],
                ativo=True,
            )
        )
    await db.flush()


def _map_trilha_response(trilha: TrilhaConhecimento, progresso: TrilhaProgresso | None) -> TrilhaOnboardingResponse:
    etapas = list(trilha.etapas or [])
    total = len(etapas)
    concluidas = progresso.etapas_concluidas if progresso else 0
    concluidas = max(0, min(concluidas, total))
    percentual = round((concluidas / total) * 100, 2) if total else 0
    badge = bool(progresso.badge_emitido) if progresso else percentual == 100

    return TrilhaOnboardingResponse(
        id=str(trilha.id),
        nome=trilha.nome,
        perfil=trilha.perfil,
        duracao_estimada_min=trilha.duracao_estimada_min,
        etapas=etapas,
        etapas_concluidas=concluidas,
        progresso_percentual=percentual,
        badge_emitido=badge,
    )


@router.get("/templates", response_model=list[TemplateConhecimentoResponse])
async def listar_templates(
    query: str | None = Query(None),
    incluir_inativos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar templates oficiais e materiais de apoio por busca textual."""
    await _ensure_seed_data(db)

    items = (await db.execute(select(TemplateConhecimento))).scalars().all()
    if not incluir_inativos:
        items = [item for item in items if item.ativo]
    if query:
        search = query.strip().lower()
        items = [
            item
            for item in items
            if search in item.titulo.lower()
            or search in item.descricao.lower()
            or any(search in str(tag).lower() for tag in (item.tags or []))
        ]
    return [TemplateConhecimentoResponse.model_validate(item) for item in items]


@router.post("/templates", response_model=TemplateConhecimentoResponse, status_code=status.HTTP_201_CREATED)
async def criar_template(
    data: TemplateConhecimentoCreate,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(_require_manager),
):
    """Criar template/guia na base de conhecimento."""
    slug = _slugify(data.slug or data.titulo)
    existente = _first_from_result(await db.execute(select(TemplateConhecimento).where(TemplateConhecimento.slug == slug)))
    if existente:
        raise HTTPException(status_code=400, detail="Slug já cadastrado")

    item = TemplateConhecimento(
        slug=slug,
        titulo=data.titulo,
        categoria=data.categoria,
        descricao=data.descricao,
        tags=_normalize_tags(data.tags),
        template_content=data.template_content,
        guide_content=data.guide_content,
        ativo=True,
        criado_por=manager.id,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return TemplateConhecimentoResponse.model_validate(item)


@router.patch("/templates/{slug}", response_model=TemplateConhecimentoResponse)
async def atualizar_template(
    slug: str,
    data: TemplateConhecimentoUpdate,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(_require_manager),
):
    """Atualizar template existente."""
    item = _first_from_result(await db.execute(select(TemplateConhecimento).where(TemplateConhecimento.slug == slug)))
    if not item:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nenhuma alteração enviada")
    if "tags" in changes and changes["tags"] is not None:
        changes["tags"] = _normalize_tags(changes["tags"])

    for field, value in changes.items():
        setattr(item, field, value)

    await db.flush()
    await db.refresh(item)
    return TemplateConhecimentoResponse.model_validate(item)


@router.delete("/templates/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_template(
    slug: str,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(_require_manager),
):
    """Soft delete de template."""
    item = _first_from_result(await db.execute(select(TemplateConhecimento).where(TemplateConhecimento.slug == slug)))
    if not item:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    item.ativo = False
    await db.flush()
    return None


@router.get("/templates/{slug}/download", response_model=TemplateDownloadResponse)
async def baixar_template(
    slug: str,
    tipo: str = Query("template"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Baixar template oficial ou guia de preenchimento."""
    await _ensure_seed_data(db)

    item = _first_from_result(await db.execute(select(TemplateConhecimento).where(TemplateConhecimento.slug == slug)))
    if not item or not item.ativo:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    if tipo not in {"template", "guia"}:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'template' ou 'guia'")

    conteudo = item.template_content if tipo == "template" else item.guide_content
    sufixo = "template" if tipo == "template" else "guia"
    return TemplateDownloadResponse(
        slug=item.slug,
        titulo=item.titulo,
        tipo=tipo,
        nome_arquivo=f"{item.slug}-{sufixo}.md",
        mime_type="text/markdown",
        conteudo=conteudo,
    )


@router.get("/trilhas", response_model=list[TrilhaOnboardingResponse])
async def listar_trilhas(
    incluir_inativas: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar trilhas de onboarding com progresso do usuário atual."""
    await _ensure_seed_data(db)

    trilhas = (await db.execute(select(TrilhaConhecimento))).scalars().all()
    if not incluir_inativas:
        trilhas = [item for item in trilhas if item.ativo]

    progressos = (await db.execute(select(TrilhaProgresso))).scalars().all()
    progress_map = {
        str(item.trilha_id): item
        for item in progressos
        if item.user_id == current_user.id
    }
    return [_map_trilha_response(item, progress_map.get(str(item.id))) for item in trilhas]


@router.post("/trilhas", response_model=TrilhaOnboardingResponse, status_code=status.HTTP_201_CREATED)
async def criar_trilha(
    data: TrilhaCreate,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(_require_manager),
):
    """Criar trilha de onboarding."""
    trilha = TrilhaConhecimento(
        nome=data.nome,
        perfil=data.perfil,
        duracao_estimada_min=max(1, data.duracao_estimada_min),
        etapas=[etapa.strip() for etapa in data.etapas if etapa.strip()],
        ativo=True,
        criado_por=manager.id,
    )
    db.add(trilha)
    await db.flush()
    await db.refresh(trilha)
    return _map_trilha_response(trilha, None)


@router.patch("/trilhas/{trilha_id}", response_model=TrilhaOnboardingResponse)
async def atualizar_trilha(
    trilha_id: uuid.UUID,
    data: TrilhaUpdate,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(_require_manager),
):
    """Atualizar trilha de onboarding."""
    trilha = await db.get(TrilhaConhecimento, trilha_id)
    if not trilha:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nenhuma alteração enviada")
    if "duracao_estimada_min" in changes and changes["duracao_estimada_min"] is not None:
        changes["duracao_estimada_min"] = max(1, int(changes["duracao_estimada_min"]))
    if "etapas" in changes and changes["etapas"] is not None:
        changes["etapas"] = [etapa.strip() for etapa in changes["etapas"] if etapa.strip()]

    for field, value in changes.items():
        setattr(trilha, field, value)

    await db.flush()
    await db.refresh(trilha)

    progresso = _first_from_result(
        await db.execute(select(TrilhaProgresso).where(TrilhaProgresso.trilha_id == trilha.id, TrilhaProgresso.user_id == manager.id))
    )
    return _map_trilha_response(trilha, progresso)


@router.delete("/trilhas/{trilha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_trilha(
    trilha_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(_require_manager),
):
    """Soft delete de trilha."""
    trilha = await db.get(TrilhaConhecimento, trilha_id)
    if not trilha:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")
    trilha.ativo = False
    await db.flush()
    return None


@router.post("/trilhas/{trilha_id}/progresso", response_model=TrilhaOnboardingResponse)
async def atualizar_progresso_trilha(
    trilha_id: uuid.UUID,
    data: TrilhaProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar progresso de onboarding e emitir badge ao concluir trilha."""
    trilha = await db.get(TrilhaConhecimento, trilha_id)
    if not trilha or not trilha.ativo:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")

    progresso = _first_from_result(
        await db.execute(
            select(TrilhaProgresso).where(
                TrilhaProgresso.trilha_id == trilha.id,
                TrilhaProgresso.user_id == current_user.id,
            )
        )
    )

    if not progresso:
        progresso = TrilhaProgresso(user_id=current_user.id, trilha_id=trilha.id, etapas_concluidas=0, badge_emitido=False)
        db.add(progresso)

    total = len(trilha.etapas or [])
    concluidas = max(0, min(data.etapas_concluidas, total))
    progresso.etapas_concluidas = concluidas
    progresso.badge_emitido = total > 0 and concluidas == total

    await db.flush()
    await db.refresh(progresso)
    return _map_trilha_response(trilha, progresso)
