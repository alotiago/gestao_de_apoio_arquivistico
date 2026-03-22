"""
Testes para o router de Relatórios, Exportação e Importação.

HU-032  Exportação PDF
HU-033  Exportação CSV / Excel
HU-034  Importação em lote
HU-035  Dashboard temporalidade
HU-036  Busca avançada
HU-037  Termo de eliminação
HU-038  Relatório de transferência
"""

import io
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.models.pcd import PcdNivel
from app.models.ttd import RegraRetencao, LegalHold
from app.models.user import User
from app.routers import relatorios
from app.routers.auth import get_current_user


# ===== Fixtures leves =====

_NOW = datetime.now(UTC)


def _user(role: str = "admin") -> User:
    return User(
        id=uuid.uuid4(),
        email="admin@example.com",
        nome="Admin Teste",
        hashed_password="hash",
        role=role,
        is_active=True,
        atributos={},
    )


def _nivel(codigo: str, tipo: str = "serie", titulo: str = "Nível Teste",
           pai_id: uuid.UUID | None = None) -> PcdNivel:
    n = PcdNivel(
        id=uuid.uuid4(),
        pai_id=pai_id,
        tipo=tipo,
        codigo=codigo,
        titulo=titulo,
        descricao="desc",
        codigo_conarq=None,
        versao=1,
        status="ativo",
        nivel_sigilo="publico",
        metadados={},
        created_at=_NOW,
        updated_at=_NOW,
    )
    n.filhos = []
    return n


def _regra(pcd_nivel_id: uuid.UUID, destinacao: str = "eliminacao") -> RegraRetencao:
    return RegraRetencao(
        id=uuid.uuid4(),
        pcd_nivel_id=pcd_nivel_id,
        evento_inicio="criacao",
        prazo_dias=1825,
        fase_corrente=3,
        fase_intermediaria=2,
        destinacao_final=destinacao,
        base_legal="Lei 8.159/91",
        legislacao_ref=None,
        observacoes="Obs teste",
        created_at=_NOW,
    )


# ===== Fake DB simples para relatórios =====

class FakeScalars:
    def __init__(self, items: list) -> None:
        self._items = items

    def all(self) -> list:
        return self._items


class FakeExecResult:
    def __init__(self, items: list) -> None:
        self._items = items

    def scalars(self) -> FakeScalars:
        return FakeScalars(self._items)

    def all(self) -> list:
        """For raw selects like select(LegalHold.pcd_nivel_id)."""
        return [(i.pcd_nivel_id if hasattr(i, "pcd_nivel_id") else i,) for i in self._items]


class FakeReportSession:
    """Sessão fake que resolve queries por modelo."""

    def __init__(self,
                 niveis: list[PcdNivel] | None = None,
                 regras: list[RegraRetencao] | None = None,
                 holds: list[LegalHold] | None = None):
        self._niveis = niveis or []
        self._regras = regras or []
        self._holds = holds or []

    async def execute(self, statement) -> FakeExecResult:
        model = None
        column_descriptions = getattr(statement, "column_descriptions", None)
        if column_descriptions:
            model = column_descriptions[0].get("entity")

        if model is PcdNivel:
            return FakeExecResult(self._niveis)
        if model is RegraRetencao:
            return FakeExecResult(self._regras)
        if model is LegalHold:
            return FakeExecResult(self._holds)

        # select(LegalHold.pcd_nivel_id) — column select
        cols = getattr(statement, "columns_clause_froms", None) or []
        for col in cols:
            table_name = getattr(getattr(col, "table", None), "name", "")
            if table_name == "legal_holds":
                return FakeExecResult(self._holds)

        return FakeExecResult([])

    async def flush(self):
        pass

    async def refresh(self, instance, attribute_names=None):
        pass

    def add(self, instance):
        if isinstance(instance, PcdNivel):
            self._niveis.append(instance)
        elif isinstance(instance, RegraRetencao):
            self._regras.append(instance)


def _build_app(session, user: User | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(relatorios.router, prefix="/api/v1/relatorios")

    async def override_get_db():
        yield session

    async def override_user():
        return user or _user()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_user
    return app


# ===== Testes =====

def test_busca_retorna_200() -> None:
    n1 = _nivel("F01", tipo="funcao", titulo="Gestão")
    session = FakeReportSession(niveis=[n1])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/busca?q=Gestão")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)


def test_dashboard_temporalidade() -> None:
    n1 = _nivel("S01", titulo="Serie A")
    regra = _regra(n1.id, "eliminacao")
    session = FakeReportSession(niveis=[n1], regras=[regra])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/dashboard-temporalidade")
        assert r.status_code == 200
        body = r.json()
        assert body["total_regras"] == 1
        assert "eliminacao" in body["por_destinacao"]
        assert body["total_com_hold"] == 0
        assert len(body["itens"]) == 1
        assert body["itens"][0]["codigo"] == "S01"


def test_exportar_csv() -> None:
    n1 = _nivel("F01", tipo="funcao", titulo="Administração")
    session = FakeReportSession(niveis=[n1])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/exportar/csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        content = r.content.decode("utf-8-sig")
        assert "Administra" in content


def test_exportar_pdf() -> None:
    n1 = _nivel("F01", tipo="funcao", titulo="Admin")
    session = FakeReportSession(niveis=[n1])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/exportar/pdf")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"


def test_exportar_excel() -> None:
    n1 = _nivel("F01", tipo="funcao", titulo="Admin")
    session = FakeReportSession(niveis=[n1])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/exportar/excel")
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers["content-type"]
        # XLSX magic bytes: PK (zip)
        assert r.content[:2] == b"PK"


def test_termo_eliminacao() -> None:
    n1 = _nivel("S01", titulo="Ofícios")
    regra = _regra(n1.id, "eliminacao")
    session = FakeReportSession(niveis=[n1], regras=[regra])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/termo-eliminacao")
        assert r.status_code == 200
        body = r.json()
        assert body["titulo"] == "Listagem de Eliminação de Documentos"
        assert body["total_itens"] == 1
        assert body["itens"][0]["codigo"] == "S01"


def test_termo_eliminacao_exclui_hold_ativo() -> None:
    n1 = _nivel("S01", titulo="Ofícios")
    regra = _regra(n1.id, "eliminacao")
    hold = LegalHold(
        id=uuid.uuid4(),
        pcd_nivel_id=n1.id,
        motivo="Litígio",
        tipo="litigio",
        aplicado_por=uuid.uuid4(),
        data_inicio=_NOW,
        status="ativo",
        created_at=_NOW,
    )
    session = FakeReportSession(niveis=[n1], regras=[regra], holds=[hold])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/termo-eliminacao")
        assert r.status_code == 200
        body = r.json()
        assert body["total_itens"] == 0


def test_relatorio_transferencia() -> None:
    n1 = _nivel("S02", titulo="Processos")
    regra = _regra(n1.id, "guarda_permanente")
    session = FakeReportSession(niveis=[n1], regras=[regra])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/relatorio-transferencia?tipo=transferencia")
        assert r.status_code == 200
        body = r.json()
        assert body["tipo_relatorio"] == "transferencia"
        assert body["total_itens"] == 1


def test_relatorio_transferencia_tipo_invalido() -> None:
    session = FakeReportSession()
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/relatorio-transferencia?tipo=invalido")
        assert r.status_code == 400


def test_termo_eliminacao_pdf() -> None:
    n1 = _nivel("S01", titulo="Ofícios")
    regra = _regra(n1.id, "eliminacao")
    session = FakeReportSession(niveis=[n1], regras=[regra])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/termo-eliminacao/pdf")
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-"


def test_relatorio_transferencia_pdf() -> None:
    n1 = _nivel("S02", titulo="Processos")
    regra = _regra(n1.id, "guarda_permanente")
    session = FakeReportSession(niveis=[n1], regras=[regra])
    app = _build_app(session)

    with TestClient(app) as c:
        r = c.get("/api/v1/relatorios/relatorio-transferencia/pdf?tipo=transferencia")
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-"
