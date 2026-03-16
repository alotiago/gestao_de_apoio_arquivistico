"""Router EP10: base de conhecimento, templates e onboarding interno."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.user import User
from app.routers.auth import get_current_user
from app.services.conhecimento import knowledge_base_store

router = APIRouter()


class TemplateConhecimentoResponse(BaseModel):
    slug: str
    titulo: str
    categoria: str
    descricao: str
    tags: list[str] = Field(default_factory=list)


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


class TrilhaProgressUpdate(BaseModel):
    etapas_concluidas: int = 0


@router.get("/templates", response_model=list[TemplateConhecimentoResponse])
async def listar_templates(
    query: str | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Listar templates oficiais e materiais de apoio por busca textual (US-091)."""
    templates = knowledge_base_store.search_templates(query)
    return [
        TemplateConhecimentoResponse(
            slug=item["slug"],
            titulo=item["titulo"],
            categoria=item["categoria"],
            descricao=item["descricao"],
            tags=item["tags"],
        )
        for item in templates
    ]


@router.get("/templates/{slug}/download", response_model=TemplateDownloadResponse)
async def baixar_template(
    slug: str,
    tipo: str = Query("template"),
    current_user: User = Depends(get_current_user),
):
    """Baixar template oficial ou guia de preenchimento da base de conhecimento (US-091)."""
    item = knowledge_base_store.get_template(slug)
    if not item:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    if tipo not in {"template", "guia"}:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'template' ou 'guia'")

    conteudo = item["template_content"] if tipo == "template" else item["guide_content"]
    sufixo = "template" if tipo == "template" else "guia"
    return TemplateDownloadResponse(
        slug=item["slug"],
        titulo=item["titulo"],
        tipo=tipo,
        nome_arquivo=f"{item['slug']}-{sufixo}.md",
        mime_type="text/markdown",
        conteudo=conteudo,
    )


@router.get("/trilhas", response_model=list[TrilhaOnboardingResponse])
async def listar_trilhas(
    current_user: User = Depends(get_current_user),
):
    """Listar trilhas de onboarding com progresso do usuário atual (US-091)."""
    return [TrilhaOnboardingResponse(**item) for item in knowledge_base_store.list_trilhas(str(current_user.id))]


@router.post("/trilhas/{trilha_id}/progresso", response_model=TrilhaOnboardingResponse)
async def atualizar_progresso_trilha(
    trilha_id: str,
    data: TrilhaProgressUpdate,
    current_user: User = Depends(get_current_user),
):
    """Atualizar progresso de onboarding e emitir badge ao concluir trilha (US-091)."""
    trilha = knowledge_base_store.update_progress(str(current_user.id), trilha_id, data.etapas_concluidas)
    if not trilha:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")
    return TrilhaOnboardingResponse(**trilha)
