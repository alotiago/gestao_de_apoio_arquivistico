"""
Router: Autenticacao (Login, Register, Refresh Token)
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

router = APIRouter()
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ===== Schemas =====

class UserCreate(BaseModel):
    email: EmailStr
    nome: str
    password: str
    role: str = "viewer"
    departamento: str | None = None
    unidade: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    nome: str
    role: str
    departamento: str | None
    unidade: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: uuid.UUID
    email: str
    role: str


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str


# ===== Helpers =====

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: extract and validate user from JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        parsed_user_id = uuid.UUID(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# ===== Endpoints =====

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        email=user_data.email,
        nome=user_data.nome,
        hashed_password=pwd_context.hash(user_data.password),
        role=user_data.role,
        departamento=user_data.departamento,
        unidade=user_data.unidade,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and issue JWT tokens."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Renew access/refresh tokens from a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de refresh inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_payload = jwt.decode(
            payload.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_type = token_payload.get("type")
        if token_type != "refresh":
            raise credentials_exception

        user_id: str = token_payload.get("sub")
        if user_id is None:
            raise credentials_exception

        parsed_user_id = uuid.UUID(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return authenticated user profile."""
    return current_user


@router.patch("/me/senha", status_code=status.HTTP_204_NO_CONTENT)
async def alterar_senha(
    data: AlterarSenhaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alterar senha do usuário autenticado."""
    if not pwd_context.verify(data.senha_atual, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual inválida")

    nova_senha = data.nova_senha
    if len(nova_senha) < 8 or not any(c.isupper() for c in nova_senha) or not any(c.isdigit() for c in nova_senha):
        raise HTTPException(status_code=400, detail="Nova senha deve conter ao menos 8 caracteres, 1 maiúscula e 1 número")

    current_user.hashed_password = get_password_hash(nova_senha)
    atributos = dict(current_user.atributos or {})
    if atributos.get("force_password_change"):
        atributos["force_password_change"] = False
    current_user.atributos = atributos

    await db.flush()
    return None


# ===== Role-based dependencies =====

INTERNAL_ROLES = {"admin", "gestor", "analista", "arquivista", "classificador", "auditor", "viewer"}


async def require_internal(current_user: User = Depends(get_current_user)) -> User:
    """Rejeita usuários com role 'cliente' — uso em routers internos."""
    if current_user.role not in INTERNAL_ROLES:
        raise HTTPException(status_code=403, detail="Acesso restrito a usuários internos")
    return current_user


async def require_cliente(current_user: User = Depends(get_current_user)) -> User:
    """Aceita apenas role 'cliente' — uso no portal externo."""
    if current_user.role != "cliente":
        raise HTTPException(status_code=403, detail="Endpoint exclusivo para clientes")
    return current_user
