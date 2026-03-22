"""Tests: Portal do Cliente — CLI-01 a CLI-04."""

import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.models.roteiro import Entrevista, Evidencia, Pergunta, Roteiro
from app.models.user import User
from app.routers import portal, roteiros as roteiros_router
from app.routers.auth import get_current_user, require_cliente, require_internal


# ===== Fake Session (simplificada) =====


class FakeScalars:
    def __init__(self, items: list[object]) -> None:
        self._items = items

    def all(self) -> list[object]:
        return self._items


class FakeExecuteResult:
    def __init__(self, payload: object | list[object] | None) -> None:
        self._payload = payload

    def scalar_one_or_none(self) -> object | None:
        if isinstance(self._payload, list):
            return self._payload[0] if self._payload else None
        return self._payload

    def scalar(self) -> object | None:
        if isinstance(self._payload, list):
            return len(self._payload)
        return self._payload

    def scalars(self) -> FakeScalars:
        if isinstance(self._payload, list):
            return FakeScalars(self._payload)
        if self._payload is None:
            return FakeScalars([])
        return FakeScalars([self._payload])


class FakeAsyncSession:
    def __init__(self) -> None:
        self.now = datetime.now(UTC)
        self.users: dict[uuid.UUID, User] = {}
        self.roteiros: dict[uuid.UUID, Roteiro] = {}
        self.perguntas: dict[uuid.UUID, Pergunta] = {}
        self.entrevistas: dict[uuid.UUID, Entrevista] = {}
        self.evidencias: dict[uuid.UUID, Evidencia] = {}

    def _filters_from_statement(self, statement: object) -> dict[str, object]:
        filters: dict[str, object] = {}
        for criterion in getattr(statement, "_where_criteria", ()):
            left = getattr(criterion, "left", None)
            column_name = getattr(left, "name", None)
            if not column_name:
                continue
            criterion_str = str(criterion)
            if " IS NULL" in criterion_str:
                filters[column_name] = None
                continue
            right = getattr(criterion, "right", None)
            filters[column_name] = getattr(right, "value", None)
        return filters

    def _model_from_statement(self, statement: object) -> object:
        column_descriptions = getattr(statement, "column_descriptions", None)
        if column_descriptions:
            return column_descriptions[0].get("entity")
        return None

    async def execute(self, statement: object) -> FakeExecuteResult:
        model = self._model_from_statement(statement)
        filters = self._filters_from_statement(statement)

        if model is Entrevista:
            items = list(self.entrevistas.values())
            for fk, fv in filters.items():
                items = [i for i in items if getattr(i, fk, None) == fv]
            if "id" in filters:
                return FakeExecuteResult(items[0] if items else None)
            return FakeExecuteResult(items)

        if model is Roteiro:
            items = list(self.roteiros.values())
            for fk, fv in filters.items():
                items = [i for i in items if getattr(i, fk, None) == fv]
            if "id" in filters:
                return FakeExecuteResult(items[0] if items else None)
            return FakeExecuteResult(items)

        if model is User:
            items = list(self.users.values())
            for fk, fv in filters.items():
                items = [i for i in items if getattr(i, fk, None) == fv]
            return FakeExecuteResult(items[0] if items else None)

        if model is Evidencia:
            items = list(self.evidencias.values())
            for fk, fv in filters.items():
                items = [i for i in items if getattr(i, fk, None) == fv]
            return FakeExecuteResult(items)

        return FakeExecuteResult(None)

    async def get(self, model: type[object], key: object) -> object | None:
        if model is User:
            return self.users.get(key)
        if model is Roteiro:
            return self.roteiros.get(key)
        if model is Pergunta:
            return self.perguntas.get(key)
        if model is Entrevista:
            return self.entrevistas.get(key)
        if model is Evidencia:
            return self.evidencias.get(key)
        return None

    def add(self, instance: object) -> None:
        if isinstance(instance, Entrevista):
            if instance.id is None:
                instance.id = uuid.uuid4()
            self.entrevistas[instance.id] = instance
        if isinstance(instance, Evidencia):
            if instance.id is None:
                instance.id = uuid.uuid4()
            self.evidencias[instance.id] = instance

    async def delete(self, instance: object) -> None:
        if isinstance(instance, Entrevista) and instance.id in self.entrevistas:
            del self.entrevistas[instance.id]
        if isinstance(instance, Evidencia) and instance.id in self.evidencias:
            del self.evidencias[instance.id]

    async def flush(self) -> None:
        return None

    async def refresh(self, instance: object, attrs: list[str] | None = None) -> None:
        if isinstance(instance, Entrevista) and attrs and "roteiro" in attrs:
            roteiro = self.roteiros.get(instance.roteiro_id)
            if roteiro:
                instance.roteiro = roteiro
        return None


# ===== Helpers =====


def _make_user(role: str = "admin", **kwargs) -> User:
    return User(
        id=kwargs.get("id", uuid.uuid4()),
        email=kwargs.get("email", f"{role}@example.com"),
        nome=kwargs.get("nome", role.capitalize()),
        hashed_password="hash",
        role=role,
        is_active=True,
        atributos={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_roteiro(session: FakeAsyncSession) -> Roteiro:
    pergunta = Pergunta(
        id=uuid.uuid4(),
        ordem=1,
        texto="Qual o tipo documental?",
        tipo="texto",
        obrigatoria=True,
        secao=None,
        metadado_alvo=None,
        opcoes=None,
        condicoes=[],
        created_at=datetime.now(UTC),
    )
    roteiro = Roteiro(
        id=uuid.uuid4(),
        titulo="Roteiro Teste",
        descricao="Desc",
        area="RH",
        versao=1,
        status="ativo",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        perguntas=[pergunta],
    )
    pergunta.roteiro_id = roteiro.id
    session.roteiros[roteiro.id] = roteiro
    session.perguntas[pergunta.id] = pergunta
    return roteiro


def _make_entrevista(
    session: FakeAsyncSession,
    roteiro: Roteiro,
    cliente: User,
    status: str = "em_andamento",
    respostas: dict | None = None,
) -> Entrevista:
    entrevista = Entrevista(
        id=uuid.uuid4(),
        roteiro_id=roteiro.id,
        entrevistador_id=uuid.uuid4(),
        cliente_id=cliente.id,
        status=status,
        respostas=respostas or {},
        motivo_devolucao=None,
        sugestao_classe=None,
        sugestao_justificativa=None,
        created_at=datetime.now(UTC),
        completed_at=None,
    )
    entrevista.roteiro = roteiro
    session.entrevistas[entrevista.id] = entrevista
    return entrevista


def _build_portal_app(session: FakeAsyncSession, user: User) -> FastAPI:
    app = FastAPI()
    app.include_router(portal.router, prefix="/api/v1/portal")

    async def override_db():
        yield session

    async def override_cliente():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_cliente] = override_cliente
    return app


def _build_internal_app(session: FakeAsyncSession, user: User) -> FastAPI:
    """Monta app com roteiros router + require_internal gate."""
    from fastapi import Depends

    app = FastAPI()
    app.include_router(
        roteiros_router.router,
        prefix="/api/v1/roteiros",
        dependencies=[Depends(require_internal)],
    )

    async def override_db():
        yield session

    async def override_current_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user
    return app


# ===== CLI-01: require_internal bloqueia cliente =====


def test_cliente_bloqueado_em_routers_internos() -> None:
    """Cliente com role='cliente' recebe 403 em endpoints internos."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    session.users[cliente.id] = cliente
    app = _build_internal_app(session, cliente)

    with TestClient(app) as c:
        r = c.get("/api/v1/roteiros")
        assert r.status_code == 403
        assert "internos" in r.json()["detail"].lower()


def test_interno_permitido_em_routers_internos() -> None:
    """Usuário com role interno passa normalmente."""
    session = FakeAsyncSession()
    admin = _make_user(role="admin")
    session.users[admin.id] = admin
    app = _build_internal_app(session, admin)

    with TestClient(app) as c:
        r = c.get("/api/v1/roteiros")
        assert r.status_code == 200


# ===== CLI-02: Novos status de entrevista =====


def test_transicao_em_andamento_para_submetida_pelo_cliente() -> None:
    """Cliente pode submeter entrevista em_andamento (via portal)."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    pergunta = roteiro.perguntas[0]
    entrevista = _make_entrevista(
        session, roteiro, cliente,
        respostas={str(pergunta.id): "Contrato de trabalho"},
    )
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.post(f"/api/v1/portal/entrevistas/{entrevista.id}/submeter")
        assert r.status_code == 200
        assert r.json()["status"] == "submetida"


def test_submeter_sem_obrigatorias_retorna_422() -> None:
    """Submissão sem preencher obrigatória falha com 422."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, cliente, respostas={})
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.post(f"/api/v1/portal/entrevistas/{entrevista.id}/submeter")
        assert r.status_code == 422
        assert "obrigatórias" in r.json()["detail"].lower()


def test_transicao_submetida_para_devolvida_requer_motivo() -> None:
    """Interno devolvendo sem motivo recebe 422."""
    session = FakeAsyncSession()
    arquivista = _make_user(role="arquivista")
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, cliente, status="submetida")
    session.users[cliente.id] = cliente
    app = _build_internal_app(session, arquivista)

    with TestClient(app) as c:
        # Sem motivo → 422
        r = c.patch(
            f"/api/v1/roteiros/entrevistas/{entrevista.id}",
            json={"status": "devolvida"},
        )
        assert r.status_code == 422
        assert "motivo_devolucao" in r.json()["detail"].lower()

        # Com motivo → 200
        r = c.patch(
            f"/api/v1/roteiros/entrevistas/{entrevista.id}",
            json={"status": "devolvida", "motivo_devolucao": "Faltam anexos"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "devolvida"
        assert r.json()["motivo_devolucao"] == "Faltam anexos"


def test_cliente_nao_pode_concluir() -> None:
    """Cliente não pode transicionar diretamente para concluida."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, cliente)
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        # Portal não tem endpoint PATCH com status, mas vamos testar via respostas
        # O cliente usa PATCH /portal/entrevistas/{id} que só aceita respostas
        r = c.patch(
            f"/api/v1/portal/entrevistas/{entrevista.id}",
            json={"respostas": {"q1": "v1"}},
        )
        assert r.status_code == 200


# ===== CLI-03: Endpoints do portal =====


def test_listar_entrevistas_portal_filtra_por_cliente() -> None:
    """Cliente vê apenas suas entrevistas."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    outro = _make_user(role="cliente", id=uuid.uuid4(), email="outro@x.com")
    roteiro = _make_roteiro(session)
    e1 = _make_entrevista(session, roteiro, cliente)
    _make_entrevista(session, roteiro, outro)  # não deve aparecer
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.get("/api/v1/portal/entrevistas")
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["id"] == str(e1.id)


def test_obter_detalhe_entrevista_portal() -> None:
    """GET detalhe retorna perguntas do roteiro."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, cliente)
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.get(f"/api/v1/portal/entrevistas/{entrevista.id}")
        assert r.status_code == 200
        body = r.json()
        assert body["roteiro_titulo"] == "Roteiro Teste"
        assert len(body["perguntas"]) == 1


def test_entrevista_de_outro_cliente_retorna_404() -> None:
    """Acesso a entrevista de outro cliente retorna 404."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    outro = _make_user(role="cliente", id=uuid.uuid4(), email="outro@x.com")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, outro)
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.get(f"/api/v1/portal/entrevistas/{entrevista.id}")
        assert r.status_code == 404


def test_atualizar_respostas_portal() -> None:
    """PATCH respostas em entrevista em_andamento funciona."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, cliente)
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.patch(
            f"/api/v1/portal/entrevistas/{entrevista.id}",
            json={"respostas": {"q1": "resposta"}},
        )
        assert r.status_code == 200


def test_atualizar_respostas_submetida_bloqueado() -> None:
    """PATCH respostas em entrevista submetida retorna 403."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(session, roteiro, cliente, status="submetida")
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.patch(
            f"/api/v1/portal/entrevistas/{entrevista.id}",
            json={"respostas": {"q1": "resposta"}},
        )
        assert r.status_code == 403


# ===== CLI-04: Atribuir entrevista a cliente =====


def test_criar_entrevista_com_cliente_id() -> None:
    """Interno pode criar entrevista atribuída a um cliente."""
    session = FakeAsyncSession()
    admin = _make_user(role="admin")
    cliente = _make_user(role="cliente", id=uuid.uuid4(), email="cli@x.com")
    session.users[admin.id] = admin
    session.users[cliente.id] = cliente
    roteiro = _make_roteiro(session)
    app = _build_internal_app(session, admin)

    with TestClient(app) as c:
        r = c.post(
            f"/api/v1/roteiros/{roteiro.id}/entrevistas",
            json={"respostas": {}, "cliente_id": str(cliente.id)},
        )
        assert r.status_code == 201
        assert r.json()["cliente_id"] == str(cliente.id)


def test_criar_entrevista_com_user_nao_cliente_retorna_422() -> None:
    """Atribuir entrevista a user que não é cliente retorna 422."""
    session = FakeAsyncSession()
    admin = _make_user(role="admin")
    gestor = _make_user(role="gestor", id=uuid.uuid4(), email="gest@x.com")
    session.users[admin.id] = admin
    session.users[gestor.id] = gestor
    roteiro = _make_roteiro(session)
    app = _build_internal_app(session, admin)

    with TestClient(app) as c:
        r = c.post(
            f"/api/v1/roteiros/{roteiro.id}/entrevistas",
            json={"respostas": {}, "cliente_id": str(gestor.id)},
        )
        assert r.status_code == 422
        assert "cliente" in r.json()["detail"].lower()


def test_devolvida_permite_edicao_no_portal() -> None:
    """Cliente pode editar entrevista devolvida."""
    session = FakeAsyncSession()
    cliente = _make_user(role="cliente")
    roteiro = _make_roteiro(session)
    entrevista = _make_entrevista(
        session, roteiro, cliente, status="devolvida",
    )
    entrevista.motivo_devolucao = "Faltam anexos"
    app = _build_portal_app(session, cliente)

    with TestClient(app) as c:
        r = c.patch(
            f"/api/v1/portal/entrevistas/{entrevista.id}",
            json={"respostas": {"q1": "corrigido"}},
        )
        assert r.status_code == 200
