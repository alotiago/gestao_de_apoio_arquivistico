import json
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.database import get_db
from app.models.dados_migracao import DependenciaMigracao, FaseMigracao, InventarioQualidade, OndaMigracao, RegraCleansing
from app.middlewares.rate_limit import InMemoryRateLimitMiddleware
from app.middlewares.observability import ObservabilityMiddleware
from app.models.ciclo_vida import EventoInterno, JobRetencao, SeloEvidencia, WorkflowTarefa
from app.models.roteiro import Condicao, Entrevista, Evidencia, Pergunta, Roteiro
from app.models.governanca import AuditLog, MatrizRastreabilidade
from app.models.integracao import ImportacaoAcervo
from app.models.pcd import PcdNivel, PcdVersao
from app.models.ttd import LegalHold, OrdemDestinacao, RegraRetencao
from app.models.user import User
from app.routers import ciclo_vida, conhecimento, dados_migracao, governanca, health, integracao, pcd, roteiros, ttd
from app.routers.auth import get_current_user
from app.services.observability import observability_store


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
    def __init__(self) -> None:
        self.now = datetime.now(UTC)
        self.users: dict[uuid.UUID, User] = {}
        self.roteiros: dict[uuid.UUID, Roteiro] = {}
        self.perguntas: dict[uuid.UUID, Pergunta] = {}
        self.condicoes: dict[uuid.UUID, Condicao] = {}
        self.entrevistas: dict[uuid.UUID, Entrevista] = {}
        self.evidencias: dict[uuid.UUID, Evidencia] = {}
        self.pcd: dict[uuid.UUID, PcdNivel] = {}
        self.pcd_versoes: dict[uuid.UUID, PcdVersao] = {}
        self.regras: dict[uuid.UUID, RegraRetencao] = {}
        self.holds: dict[uuid.UUID, LegalHold] = {}
        self.ordens: dict[uuid.UUID, OrdemDestinacao] = {}
        self.workflows: dict[uuid.UUID, WorkflowTarefa] = {}
        self.jobs: dict[uuid.UUID, JobRetencao] = {}
        self.selos: dict[uuid.UUID, SeloEvidencia] = {}
        self.eventos: dict[uuid.UUID, EventoInterno] = {}
        self.importacoes: dict[uuid.UUID, ImportacaoAcervo] = {}
        self.regras_cleansing: dict[uuid.UUID, RegraCleansing] = {}
        self.inventarios: dict[uuid.UUID, InventarioQualidade] = {}
        self.ondas: dict[uuid.UUID, OndaMigracao] = {}
        self.fases_migracao: dict[uuid.UUID, FaseMigracao] = {}
        self.dependencias_migracao: dict[uuid.UUID, DependenciaMigracao] = {}
        self.matriz: dict[uuid.UUID, MatrizRastreabilidade] = {}
        self.logs: dict[int, AuditLog] = {}
        self._audit_seq = 1

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

        if model is PcdNivel:
            if "id" in filters:
                return FakeExecuteResult(self.pcd.get(filters["id"]))

            items = list(self.pcd.values())
            if "pai_id" in filters:
                pai_filter = filters["pai_id"]
                items = [item for item in items if item.pai_id == pai_filter]
            return FakeExecuteResult(items)

        if model is User:
            items = list(self.users.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is Roteiro:
            items = list(self.roteiros.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            if "id" in filters:
                return FakeExecuteResult(items[0] if items else None)
            return FakeExecuteResult(items)

        if model is PcdVersao:
            items = list(self.pcd_versoes.values())
            if "pcd_nivel_id" in filters:
                nivel_id = filters["pcd_nivel_id"]
                items = [item for item in items if item.pcd_nivel_id == nivel_id]
            return FakeExecuteResult(items)

        if model is RegraRetencao:
            items = list(self.regras.values())
            if "pcd_nivel_id" in filters:
                nivel_id = filters["pcd_nivel_id"]
                items = [item for item in items if item.pcd_nivel_id == nivel_id]
            return FakeExecuteResult(items)

        if model is LegalHold:
            items = list(self.holds.values())
            if "status" in filters:
                status_filter = filters["status"]
                items = [item for item in items if item.status == status_filter]
            return FakeExecuteResult(items)

        if model is OrdemDestinacao:
            items = list(self.ordens.values())
            if "status" in filters:
                status_filter = filters["status"]
                items = [item for item in items if item.status == status_filter]
            return FakeExecuteResult(items)

        if model is WorkflowTarefa:
            items = list(self.workflows.values())
            if "estado" in filters:
                estado = filters["estado"]
                items = [item for item in items if item.estado == estado]
            if "tipo" in filters:
                tipo = filters["tipo"]
                items = [item for item in items if item.tipo == tipo]
            return FakeExecuteResult(items)

        if model is JobRetencao:
            items = list(self.jobs.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is SeloEvidencia:
            items = list(self.selos.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is EventoInterno:
            items = list(self.eventos.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is ImportacaoAcervo:
            items = list(self.importacoes.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is RegraCleansing:
            items = list(self.regras_cleansing.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is InventarioQualidade:
            items = list(self.inventarios.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is OndaMigracao:
            items = list(self.ondas.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is FaseMigracao:
            items = list(self.fases_migracao.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is DependenciaMigracao:
            items = list(self.dependencias_migracao.values())
            for filter_key, filter_value in filters.items():
                items = [item for item in items if getattr(item, filter_key, None) == filter_value]
            return FakeExecuteResult(items)

        if model is MatrizRastreabilidade:
            items = list(self.matriz.values())
            if "pcd_nivel_id" in filters:
                nivel_id = filters["pcd_nivel_id"]
                items = [item for item in items if item.pcd_nivel_id == nivel_id]
            if "risco" in filters:
                risco = filters["risco"]
                items = [item for item in items if item.risco == risco]
            return FakeExecuteResult(items)

        if model is AuditLog:
            items = sorted(self.logs.values(), key=lambda item: item.id)
            if "entidade" in filters:
                entidade = filters["entidade"]
                items = [item for item in items if item.entidade == entidade]
            if "acao" in filters:
                acao = filters["acao"]
                items = [item for item in items if item.acao == acao]
            return FakeExecuteResult(items)

        return FakeExecuteResult(None)

    async def get(self, model: type[object], key: object) -> object | None:
        if model is User:
            return self.users.get(key)
        if model is Roteiro:
            return self.roteiros.get(key)
        if model is Pergunta:
            return self.perguntas.get(key)
        if model is Condicao:
            return self.condicoes.get(key)
        if model is Entrevista:
            return self.entrevistas.get(key)
        if model is Evidencia:
            return self.evidencias.get(key)
        if model is PcdNivel:
            return self.pcd.get(key)
        if model is PcdVersao:
            return self.pcd_versoes.get(key)
        if model is RegraRetencao:
            return self.regras.get(key)
        if model is LegalHold:
            return self.holds.get(key)
        if model is OrdemDestinacao:
            return self.ordens.get(key)
        if model is WorkflowTarefa:
            return self.workflows.get(key)
        if model is JobRetencao:
            return self.jobs.get(key)
        if model is SeloEvidencia:
            return self.selos.get(key)
        if model is EventoInterno:
            return self.eventos.get(key)
        if model is ImportacaoAcervo:
            return self.importacoes.get(key)
        if model is RegraCleansing:
            return self.regras_cleansing.get(key)
        if model is InventarioQualidade:
            return self.inventarios.get(key)
        if model is OndaMigracao:
            return self.ondas.get(key)
        if model is FaseMigracao:
            return self.fases_migracao.get(key)
        if model is DependenciaMigracao:
            return self.dependencias_migracao.get(key)
        if model is MatrizRastreabilidade:
            return self.matriz.get(key)
        if model is AuditLog:
            return self.logs.get(key)
        return None

    def add(self, instance: object) -> None:
        if isinstance(instance, User):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.updated_at is None:
                instance.updated_at = self.now
            if instance.atributos is None:
                instance.atributos = {}
            self.users[instance.id] = instance
            return

        if isinstance(instance, Roteiro):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.updated_at is None:
                instance.updated_at = self.now
            if instance.versao is None:
                instance.versao = 1
            if instance.status is None:
                instance.status = "rascunho"
            if instance.perguntas is None:
                instance.perguntas = []
            self.roteiros[instance.id] = instance
            for pergunta in instance.perguntas:
                if pergunta.id is None:
                    pergunta.id = uuid.uuid4()
                pergunta.roteiro_id = instance.id
                if pergunta.created_at is None:
                    pergunta.created_at = self.now
                if pergunta.condicoes is None:
                    pergunta.condicoes = []
                self.perguntas[pergunta.id] = pergunta
                for condicao in pergunta.condicoes:
                    if condicao.id is None:
                        condicao.id = uuid.uuid4()
                    condicao.pergunta_id = pergunta.id
                    if condicao.created_at is None:
                        condicao.created_at = self.now
                    self.condicoes[condicao.id] = condicao
            return

        if isinstance(instance, PcdNivel):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.updated_at is None:
                instance.updated_at = self.now
            if instance.versao is None:
                instance.versao = 1
            if instance.status is None:
                instance.status = "rascunho"
            if instance.nivel_sigilo is None:
                instance.nivel_sigilo = "publico"
            if instance.metadados is None:
                instance.metadados = {}
            if instance.filhos is None:
                instance.filhos = []
            self.pcd[instance.id] = instance
            if instance.pai_id:
                pai = self.pcd.get(instance.pai_id)
                if pai and all(child.id != instance.id for child in pai.filhos):
                    pai.filhos.append(instance)
            return

        if isinstance(instance, PcdVersao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.status is None:
                instance.status = "pendente"
            self.pcd_versoes[instance.id] = instance
            return

        if isinstance(instance, RegraRetencao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            self.regras[instance.id] = instance
            return

        if isinstance(instance, LegalHold):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.data_inicio is None:
                instance.data_inicio = self.now
            if instance.status is None:
                instance.status = "ativo"
            self.holds[instance.id] = instance
            return

        if isinstance(instance, OrdemDestinacao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.status is None:
                instance.status = "pendente"
            if instance.items is None:
                instance.items = []
            self.ordens[instance.id] = instance
            return

        if isinstance(instance, WorkflowTarefa):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.updated_at is None:
                instance.updated_at = self.now
            self.workflows[instance.id] = instance
            return

        if isinstance(instance, JobRetencao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.status is None:
                instance.status = "agendado"
            if instance.total_analisados is None:
                instance.total_analisados = 0
            if instance.total_ordens is None:
                instance.total_ordens = 0
            if instance.log_execucao is None:
                instance.log_execucao = {"execucoes": [], "ordens_geradas_ids": []}
            self.jobs[instance.id] = instance
            return

        if isinstance(instance, SeloEvidencia):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.metadados is None:
                instance.metadados = {}
            self.selos[instance.id] = instance
            return

        if isinstance(instance, EventoInterno):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.status is None:
                instance.status = "enviado"
            if instance.tentativas is None:
                instance.tentativas = 1
            if instance.payload is None:
                instance.payload = {}
            self.eventos[instance.id] = instance
            return

        if isinstance(instance, ImportacaoAcervo):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.mapping is None:
                instance.mapping = {}
            if instance.resultados is None:
                instance.resultados = []
            self.importacoes[instance.id] = instance
            return

        if isinstance(instance, RegraCleansing):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.configuracao is None:
                instance.configuracao = {}
            self.regras_cleansing[instance.id] = instance
            return

        if isinstance(instance, InventarioQualidade):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.regras_aplicadas is None:
                instance.regras_aplicadas = []
            if instance.indicadores is None:
                instance.indicadores = {}
            if instance.inconsistencias is None:
                instance.inconsistencias = []
            if instance.recomendacoes is None:
                instance.recomendacoes = []
            self.inventarios[instance.id] = instance
            return

        if isinstance(instance, OndaMigracao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.status is None:
                instance.status = "planejada"
            if instance.estrategia_corte is None:
                instance.estrategia_corte = "ondas"
            if instance.historico is None:
                instance.historico = []
            self.ondas[instance.id] = instance
            return

        if isinstance(instance, FaseMigracao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.status is None:
                instance.status = "planejada"
            if instance.rollback_script is None:
                instance.rollback_script = []
            self.fases_migracao[instance.id] = instance
            return

        if isinstance(instance, DependenciaMigracao):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            if instance.tipo is None:
                instance.tipo = "finish_to_start"
            self.dependencias_migracao[instance.id] = instance
            return

        if isinstance(instance, MatrizRastreabilidade):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if instance.created_at is None:
                instance.created_at = self.now
            self.matriz[instance.id] = instance
            return

        if isinstance(instance, AuditLog):
            if instance.id is None:
                instance.id = self._audit_seq
                self._audit_seq += 1
            if instance.created_at is None:
                instance.created_at = self.now
            self.logs[instance.id] = instance

    async def delete(self, instance: object) -> None:
        if isinstance(instance, PcdNivel) and instance.id in self.pcd:
            del self.pcd[instance.id]

    async def flush(self) -> None:
        return None

    async def refresh(self, instance: object, attrs: list[str] | None = None) -> None:
        return None


def build_test_app(router, prefix: str, session: FakeAsyncSession, current_user: User | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix=prefix)

    async def override_get_db() -> FakeAsyncSession:
        yield session

    async def override_current_user() -> User:
        if current_user is not None:
            return current_user
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


def test_pcd_arvore_e_versionamento() -> None:
    session = FakeAsyncSession()
    app = build_test_app(pcd.router, "/api/v1/pcd", session)

    with TestClient(app) as client:
        create_root = client.post(
            "/api/v1/pcd",
            json={
                "pai_id": None,
                "tipo": "funcao",
                "codigo": "F1",
                "titulo": "Gestão Administrativa",
                "descricao": None,
                "codigo_conarq": None,
                "nivel_sigilo": "publico",
                "metadados": {},
            },
        )
        assert create_root.status_code == 201
        root_id = create_root.json()["id"]

        create_child = client.post(
            "/api/v1/pcd",
            json={
                "pai_id": root_id,
                "tipo": "atividade",
                "codigo": "A1",
                "titulo": "Admissão",
                "descricao": None,
                "codigo_conarq": None,
                "nivel_sigilo": "publico",
                "metadados": {},
            },
        )
        assert create_child.status_code == 201

        arvore = client.get("/api/v1/pcd/arvore")
        assert arvore.status_code == 200
        body = arvore.json()
        assert len(body) == 1
        assert body[0]["codigo"] == "F1"
        assert len(body[0]["filhos"]) == 1

        update_root = client.patch(
            f"/api/v1/pcd/{root_id}",
            json={
                "titulo": "Gestão Administrativa Central",
                "descricao": "Escopo corporativo",
                "codigo_conarq": "01.00",
                "nivel_sigilo": "restrito",
                "status": "rascunho",
                "metadados": {"setor": "corporativo"},
            },
        )
        assert update_root.status_code == 200
        assert update_root.json()["titulo"] == "Gestão Administrativa Central"

        versao = client.post(
            f"/api/v1/pcd/{root_id}/versao",
            json={"justificativa": "Ajuste estrutural"},
        )
        assert versao.status_code == 201
        assert versao.json()["versao"] == 1
        versao_id = versao.json()["id"]
        assert versao.json()["dados_snapshot"]["titulo"] == "Gestão Administrativa Central"

        versoes = client.get(f"/api/v1/pcd/{root_id}/versoes")
        assert versoes.status_code == 200
        versoes_body = versoes.json()
        assert len(versoes_body) == 1
        assert versoes_body[0]["id"] == versao_id
        assert versoes_body[0]["dados_snapshot"]["metadados"]["setor"] == "corporativo"

        aprovar_versao = client.patch(
            f"/api/v1/pcd/{root_id}/versoes/{versao_id}/status",
            json={"status": "aprovado"},
        )
        assert aprovar_versao.status_code == 200
        assert aprovar_versao.json()["status"] == "aprovado"

        nivel_atualizado = client.get(f"/api/v1/pcd/{root_id}")
        assert nivel_atualizado.status_code == 200
        assert nivel_atualizado.json()["status"] == "ativo"


def test_pcd_controle_seguranca_e_validacao_metadados() -> None:
    session = FakeAsyncSession()
    app = build_test_app(pcd.router, "/api/v1/pcd", session)

    with TestClient(app) as client:
        create_classe = client.post(
            "/api/v1/pcd",
            json={
                "pai_id": None,
                "tipo": "classe",
                "codigo": "C100",
                "titulo": "Classe Contratos",
                "descricao": None,
                "codigo_conarq": None,
                "nivel_sigilo": "restrito",
                "metadados": {},
            },
        )
        assert create_classe.status_code == 201
        classe_id = create_classe.json()["id"]

        create_atividade = client.post(
            "/api/v1/pcd",
            json={
                "pai_id": None,
                "tipo": "atividade",
                "codigo": "A200",
                "titulo": "Atividade de apoio",
                "descricao": None,
                "codigo_conarq": None,
                "nivel_sigilo": "publico",
                "metadados": {},
            },
        )
        assert create_atividade.status_code == 201
        atividade_id = create_atividade.json()["id"]

        atualizar_controle = client.patch(
            f"/api/v1/pcd/{classe_id}/controle-seguranca",
            json={
                "metadados_obrigatorios": ["setor", "cpf_responsavel", "setor"],
                "permissoes_por_papel": {
                    "arquivista": ["ler", "editar", "editar"],
                    "auditor": ["ler"],
                },
            },
        )
        assert atualizar_controle.status_code == 200
        controle_body = atualizar_controle.json()
        assert controle_body["metadados_obrigatorios"] == ["setor", "cpf_responsavel"]
        assert controle_body["permissoes_por_papel"]["arquivista"] == ["ler", "editar"]

        obter_controle = client.get(f"/api/v1/pcd/{classe_id}/controle-seguranca")
        assert obter_controle.status_code == 200
        assert obter_controle.json()["metadados_obrigatorios"] == ["setor", "cpf_responsavel"]

        validar_invalido = client.post(
            f"/api/v1/pcd/{classe_id}/validar-metadados",
            json={"metadados_documento": {"setor": "RH"}},
        )
        assert validar_invalido.status_code == 200
        assert validar_invalido.json()["valido"] is False
        assert validar_invalido.json()["faltantes"] == ["cpf_responsavel"]

        validar_valido = client.post(
            f"/api/v1/pcd/{classe_id}/validar-metadados",
            json={"metadados_documento": {"setor": "RH", "cpf_responsavel": "12345678901"}},
        )
        assert validar_valido.status_code == 200
        assert validar_valido.json()["valido"] is True
        assert validar_valido.json()["faltantes"] == []

        controle_nao_classe = client.get(f"/api/v1/pcd/{atividade_id}/controle-seguranca")
        assert controle_nao_classe.status_code == 400


def test_pcd_validacao_acesso_rbac_abac() -> None:
    session = FakeAsyncSession()
    usuario_autorizado = User(
        id=uuid.uuid4(),
        email="arquivista@example.com",
        nome="Arquivista",
        hashed_password="hash",
        role="arquivista",
        is_active=True,
        unidade="RJ",
        atributos={
            "sigilos_permitidos": ["publico", "restrito"],
            "unidades_autorizadas": ["RJ"],
        },
    )
    app = build_test_app(pcd.router, "/api/v1/pcd", session, current_user=usuario_autorizado)

    with TestClient(app) as client:
        create_classe = client.post(
            "/api/v1/pcd",
            json={
                "pai_id": None,
                "tipo": "classe",
                "codigo": "C200",
                "titulo": "Classe Sigilosa",
                "descricao": None,
                "codigo_conarq": None,
                "nivel_sigilo": "restrito",
                "metadados": {},
            },
        )
        assert create_classe.status_code == 201
        classe_id = create_classe.json()["id"]

        salvar_controle = client.patch(
            f"/api/v1/pcd/{classe_id}/controle-seguranca",
            json={
                "metadados_obrigatorios": ["setor"],
                "permissoes_por_papel": {"arquivista": ["ler"]},
                "unidades_autorizadas": ["RJ"],
            },
        )
        assert salvar_controle.status_code == 200
        assert salvar_controle.json()["unidades_autorizadas"] == ["RJ"]

        acesso_permitido = client.post(
            f"/api/v1/pcd/{classe_id}/validar-acesso",
            json={"acao": "ler"},
        )
        assert acesso_permitido.status_code == 200
        assert acesso_permitido.json()["permitido"] is True

    usuario_bloqueado = User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        nome="Viewer",
        hashed_password="hash",
        role="viewer",
        is_active=True,
        unidade="SP",
        atributos={"sigilos_permitidos": ["publico"]},
    )
    app_bloqueado = build_test_app(pcd.router, "/api/v1/pcd", session, current_user=usuario_bloqueado)

    with TestClient(app_bloqueado) as client:
        acesso_negado = client.post(
            f"/api/v1/pcd/{classe_id}/validar-acesso",
            json={"acao": "ler"},
        )
        assert acesso_negado.status_code == 200
        assert acesso_negado.json()["permitido"] is False
        assert len(acesso_negado.json()["motivos"]) >= 1


def test_ttd_regras_holds_fluxo_basico() -> None:
    session = FakeAsyncSession()
    app = build_test_app(ttd.router, "/api/v1/ttd", session)

    nivel = PcdNivel(
        id=uuid.uuid4(),
        pai_id=None,
        tipo="classe",
        codigo="C1",
        titulo="Classe C1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        filhos=[],
    )
    session.add(nivel)

    with TestClient(app) as client:
        create_rule = client.post(
            "/api/v1/ttd/regras",
            json={
                "pcd_nivel_id": str(nivel.id),
                "evento_inicio": "fim_contrato",
                "prazo_dias": 365,
                "fase_corrente": 0,
                "fase_intermediaria": 0,
                "destinacao_final": "eliminacao",
                "base_legal": None,
                "legislacao_ref": None,
                "observacoes": None,
            },
        )
        assert create_rule.status_code == 201

        list_rules = client.get("/api/v1/ttd/regras")
        assert list_rules.status_code == 200
        assert len(list_rules.json()) == 1

        create_hold = client.post(
            "/api/v1/ttd/holds",
            json={
                "pcd_nivel_id": str(nivel.id),
                "motivo": "Auditoria interna",
                "tipo": "auditoria",
                "data_expiracao": None,
                "evidencia": None,
            },
        )
        assert create_hold.status_code == 201
        hold_id = create_hold.json()["id"]

        revoke_hold = client.patch(f"/api/v1/ttd/holds/{hold_id}/revogar")
        assert revoke_hold.status_code == 200
        assert revoke_hold.json()["status"] == "revogado"


def test_ttd_ordens_fluxo_aprovacao_assinatura() -> None:
    session = FakeAsyncSession()
    app = build_test_app(ttd.router, "/api/v1/ttd", session)

    with TestClient(app) as client:
        create_ordem = client.post(
            "/api/v1/ttd/ordens",
            json={
                "tipo": "eliminacao",
                "items": [
                    {"pcd_nivel_id": str(uuid.uuid4()), "quantidade": 12},
                    {"pcd_nivel_id": str(uuid.uuid4()), "quantidade": 5},
                ],
            },
        )
        assert create_ordem.status_code == 201
        ordem_id = create_ordem.json()["id"]
        assert create_ordem.json()["status"] == "pendente"

        list_ordens = client.get("/api/v1/ttd/ordens")
        assert list_ordens.status_code == 200
        assert len(list_ordens.json()) == 1

        aprovar_1 = client.patch(f"/api/v1/ttd/ordens/{ordem_id}/aprovar")
        assert aprovar_1.status_code == 200
        assert aprovar_1.json()["status"] == "em_aprovacao"
        assert aprovar_1.json()["aprovador_1_id"] is not None

        aprovar_2 = client.patch(f"/api/v1/ttd/ordens/{ordem_id}/aprovar")
        assert aprovar_2.status_code == 200
        assert aprovar_2.json()["status"] == "aprovado"
        assert aprovar_2.json()["aprovador_2_id"] is not None

        assinar = client.patch(
            f"/api/v1/ttd/ordens/{ordem_id}/assinar",
            json={"assinatura_digital": "ASS-HW1"},
        )
        assert assinar.status_code == 200
        assert assinar.json()["status"] == "assinado"
        assert assinar.json()["hash_termo"] is not None
        assert assinar.json()["assinatura_digital"] == "ASS-HW1"


def test_ciclo_vida_workflow_jobs() -> None:
    session = FakeAsyncSession()
    app = build_test_app(ciclo_vida.router, "/api/v1/ciclo-vida", session)

    workflow = WorkflowTarefa(
        id=uuid.uuid4(),
        tipo="avaliacao",
        estado="pendente",
        item_id=uuid.uuid4(),
        item_tipo="ordem_destinacao",
        sla_horas=72,
        comentario=None,
        escalado=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(workflow)

    regra_a = RegraRetencao(
        id=uuid.uuid4(),
        pcd_nivel_id=uuid.uuid4(),
        evento_inicio="fim_contrato",
        prazo_dias=180,
        fase_corrente=0,
        fase_intermediaria=0,
        destinacao_final="eliminacao",
        base_legal=None,
        legislacao_ref=None,
        observacoes=None,
        created_at=datetime.now(UTC),
    )
    regra_b = RegraRetencao(
        id=uuid.uuid4(),
        pcd_nivel_id=uuid.uuid4(),
        evento_inicio="rescisao",
        prazo_dias=365,
        fase_corrente=0,
        fase_intermediaria=0,
        destinacao_final="guarda_permanente",
        base_legal=None,
        legislacao_ref=None,
        observacoes=None,
        created_at=datetime.now(UTC),
    )
    session.add(regra_a)
    session.add(regra_b)

    hold = LegalHold(
        id=uuid.uuid4(),
        pcd_nivel_id=regra_b.pcd_nivel_id,
        motivo="Auditoria externa em andamento",
        tipo="auditoria",
        aplicado_por=uuid.uuid4(),
        data_inicio=datetime.now(UTC),
        data_expiracao=None,
        status="ativo",
        evidencia=None,
        created_at=datetime.now(UTC),
    )
    session.add(hold)

    with TestClient(app) as client:
        list_workflows = client.get("/api/v1/ciclo-vida/workflows")
        assert list_workflows.status_code == 200
        assert len(list_workflows.json()) == 1

        valid_transition = client.patch(
            f"/api/v1/ciclo-vida/workflows/{workflow.id}/transicao",
            json={"novo_estado": "em_avaliacao", "comentario": "Iniciado"},
        )
        assert valid_transition.status_code == 200
        assert valid_transition.json()["estado"] == "em_avaliacao"

        invalid_transition = client.patch(
            f"/api/v1/ciclo-vida/workflows/{workflow.id}/transicao",
            json={"novo_estado": "executado", "comentario": None},
        )
        assert invalid_transition.status_code == 400

        aprovar_workflow = client.patch(
            f"/api/v1/ciclo-vida/workflows/{workflow.id}/transicao",
            json={"novo_estado": "aprovado", "comentario": "Conferido"},
        )
        assert aprovar_workflow.status_code == 200
        assert aprovar_workflow.json()["estado"] == "aprovado"

        eventos_aprovacao = client.get("/api/v1/ciclo-vida/eventos?tipo=workflow.aprovado")
        assert eventos_aprovacao.status_code == 200
        eventos_body = eventos_aprovacao.json()
        assert len(eventos_body) == 1
        assert eventos_body[0]["status"] == "enviado"
        assert len(eventos_body[0]["assinatura"]) == 64

        retry_evento = client.post(f"/api/v1/ciclo-vida/eventos/{eventos_body[0]['id']}/retry")
        assert retry_evento.status_code == 200
        assert retry_evento.json()["tentativas"] == 2

        disparo_manual = client.post(
            "/api/v1/ciclo-vida/eventos/disparar",
            json={
                "tipo": "pcd.aprovado",
                "origem": "pcd",
                "referencia_id": str(uuid.uuid4()),
                "payload": {"status": "aprovado"},
            },
        )
        assert disparo_manual.status_code == 201
        assert disparo_manual.json()["tipo"] == "pcd.aprovado"
        assert len(disparo_manual.json()["assinatura"]) == 64

        janela_inicio = datetime(2026, 3, 1, 0, 0, tzinfo=UTC)
        janela_fim = datetime(2026, 3, 31, 23, 59, tzinfo=UTC)

        agendar_job = client.post(
            "/api/v1/ciclo-vida/jobs",
            json={
                "janela_inicio": janela_inicio.isoformat(),
                "janela_fim": janela_fim.isoformat(),
            },
        )
        assert agendar_job.status_code == 201
        job_body = agendar_job.json()
        job_id = job_body["id"]
        assert job_body["status"] == "agendado"

        agendar_mesma_janela = client.post(
            "/api/v1/ciclo-vida/jobs",
            json={
                "janela_inicio": janela_inicio.isoformat(),
                "janela_fim": janela_fim.isoformat(),
            },
        )
        assert agendar_mesma_janela.status_code in {200, 201}
        assert agendar_mesma_janela.json()["id"] == job_id

        executar_job = client.post(f"/api/v1/ciclo-vida/jobs/{job_id}/executar")
        assert executar_job.status_code == 200
        assert executar_job.json()["status"] == "concluido"
        assert executar_job.json()["total_analisados"] == 2
        assert executar_job.json()["total_ordens"] == 1
        assert len(session.ordens) == 1

        reprocessar_job = client.post(f"/api/v1/ciclo-vida/jobs/{job_id}/executar")
        assert reprocessar_job.status_code == 200
        assert reprocessar_job.json()["status"] == "concluido"
        assert reprocessar_job.json()["total_ordens"] == 1
        assert len(session.ordens) == 1
        execucoes = reprocessar_job.json()["log_execucao"]["execucoes"]
        assert len(execucoes) == 2
        assert "idempotente" in execucoes[-1]["mensagem"].lower()

        criar_selo_job = client.post(
            "/api/v1/ciclo-vida/selos",
            json={
                "entidade": "job_retencao",
                "entidade_id": job_id,
                "razao": "Fechamento mensal de retenção",
                "contexto": {"origem": "teste_integracao"},
            },
        )
        assert criar_selo_job.status_code == 201
        selo_body = criar_selo_job.json()
        assert selo_body["entidade"] == "job_retencao"
        assert selo_body["entidade_id"] == job_id
        assert len(selo_body["hash_selo"]) == 64

        pacote_job = client.get(f"/api/v1/ciclo-vida/auditoria/pacote?entidade=job_retencao&entidade_id={job_id}")
        assert pacote_job.status_code == 200
        pacote_body = pacote_job.json()
        assert pacote_body["resumo"]["selos"] == 1
        assert pacote_body["resumo"]["jobs"] == 1
        assert pacote_body["resumo"]["workflows"] == 0
        assert pacote_body["resumo"]["ordens"] == 0
        assert pacote_body["trilhas"]["selos"][0]["hash_selo"] == selo_body["hash_selo"]

        list_jobs = client.get("/api/v1/ciclo-vida/jobs?status=concluido")
        assert list_jobs.status_code == 200
        assert len(list_jobs.json()) == 1


def test_governanca_matriz_logs_integridade() -> None:
    session = FakeAsyncSession()
    app = build_test_app(governanca.router, "/api/v1/governanca", session)

    nivel = PcdNivel(
        id=uuid.uuid4(),
        pai_id=None,
        tipo="classe",
        codigo="C2",
        titulo="Classe C2",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        filhos=[],
    )
    session.add(nivel)

    log1 = AuditLog(
        id=1,
        hash_anterior=None,
        hash_atual="hash-1",
        acao="criar",
        entidade="pcd_nivel",
        entidade_id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        dados_antes=None,
        dados_depois={"codigo": "C2"},
        ip_address="127.0.0.1",
        user_agent="pytest",
        created_at=datetime.now(UTC),
    )
    log2 = AuditLog(
        id=2,
        hash_anterior="hash-1",
        hash_atual="hash-2",
        acao="atualizar",
        entidade="pcd_nivel",
        entidade_id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        dados_antes={"codigo": "C2"},
        dados_depois={"codigo": "C2A"},
        ip_address="127.0.0.1",
        user_agent="pytest",
        created_at=datetime.now(UTC),
    )
    session.add(log1)
    session.add(log2)

    with TestClient(app) as client:
        create_matriz = client.post(
            "/api/v1/governanca/matriz",
            json={
                "pcd_nivel_id": str(nivel.id),
                "legislacao": "Lei 8.159/91",
                "artigo": "Art. 1",
                "norma_interna": None,
                "regra_retencao_id": None,
                "risco": "medio",
                "evidencia": None,
            },
        )
        assert create_matriz.status_code == 201

        list_matriz = client.get("/api/v1/governanca/matriz")
        assert list_matriz.status_code == 200
        assert len(list_matriz.json()) == 1

        list_logs = client.get("/api/v1/governanca/logs")
        assert list_logs.status_code == 200
        assert len(list_logs.json()) == 2

        integridade = client.get("/api/v1/governanca/logs/verificar-integridade")
        assert integridade.status_code == 200
        body = integridade.json()
        assert body["integridade"] == "OK"
        assert body["total_inconsistencias"] == 0


def test_rate_limit_middleware_bloqueia_excesso() -> None:
    app = FastAPI()
    app.add_middleware(InMemoryRateLimitMiddleware, limit_per_window=2, window_seconds=60)

    @app.get("/api/v1/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        first = client.get("/api/v1/ping")
        second = client.get("/api/v1/ping")
        third = client.get("/api/v1/ping")

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 429


def test_integracao_importacao_acervo_csv() -> None:
    session = FakeAsyncSession()
    app = build_test_app(integracao.router, "/api/v1/integracao", session)

    classe = PcdNivel(
        id=uuid.uuid4(),
        pai_id=None,
        tipo="classe",
        codigo="CL001",
        titulo="Classe Contratos",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        filhos=[],
    )
    session.add(classe)

    csv_content = "codigo_doc,titulo_doc,classe_ref,descricao_doc\nDOC-1,Contrato Master,CL001,Registro válido\nDOC-2,,CL001,Falta título\nDOC-3,Documento órfão,CL999,Classe inválida\n"
    mapping = {
        "codigo": "codigo_doc",
        "titulo": "titulo_doc",
        "classe_codigo": "classe_ref",
        "descricao": "descricao_doc",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/integracao/importacoes",
            files={"arquivo": ("inventario.csv", csv_content.encode("utf-8"), "text/csv")},
            data={"mapping_json": json.dumps(mapping)},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "concluido_com_erros"
        assert body["total_registros"] == 3
        assert body["total_sucesso"] == 1
        assert body["total_erros"] == 2
        assert len(body["resultados"]) == 3
        assert body["resultados"][0]["status"] == "sucesso"
        assert body["resultados"][1]["status"] == "erro"

        listagem = client.get("/api/v1/integracao/importacoes")
        assert listagem.status_code == 200
        assert len(listagem.json()) == 1

        detalhe = client.get(f"/api/v1/integracao/importacoes/{body['id']}")
        assert detalhe.status_code == 200
        assert detalhe.json()["nome_arquivo"] == "inventario.csv"


def test_dados_migracao_inventario_qualidade_com_historico() -> None:
    session = FakeAsyncSession()
    app = FastAPI()
    app.include_router(integracao.router, prefix="/api/v1/integracao")
    app.include_router(dados_migracao.router, prefix="/api/v1/dados-migracao")

    async def override_get_db() -> FakeAsyncSession:
        yield session

    async def override_current_user() -> User:
        return User(
            id=uuid.uuid4(),
            email="dados@example.com",
            nome="Gestor de Dados",
            hashed_password="hash",
            role="admin",
            is_active=True,
            atributos={},
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    importacao = ImportacaoAcervo(
        id=uuid.uuid4(),
        nome_arquivo="acervo-ep9.csv",
        status="concluido_com_erros",
        mapping={
            "codigo": "codigo_doc",
            "titulo": "titulo_doc",
            "classe_codigo": "classe_ref",
        },
        total_registros=4,
        total_sucesso=3,
        total_erros=1,
        resultados=[
            {
                "linha": 2,
                "status": "sucesso",
                "codigo": "doc-1 ",
                "titulo": " Contrato Master ",
                "classe_codigo": "cl001",
            },
            {
                "linha": 3,
                "status": "sucesso",
                "codigo": "DOC-1",
                "titulo": "Contrato Master",
                "classe_codigo": "CL001",
            },
            {
                "linha": 4,
                "status": "erro",
                "codigo": "",
                "titulo": "Documento sem código",
                "classe_codigo": "CL001",
                "erros": ["codigo ausente"],
            },
            {
                "linha": 5,
                "status": "sucesso",
                "codigo": "doc-3",
                "titulo": "ab",
                "classe_codigo": "CL001",
            },
        ],
        observacoes="Carga piloto",
        created_at=datetime.now(UTC),
    )
    session.add(importacao)

    with TestClient(app) as client:
        regra_trim = client.post(
            "/api/v1/dados-migracao/regras-cleansing",
            json={"nome": "Trim global", "tipo": "trim", "campo": None, "configuracao": {}, "ativo": True},
        )
        assert regra_trim.status_code == 201

        regra_upper = client.post(
            "/api/v1/dados-migracao/regras-cleansing",
            json={"nome": "Upper código", "tipo": "upper", "campo": "codigo", "configuracao": {}, "ativo": True},
        )
        assert regra_upper.status_code == 201

        regras = client.get("/api/v1/dados-migracao/regras-cleansing?ativo=true")
        assert regras.status_code == 200
        assert len(regras.json()) == 2

        primeiro_scan = client.post(
            "/api/v1/dados-migracao/inventarios/scan",
            json={
                "importacao_id": str(importacao.id),
                "regra_ids": [regra_trim.json()["id"], regra_upper.json()["id"]],
                "incluir_apenas_sucesso": False,
            },
        )
        assert primeiro_scan.status_code == 201
        body = primeiro_scan.json()
        assert body["status_qualidade"] in {"atencao", "critico"}
        assert body["indicadores"]["duplicidades_codigo"] == ["DOC-1"]
        assert body["indicadores"]["transformacoes_aplicadas"] >= 2
        assert body["comparativo_anterior"] is None

        segundo_scan = client.post(
            "/api/v1/dados-migracao/inventarios/scan",
            json={
                "importacao_id": str(importacao.id),
                "regra_ids": [regra_trim.json()["id"], regra_upper.json()["id"]],
                "incluir_apenas_sucesso": True,
            },
        )
        assert segundo_scan.status_code == 201
        second_body = segundo_scan.json()
        assert second_body["comparativo_anterior"] is not None
        assert second_body["comparativo_anterior"]["score_geral_delta"] > 0

        historico = client.get(f"/api/v1/dados-migracao/inventarios?importacao_id={importacao.id}")
        assert historico.status_code == 200
        assert len(historico.json()) == 2

        detalhe = client.get(f"/api/v1/dados-migracao/inventarios/{second_body['id']}")
        assert detalhe.status_code == 200
        assert detalhe.json()["importacao_id"] == str(importacao.id)


def test_dados_migracao_planejamento_ondas_validacao_e_rollback() -> None:
    session = FakeAsyncSession()
    app = build_test_app(dados_migracao.router, "/api/v1/dados-migracao", session)

    inventario = InventarioQualidade(
        id=uuid.uuid4(),
        importacao_id=uuid.uuid4(),
        total_registros=12,
        score_geral=91.5,
        score_completude=95.0,
        score_unicidade=88.0,
        score_conformidade=90.0,
        status_qualidade="saudavel",
        regras_aplicadas=[],
        indicadores={},
        inconsistencias=[],
        recomendacoes=["seguir com a onda"],
        comparativo_anterior=None,
        created_at=datetime.now(UTC),
    )
    session.add(inventario)

    with TestClient(app) as client:
        onda_1 = client.post(
            "/api/v1/dados-migracao/ondas",
            json={
                "nome": "Wave 1",
                "unidade": "DF",
                "processo": "Legislação",
                "ordem": 1,
                "estrategia_corte": "ondas",
                "inventario_id": str(inventario.id),
                "dependencia_ids": [],
                "fases": [
                    {"nome": "Preparação", "ordem": 1, "rollback_script": ["restaurar snapshot df"]},
                    {"nome": "Carga", "ordem": 2, "rollback_script": ["reverter lote df"]},
                ],
            },
        )
        assert onda_1.status_code == 201
        onda_1_id = onda_1.json()["id"]

        onda_2 = client.post(
            "/api/v1/dados-migracao/ondas",
            json={
                "nome": "Wave 2",
                "unidade": "SP",
                "processo": "TTD",
                "ordem": 2,
                "estrategia_corte": "ondas",
                "inventario_id": str(inventario.id),
                "dependencia_ids": [onda_1_id],
                "fases": [],
            },
        )
        assert onda_2.status_code == 201
        onda_2_body = onda_2.json()
        assert len(onda_2_body["dependencias"]) == 1
        assert len(onda_2_body["fases"]) == 3

        cronograma = client.get("/api/v1/dados-migracao/ondas")
        assert cronograma.status_code == 200
        assert [item["nome"] for item in cronograma.json()] == ["Wave 1", "Wave 2"]

        validacao_bloqueada = client.post(f"/api/v1/dados-migracao/ondas/{onda_2_body['id']}/validar")
        assert validacao_bloqueada.status_code == 200
        assert validacao_bloqueada.json()["pronta"] is False
        assert validacao_bloqueada.json()["dependencias_pendentes"] == ["Wave 1"]

        concluir_onda_1 = client.patch(
            f"/api/v1/dados-migracao/ondas/{onda_1_id}/status",
            json={"status": "concluida"},
        )
        assert concluir_onda_1.status_code == 200
        assert concluir_onda_1.json()["status"] == "concluida"

        validacao_pronta = client.post(f"/api/v1/dados-migracao/ondas/{onda_2_body['id']}/validar")
        assert validacao_pronta.status_code == 200
        assert validacao_pronta.json()["pronta"] is True
        assert validacao_pronta.json()["score_qualidade"] == inventario.score_geral

        primeira_fase = onda_2_body["fases"][0]
        rollback = client.post(
            f"/api/v1/dados-migracao/ondas/{onda_2_body['id']}/rollback",
            json={"fase_id": primeira_fase["id"], "motivo": "falha de validação pós-carga"},
        )
        assert rollback.status_code == 200
        assert rollback.json()["status"] == "rollback_executado"
        assert rollback.json()["fases_afetadas"] == [primeira_fase["nome"]]

        detalhe = client.get(f"/api/v1/dados-migracao/ondas?status=rollback_executado")
        assert detalhe.status_code == 200
        assert len(detalhe.json()) == 1


def test_conhecimento_templates_e_trilhas_onboarding() -> None:
    session = FakeAsyncSession()
    app = build_test_app(conhecimento.router, "/api/v1/conhecimento", session)

    with TestClient(app) as client:
        templates = client.get("/api/v1/conhecimento/templates?query=Termo de eliminação")
        assert templates.status_code == 200
        assert len(templates.json()) >= 1
        assert templates.json()[0]["slug"] == "termo-eliminacao"

        download_template = client.get("/api/v1/conhecimento/templates/termo-eliminacao/download?tipo=template")
        assert download_template.status_code == 200
        assert download_template.json()["nome_arquivo"].endswith("template.md")
        assert "Termo de Eliminação" in download_template.json()["conteudo"]

        download_guia = client.get("/api/v1/conhecimento/templates/termo-eliminacao/download?tipo=guia")
        assert download_guia.status_code == 200
        assert "Guia de Preenchimento" in download_guia.json()["conteudo"]

        trilhas = client.get("/api/v1/conhecimento/trilhas")
        assert trilhas.status_code == 200
        assert len(trilhas.json()) >= 1
        trilha_id = trilhas.json()[0]["id"]

        progresso = client.post(
            f"/api/v1/conhecimento/trilhas/{trilha_id}/progresso",
            json={"etapas_concluidas": len(trilhas.json()[0]["etapas"])},
        )
        assert progresso.status_code == 200
        assert progresso.json()["badge_emitido"] is True


def test_roteiros_preview_assistido_pcd_ttd() -> None:
    session = FakeAsyncSession()
    app = build_test_app(roteiros.router, "/api/v1/roteiros", session)

    pergunta_tipo = Pergunta(
        id=uuid.uuid4(),
        roteiro_id=uuid.uuid4(),
        ordem=1,
        texto="Qual o tipo do documento?",
        tipo="texto",
        obrigatoria=True,
        secao="contexto",
        metadado_alvo="classe",
        opcoes=None,
        condicoes=[],
        created_at=datetime.now(UTC),
    )
    pergunta_evento = Pergunta(
        id=uuid.uuid4(),
        roteiro_id=uuid.uuid4(),
        ordem=2,
        texto="Qual o evento de início da guarda?",
        tipo="texto",
        obrigatoria=True,
        secao="ttd",
        metadado_alvo="evento",
        opcoes=None,
        condicoes=[],
        created_at=datetime.now(UTC),
    )
    roteiro = Roteiro(
        id=uuid.uuid4(),
        titulo="Roteiro Contratual",
        descricao="Preview assistido",
        area="Contratos",
        versao=1,
        status="ativo",
        criado_por=uuid.uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        perguntas=[pergunta_tipo, pergunta_evento],
    )
    session.add(roteiro)

    with TestClient(app) as client:
        preview = client.post(
            f"/api/v1/roteiros/{roteiro.id}/assistente-preview",
            json={
                "respostas": {
                    str(pergunta_tipo.id): "Contrato com fornecedor estratégico",
                }
            },
        )
        assert preview.status_code == 200
        body = preview.json()
        assert body["progresso_percentual"] == 50.0
        assert body["pcd_sugerido"]
        assert "contrat" in body["ttd_sugerida"].lower() or "fim do contrato" in body["ttd_sugerida"].lower()
        assert len(body["pendencias"]) >= 1


def test_admin_lgpd_protecao_e_anonimizacao() -> None:
    session = FakeAsyncSession()
    admin_user = User(
        id=uuid.uuid4(),
        email="admin-lgpd@example.com",
        nome="Administrador LGPD",
        hashed_password="hash",
        role="admin",
        is_active=True,
        atributos={},
    )
    titular = User(
        id=uuid.uuid4(),
        email="titular@example.com",
        nome="Titular Dados",
        hashed_password="hash",
        role="viewer",
        is_active=True,
        unidade="RJ",
        atributos={},
    )
    session.add(admin_user)
    session.add(titular)

    from app.routers import admin as admin_router

    app = build_test_app(admin_router.router, "/api/v1/admin", session, current_user=admin_user)

    with TestClient(app) as client:
        proteger = client.post(
            f"/api/v1/admin/usuarios/{titular.id}/lgpd/proteger",
            json={
                "cpf": "12345678901",
                "email_secundario": "privado@example.com",
                "campos_extras": {"telefone": "21999999999"},
            },
        )
        assert proteger.status_code == 200
        body = proteger.json()
        assert body["anonimizado"] is False
        assert "cpf" in body["campos_sensiveis"]
        assert body["dados_mascarados"]["cpf"].endswith("-01")

        resumo = client.get(f"/api/v1/admin/usuarios/{titular.id}/lgpd/resumo")
        assert resumo.status_code == 200
        assert resumo.json()["email_mascarado"].endswith("@example.com")

        anonimizar = client.post(f"/api/v1/admin/usuarios/{titular.id}/lgpd/anonimizar")
        assert anonimizar.status_code == 200
        assert anonimizar.json()["anonimizado"] is True
        assert anonimizar.json()["campos_sensiveis"] == []


def test_observabilidade_metrics_summary_com_incidente() -> None:
    observability_store.reset()
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

    from app.routers import health as health_router

    app.include_router(health_router.router)

    @app.get("/api/v1/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/v1/fail")
    async def fail() -> None:
        raise HTTPException(status_code=500, detail="falha simulada")

    with TestClient(app) as client:
        assert client.get("/api/v1/ok").status_code == 200
        assert client.get("/api/v1/ok").status_code == 200
        assert client.get("/api/v1/fail").status_code == 500

        summary = client.get("/metrics/summary")
        assert summary.status_code == 200
        body = summary.json()
        assert body["requests_total"] == 3
        assert body["errors_total"] == 1
        assert body["incidents_open"] >= 1


def test_health_smoke_check_operacional() -> None:
    session = FakeAsyncSession()
    app = build_test_app(health.router, "", session)

    classe = PcdNivel(
        id=uuid.uuid4(),
        pai_id=None,
        tipo="classe",
        codigo="SMK-CL",
        titulo="Classe Smoke",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        filhos=[],
    )
    regra = RegraRetencao(
        id=uuid.uuid4(),
        pcd_nivel_id=classe.id,
        evento_inicio="fim_contrato",
        prazo_dias=30,
        fase_corrente=0,
        fase_intermediaria=0,
        destinacao_final="eliminacao",
        base_legal=None,
        legislacao_ref=None,
        observacoes=None,
        created_at=datetime.now(UTC),
    )
    importacao = ImportacaoAcervo(
        id=uuid.uuid4(),
        nome_arquivo="smoke.csv",
        status="processado",
        mapping={"codigo": "cod"},
        total_registros=1,
        total_sucesso=1,
        total_erros=0,
        resultados=[{"linha": 2, "status": "sucesso", "codigo": "X-1"}],
        observacoes="ok",
        created_at=datetime.now(UTC),
    )
    inventario = InventarioQualidade(
        id=uuid.uuid4(),
        importacao_id=importacao.id,
        total_registros=1,
        score_geral=100,
        score_completude=100,
        score_unicidade=100,
        score_conformidade=100,
        status_qualidade="excelente",
        regras_aplicadas=[],
        indicadores={},
        inconsistencias=[],
        recomendacoes=[],
        comparativo_anterior=None,
        created_at=datetime.now(UTC),
    )
    session.add(classe)
    session.add(regra)
    session.add(importacao)
    session.add(inventario)

    with TestClient(app) as client:
        smoke = client.get("/health/smoke")
        assert smoke.status_code == 200
        body = smoke.json()
        assert body["overall_status"] == "ok"
        assert body["total_checks"] >= 9
        assert body["failed_checks"] == []
        assert body["checks"]["pcd"]["status"] == "ok"
        assert body["checks"]["ttd"]["status"] == "ok"
        assert body["checks"]["integracao"]["status"] == "ok"
        assert body["checks"]["dados_migracao"]["status"] == "ok"
        assert body["checks"]["conhecimento"]["status"] == "ok"
        assert body["checks"]["observabilidade"]["status"] == "ok"


def test_backup_incremental_e_restauracao_parcial() -> None:
    session = FakeAsyncSession()
    app = build_test_app(health.router, "", session)

    classe = PcdNivel(
        id=uuid.uuid4(),
        pai_id=None,
        tipo="classe",
        codigo="CL-BKP",
        titulo="Classe Backup",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        filhos=[],
    )
    regra = RegraRetencao(
        id=uuid.uuid4(),
        pcd_nivel_id=classe.id,
        evento_inicio="fim_contrato",
        prazo_dias=365,
        fase_corrente=0,
        fase_intermediaria=0,
        destinacao_final="eliminacao",
        base_legal=None,
        legislacao_ref=None,
        observacoes=None,
        created_at=datetime.now(UTC),
    )
    session.add(classe)
    session.add(regra)

    with TestClient(app) as client:
        snapshot = client.post(
            "/backup/snapshots",
            json={
                "pcd_nivel_id": str(classe.id),
                "regra_retencao_id": str(regra.id),
            },
        )
        assert snapshot.status_code == 201
        snapshot_id = snapshot.json()["id"]

        listagem = client.get("/backup/snapshots")
        assert listagem.status_code == 200
        assert len(listagem.json()) == 1

        session.pcd.pop(classe.id)
        session.regras.pop(regra.id)

        restore = client.post(f"/backup/snapshots/{snapshot_id}/restore")
        assert restore.status_code == 200
        assert restore.json()["restaurados"]["pcd"] == 1
        assert restore.json()["restaurados"]["regras"] == 1
        assert classe.id in session.pcd
        assert regra.id in session.regras
