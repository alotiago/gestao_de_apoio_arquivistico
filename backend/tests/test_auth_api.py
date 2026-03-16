import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.routers import auth
from app.routers.auth import create_access_token, create_refresh_token


class FakeExecuteResult:
    def __init__(self, payload: object | None) -> None:
        self._payload = payload

    def scalar_one_or_none(self) -> object | None:
        return self._payload


class FakeAsyncSession:
    def __init__(self) -> None:
        self.users: dict[uuid.UUID, User] = {}

    def _filters_from_statement(self, statement: object) -> dict[str, object]:
        filters: dict[str, object] = {}
        for criterion in getattr(statement, "_where_criteria", ()):
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            column_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            if column_name is not None:
                filters[column_name] = value
        return filters

    async def execute(self, statement: object) -> FakeExecuteResult:
        column_descriptions = getattr(statement, "column_descriptions", None)
        model = column_descriptions[0].get("entity") if column_descriptions else None
        filters = self._filters_from_statement(statement)

        if model is User:
            users = list(self.users.values())
            for filter_key, filter_value in filters.items():
                users = [item for item in users if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(users[0] if users else None)

        return FakeExecuteResult(None)


def build_test_app(session: FakeAsyncSession) -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1/auth")

    async def override_get_db() -> AsyncGenerator[FakeAsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return app


def build_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="usuario@example.com",
        nome="Usuario",
        hashed_password="hash",
        role="admin",
        is_active=True,
        atributos={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_refresh_token_renova_access_e_refresh() -> None:
    settings = get_settings()
    session = FakeAsyncSession()
    user = build_user()
    session.users[user.id] = user
    app = build_test_app(session)

    original_refresh_token = create_refresh_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh_token},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    access_payload = jwt.decode(
        body["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    refresh_payload = jwt.decode(
        body["refresh_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )

    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert access_payload["sub"] == str(user.id)
    assert refresh_payload["sub"] == str(user.id)


def test_refresh_token_rejeita_access_token() -> None:
    session = FakeAsyncSession()
    user = build_user()
    session.users[user.id] = user
    app = build_test_app(session)

    access_token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token de refresh inválido"


def test_me_rejeita_refresh_token() -> None:
    session = FakeAsyncSession()
    user = build_user()
    session.users[user.id] = user
    app = build_test_app(session)

    refresh_token = create_refresh_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"
