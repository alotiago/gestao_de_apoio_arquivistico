import uuid
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.models.roteiro import Condicao, Entrevista, Evidencia, Pergunta, Roteiro
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers import roteiros


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
            return None
        return self._payload

    def scalar(self) -> object | None:
        if isinstance(self._payload, list):
            return None
        return self._payload

    def scalars(self) -> FakeScalars:
        if isinstance(self._payload, list):
            return FakeScalars(self._payload)
        if self._payload is None:
            return FakeScalars([])
        return FakeScalars([self._payload])


class FakeAsyncSession:
    def __init__(self, roteiros_iniciais: list[Roteiro] | None = None) -> None:
        self.roteiros = {
            roteiro.id: roteiro
            for roteiro in (roteiros_iniciais or [])
            if roteiro.id is not None
        }
        self.perguntas = {
            pergunta.id: pergunta
            for roteiro in self.roteiros.values()
            for pergunta in roteiro.perguntas
            if pergunta.id is not None
        }
        self.entrevistas: dict[uuid.UUID, Entrevista] = {}
        self.evidencias: dict[uuid.UUID, Evidencia] = {}

    async def execute(self, statement: object) -> FakeExecuteResult:
        model = None
        column_descriptions = getattr(statement, "column_descriptions", None)
        if column_descriptions:
            model = column_descriptions[0].get("entity")

        where_criteria = getattr(statement, "_where_criteria", ())
        filtros: dict[str, object] = {}
        for criterion in where_criteria:
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            column_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            if column_name is not None:
                filtros[column_name] = value

        if model is Roteiro:
            if "id" in filtros:
                return FakeExecuteResult(self.roteiros.get(filtros["id"]))
            return FakeExecuteResult(list(self.roteiros.values()))

        if model is Entrevista:
            if "id" in filtros:
                return FakeExecuteResult(self.entrevistas.get(filtros["id"]))
            return FakeExecuteResult(list(self.entrevistas.values()))

        if model is Evidencia:
            items = list(self.evidencias.values())
            if "entrevista_id" in filtros:
                entrevista_id = filtros["entrevista_id"]
                items = [item for item in items if item.entrevista_id == entrevista_id]
            return FakeExecuteResult(items)

        return FakeExecuteResult(None)

    async def get(self, model: type[object], key: uuid.UUID) -> object | None:
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
        if isinstance(instance, Roteiro):
            if instance.id is None:
                instance.id = uuid.uuid4()
            self.roteiros[instance.id] = instance
            return

        if isinstance(instance, Pergunta):
            if instance.id is None:
                instance.id = uuid.uuid4()
            self.perguntas[instance.id] = instance
            for condicao in instance.condicoes:
                if condicao.id is None:
                    condicao.id = uuid.uuid4()
            roteiro = self.roteiros.get(instance.roteiro_id)
            if roteiro is not None:
                roteiro.perguntas.append(instance)

        if isinstance(instance, Entrevista):
            if instance.id is None:
                instance.id = uuid.uuid4()
            self.entrevistas[instance.id] = instance

        if isinstance(instance, Evidencia):
            if instance.id is None:
                instance.id = uuid.uuid4()
            self.evidencias[instance.id] = instance

    async def flush(self) -> None:
        return None

    async def refresh(self, instance: object, attrs: list[str] | None = None) -> None:
        return None


def build_test_app(session: FakeAsyncSession) -> FastAPI:
    app = FastAPI()
    app.include_router(roteiros.router, prefix="/api/v1/roteiros")

    async def override_get_db() -> FakeAsyncSession:
        yield session

    async def override_current_user() -> User:
        return User(
            id=uuid.uuid4(),
            email="admin@example.com",
            nome="Administrador",
            hashed_password="hash",
            role="admin",
            is_active=True,
            atributos={},
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    return app


def build_roteiro_base() -> Roteiro:
    roteiro_id = uuid.uuid4()
    pergunta_1_id = uuid.uuid4()
    pergunta_2_id = uuid.uuid4()

    pergunta_1 = Pergunta(
        id=pergunta_1_id,
        roteiro_id=roteiro_id,
        ordem=1,
        texto="Órgão produtor",
        tipo="texto",
        obrigatoria=True,
    )
    pergunta_2 = Pergunta(
        id=pergunta_2_id,
        roteiro_id=roteiro_id,
        ordem=2,
        texto="Justificativa complementar",
        tipo="texto",
        obrigatoria=True,
        condicoes=[
            Condicao(
                id=uuid.uuid4(),
                operador="EQ",
                valor={"pergunta_id": str(pergunta_1_id), "valor": "Não aplicável"},
                acao="ocultar",
            )
        ],
    )

    return Roteiro(
        id=roteiro_id,
        titulo="Roteiro base",
        descricao="Roteiro para testes de API",
        area="Arquivo",
        status="rascunho",
        versao=1,
        perguntas=[pergunta_1, pergunta_2],
    )


def test_simular_roteiro_retorna_estados_e_pendencias() -> None:
    roteiro = build_roteiro_base()
    session = FakeAsyncSession([roteiro])
    app = build_test_app(session)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/roteiros/{roteiro.id}/simular",
            json={"respostas": {str(roteiro.perguntas[0].id): "Não aplicável"}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["pode_concluir"] is True
    assert body["pendencias"] == []
    assert len(body["perguntas"]) == 2
    assert body["perguntas"][0]["visivel"] is True
    assert body["perguntas"][1]["visivel"] is False


def test_simular_roteiro_inexistente_retorna_404() -> None:
    session = FakeAsyncSession([])
    app = build_test_app(session)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/roteiros/{uuid.uuid4()}/simular",
            json={"respostas": {}},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Roteiro não encontrado"


def test_adicionar_pergunta_cria_item_com_condicao() -> None:
    roteiro = build_roteiro_base()
    roteiro.perguntas = []
    session = FakeAsyncSession([roteiro])
    app = build_test_app(session)

    payload = {
        "ordem": 1,
        "texto": "Há dados sensíveis?",
        "tipo": "boolean",
        "obrigatoria": True,
        "secao": "Triagem",
        "metadado_alvo": "sigilo",
        "opcoes": None,
        "condicoes": [
            {
                "operador": "EQ",
                "valor": {"pergunta_id": "q-origem", "valor": "Sim"},
                "acao": "obrigar",
                "alvo_id": None,
            }
        ],
    }

    with TestClient(app) as client:
        response = client.post(f"/api/v1/roteiros/{roteiro.id}/perguntas", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["texto"] == "Há dados sensíveis?"
    assert body["tipo"] == "boolean"
    assert len(body["condicoes"]) == 1
    assert body["condicoes"][0]["acao"] == "obrigar"
    assert len(session.roteiros[roteiro.id].perguntas) == 1
    assert session.roteiros[roteiro.id].perguntas[0].texto == "Há dados sensíveis?"


def test_iniciar_entrevista_retorna_sessao_ativa() -> None:
    roteiro = build_roteiro_base()
    session = FakeAsyncSession([roteiro])
    app = build_test_app(session)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/roteiros/{roteiro.id}/entrevistas",
            json={"respostas": {str(roteiro.perguntas[0].id): "TI"}},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["roteiro_id"] == str(roteiro.id)
    assert body["status"] == "em_andamento"
    assert len(session.entrevistas) == 1


def test_upload_evidencia_salva_hash_e_storage_path(monkeypatch: pytest.MonkeyPatch) -> None:
    roteiro = build_roteiro_base()
    session = FakeAsyncSession([roteiro])
    entrevista = Entrevista(
        id=uuid.uuid4(),
        roteiro_id=roteiro.id,
        entrevistador_id=uuid.uuid4(),
        status="em_andamento",
        respostas={},
        created_at=datetime.now(UTC),
    )
    session.add(entrevista)
    app = build_test_app(session)

    def fake_upload(_: bytes, storage_key: str, __: str | None = None) -> str:
        return f"s3://evidencias/{storage_key}"

    def fake_scan(_: bytes) -> tuple[bool, str | None]:
        return True, None

    monkeypatch.setattr(roteiros.settings, "CLAMAV_ENABLED", True)
    monkeypatch.setattr(roteiros, "scan_file_with_clamav", fake_scan)
    monkeypatch.setattr(roteiros, "upload_evidencia_bytes", fake_upload)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/roteiros/entrevistas/{entrevista.id}/evidencias",
            data={"pergunta_id": str(roteiro.perguntas[0].id)},
            files={"file": ("documento.txt", b"conteudo", "text/plain")},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["entrevista_id"] == str(entrevista.id)
    assert body["nome_arquivo"] == "documento.txt"
    assert body["hash_sha256"] == "92359bb294288000958de4f1f20d5778681b14bfe2f0868104f79230942a6984"
    assert body["storage_path"].startswith("s3://evidencias/entrevistas/")
    assert len(session.evidencias) == 1


def test_upload_evidencia_bloqueia_arquivo_infectado(monkeypatch: pytest.MonkeyPatch) -> None:
    roteiro = build_roteiro_base()
    session = FakeAsyncSession([roteiro])
    entrevista = Entrevista(
        id=uuid.uuid4(),
        roteiro_id=roteiro.id,
        entrevistador_id=uuid.uuid4(),
        status="em_andamento",
        respostas={},
        created_at=datetime.now(UTC),
    )
    session.add(entrevista)
    app = build_test_app(session)

    def fake_scan(_: bytes) -> tuple[bool, str | None]:
        return False, "EICAR-Test-Signature"

    monkeypatch.setattr(roteiros.settings, "CLAMAV_ENABLED", True)
    monkeypatch.setattr(roteiros, "scan_file_with_clamav", fake_scan)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/roteiros/entrevistas/{entrevista.id}/evidencias",
            files={"file": ("malware.txt", b"infectado", "text/plain")},
        )

    assert response.status_code == 400
    assert "Arquivo reprovado pelo antivírus" in response.json()["detail"]
    assert len(session.evidencias) == 0


def test_download_evidencia_retorna_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    roteiro = build_roteiro_base()
    session = FakeAsyncSession([roteiro])

    entrevista = Entrevista(
        id=uuid.uuid4(),
        roteiro_id=roteiro.id,
        entrevistador_id=uuid.uuid4(),
        status="em_andamento",
        respostas={},
        created_at=datetime.now(UTC),
    )
    session.add(entrevista)

    evidencia = Evidencia(
        id=uuid.uuid4(),
        entrevista_id=entrevista.id,
        pergunta_id=roteiro.perguntas[0].id,
        nome_arquivo="arquivo.txt",
        mime_type="text/plain",
        tamanho_bytes=8,
        hash_sha256="abc",
        storage_path="s3://evidencias/entrevistas/demo-arquivo.txt",
        created_at=datetime.now(UTC),
    )
    session.add(evidencia)
    app = build_test_app(session)

    def fake_download(_: str) -> bytes:
        return b"conteudo"

    monkeypatch.setattr(roteiros, "download_evidencia_bytes", fake_download)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/roteiros/evidencias/{evidencia.id}/download")

    assert response.status_code == 200
    assert response.content == b"conteudo"
    assert response.headers["content-type"].startswith("text/plain")


def test_gerar_sugestao_classe_persiste_retorno() -> None:
    roteiro = build_roteiro_base()
    session = FakeAsyncSession([roteiro])

    entrevista = Entrevista(
        id=uuid.uuid4(),
        roteiro_id=roteiro.id,
        entrevistador_id=uuid.uuid4(),
        status="em_andamento",
        respostas={str(roteiro.perguntas[0].id): "Contrato de fornecedor"},
        created_at=datetime.now(UTC),
    )
    session.add(entrevista)
    app = build_test_app(session)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/roteiros/entrevistas/{entrevista.id}/sugestao-classe",
            json={"respostas": {str(roteiro.perguntas[0].id): "Contrato aditivo fornecedor"}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["entrevista_id"] == str(entrevista.id)
    assert body["sugestao_classe"] == "PCD-Juridico-Contratos"
    assert "termos identificados" in body["sugestao_justificativa"]
    assert session.entrevistas[entrevista.id].sugestao_classe == "PCD-Juridico-Contratos"