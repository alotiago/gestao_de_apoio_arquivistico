"""
Router Admin — Gestão de usuários, papéis e configurações do sistema.
"""

import uuid
import secrets
import string
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user, get_password_hash
from app.services.lgpd import anonymized_email, decrypt_value, encrypt_value, mask_cpf, mask_email, mask_generic

router = APIRouter()


# ===== Schemas =====

class UserListResponse(BaseModel):
    id: uuid.UUID
    email: str
    nome: str
    role: str
    departamento: str | None
    unidade: str | None
    ativo: bool = Field(validation_alias="is_active")
    created_at: datetime
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    nome: str | None = None
    role: str | None = None
    departamento: str | None = None
    unidade: str | None = None
    ativo: bool | None = None
    atributos: dict | None = None


class UserCreateAdmin(BaseModel):
    email: EmailStr
    nome: str
    senha: str
    role: str = "viewer"
    departamento: str | None = None
    unidade: str | None = None
    atributos: dict | None = None


class PaginatedUsers(BaseModel):
    items: list[UserListResponse]
    total: int
    page: int
    per_page: int


class LgpdProtecaoRequest(BaseModel):
    cpf: str | None = None
    email_secundario: str | None = None
    campos_extras: dict[str, str] | None = None


class LgpdResumoResponse(BaseModel):
    user_id: uuid.UUID
    email_mascarado: str
    nome_mascarado: str
    anonimizado: bool
    campos_sensiveis: list[str]
    dados_mascarados: dict[str, str]


class ResetSenhaResponse(BaseModel):
    user_id: uuid.UUID
    senha_temporaria: str
    force_password_change: bool


# ===== Helpers =====

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores")
    return current_user


def _obter_bloco_lgpd(user: User) -> dict:
    atributos = user.atributos or {}
    bloco = atributos.get("_lgpd", {})
    return bloco if isinstance(bloco, dict) else {}


def _montar_resumo_lgpd(user: User) -> LgpdResumoResponse:
    bloco = _obter_bloco_lgpd(user)
    dados_criptografados = bloco.get("dados_criptografados", {})
    campos_sensiveis = list(dados_criptografados.keys()) if isinstance(dados_criptografados, dict) else []
    dados_mascarados: dict[str, str] = {}

    if isinstance(dados_criptografados, dict):
        for campo, valor in dados_criptografados.items():
            try:
                decrypted = decrypt_value(str(valor))
            except Exception:
                decrypted = ""
            if campo == "cpf":
                dados_mascarados[campo] = mask_cpf(decrypted)
            elif "email" in campo:
                dados_mascarados[campo] = mask_email(decrypted)
            else:
                dados_mascarados[campo] = mask_generic(decrypted)

    return LgpdResumoResponse(
        user_id=user.id,
        email_mascarado=mask_email(user.email),
        nome_mascarado=mask_generic(user.nome),
        anonimizado=bool(bloco.get("anonimizado")),
        campos_sensiveis=campos_sensiveis,
        dados_mascarados=dados_mascarados,
    )


# ===== Endpoints =====

@router.get("/usuarios", response_model=PaginatedUsers)
async def listar_usuarios(
    role: str | None = None,
    busca: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Listar todos os usuários com filtros."""
    query = select(User)
    count_query = select(func.count(User.id))

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if busca:
        pattern = f"%{busca}%"
        query = query.where(User.nome.ilike(pattern) | User.email.ilike(pattern))
        count_query = count_query.where(User.nome.ilike(pattern) | User.email.ilike(pattern))

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return PaginatedUsers(items=result.scalars().all(), total=total, page=page, per_page=per_page)


@router.post("/usuarios", response_model=UserListResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    data: UserCreateAdmin,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Criar usuário como admin."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        email=data.email,
        nome=data.nome,
        hashed_password=get_password_hash(data.senha),
        role=data.role,
        departamento=data.departamento,
        unidade=data.unidade,
        atributos=data.atributos or {},
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("/usuarios/{user_id}", response_model=UserListResponse)
async def obter_usuario(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Obter detalhes de um usuário."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.patch("/usuarios/{user_id}", response_model=UserListResponse)
async def atualizar_usuario(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Atualizar dados de um usuário (role, departamento, ativo, atributos ABAC)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    # Mapeia campo do schema para campo do modelo
    if "ativo" in update_data:
        update_data["is_active"] = update_data.pop("ativo")
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desativar_usuario(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Desativar (soft delete) um usuário."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.ativo = False
    await db.flush()


@router.post("/usuarios/{user_id}/reset-senha", response_model=ResetSenhaResponse)
async def resetar_senha_usuario(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Resetar senha de usuário com credencial temporária."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    caracteres = string.ascii_letters + string.digits
    senha_temporaria = "Tmp-" + "".join(secrets.choice(caracteres) for _ in range(10))
    user.hashed_password = get_password_hash(senha_temporaria)
    atributos = dict(user.atributos or {})
    atributos["force_password_change"] = True
    user.atributos = atributos

    await db.flush()
    return ResetSenhaResponse(
        user_id=user.id,
        senha_temporaria=senha_temporaria,
        force_password_change=True,
    )


@router.get("/stats")
async def estatisticas_sistema(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Estatísticas gerais do sistema."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    users_by_role = (
        await db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
    ).all()
    return {
        "total_usuarios": total_users,
        "por_role": {role: count for role, count in users_by_role},
    }


@router.post("/usuarios/{user_id}/lgpd/proteger", response_model=LgpdResumoResponse)
async def proteger_dados_lgpd(
    user_id: uuid.UUID,
    data: LgpdProtecaoRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Criptografar dados sensíveis em repouso e marcá-los no perfil do usuário (US-061)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    dados_sensiveis: dict[str, str] = {}
    if data.cpf:
        dados_sensiveis["cpf"] = encrypt_value(data.cpf)
    if data.email_secundario:
        dados_sensiveis["email_secundario"] = encrypt_value(data.email_secundario)
    if data.campos_extras:
        for campo, valor in data.campos_extras.items():
            if valor:
                dados_sensiveis[campo] = encrypt_value(valor)

    user.atributos = {
        **(user.atributos or {}),
        "_lgpd": {
            **_obter_bloco_lgpd(user),
            "dados_criptografados": dados_sensiveis,
            "anonimizado": False,
        },
    }
    await db.flush()
    await db.refresh(user)
    return _montar_resumo_lgpd(user)


@router.get("/usuarios/{user_id}/lgpd/resumo", response_model=LgpdResumoResponse)
async def obter_resumo_lgpd(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Obter resumo mascarado e estado de anonimização LGPD de um usuário (US-061)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return _montar_resumo_lgpd(user)


@router.post("/usuarios/{user_id}/lgpd/anonimizar", response_model=LgpdResumoResponse)
async def anonimizar_usuario_lgpd(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Anonimizar dados principais do usuário quando aplicável (US-061)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    identifier = str(user.id).split("-")[0]
    user.nome = f"Anonimizado {identifier}"
    user.email = anonymized_email(identifier)
    user.departamento = None
    user.unidade = None
    user.atributos = {
        **(user.atributos or {}),
        "_lgpd": {
            **_obter_bloco_lgpd(user),
            "dados_criptografados": {},
            "anonimizado": True,
        },
    }
    await db.flush()
    await db.refresh(user)
    return _montar_resumo_lgpd(user)
