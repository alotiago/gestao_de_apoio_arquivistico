"""Catálogo de base de conhecimento e onboarding para adoção interna."""

import uuid
from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class KnowledgeBaseStore:
    templates: list[dict] = field(default_factory=list)
    trilhas: list[dict] = field(default_factory=list)
    progressos: dict[str, dict[str, dict]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.templates:
            self.templates = [
                {
                    "slug": "termo-eliminacao",
                    "titulo": "Termo de Eliminação",
                    "categoria": "TTD",
                    "descricao": "Template oficial para formalizar eliminação documental com checklist de conformidade.",
                    "tags": ["termo", "eliminação", "ttd"],
                    "template_content": "# Termo de Eliminação\n\n## Identificação\n- Classe documental:\n- Base legal:\n- Responsável:\n",
                    "guide_content": "# Guia de Preenchimento — Termo de Eliminação\n\n1. Informe a classe documental validada no PCD.\n2. Anexe a ordem de destinação assinada.\n3. Registre a base legal da eliminação.\n",
                },
                {
                    "slug": "plano-classificacao",
                    "titulo": "Template de Plano de Classificação",
                    "categoria": "PCD",
                    "descricao": "Modelo padrão para cadastro e revisão de classes e séries documentais.",
                    "tags": ["pcd", "classificação", "template"],
                    "template_content": "# Plano de Classificação\n\n| Código | Título | Nível | Responsável |\n|---|---|---|---|\n",
                    "guide_content": "# Guia de Preenchimento — Plano de Classificação\n\n- Utilize códigos únicos por nível.\n- Valide sigilo e metadados obrigatórios.\n",
                },
                {
                    "slug": "roteiro-implantacao",
                    "titulo": "Roteiro de Implantação por Unidade",
                    "categoria": "Onboarding",
                    "descricao": "Checklist operativo para preparar usuários e dados antes da entrada em produção.",
                    "tags": ["onboarding", "implantação", "checklist"],
                    "template_content": "# Roteiro de Implantação\n\n- Treinamento concluído\n- Templates publicados\n- Dados validados\n",
                    "guide_content": "# Guia de Aplicação — Implantação\n\n1. Execute treinamento por perfil.\n2. Valide dados e templates oficiais.\n3. Registre aceite da unidade.\n",
                },
            ]
        if not self.trilhas:
            self.trilhas = [
                {
                    "id": str(uuid.uuid4()),
                    "nome": "Trilha do Arquivista",
                    "perfil": "Arquivista",
                    "duracao_estimada_min": 90,
                    "etapas": ["Conhecer o PCD", "Validar TTD", "Gerar termos", "Consultar auditoria"],
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome": "Trilha do Analista de Migração",
                    "perfil": "Analista",
                    "duracao_estimada_min": 75,
                    "etapas": ["Importar acervo", "Gerar inventário", "Planejar ondas", "Executar rollback"],
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome": "Trilha do Gestor",
                    "perfil": "Gestor",
                    "duracao_estimada_min": 60,
                    "etapas": ["Acompanhar dashboard", "Aprovar políticas", "Validar prontidão"],
                },
            ]

    def search_templates(self, query: str | None) -> list[dict]:
        if not query:
            return deepcopy(self.templates)
        search = query.lower().strip()
        return [
            deepcopy(item)
            for item in self.templates
            if search in item["titulo"].lower()
            or search in item["descricao"].lower()
            or any(search in tag.lower() for tag in item["tags"])
        ]

    def get_template(self, slug: str) -> dict | None:
        for item in self.templates:
            if item["slug"] == slug:
                return deepcopy(item)
        return None

    def list_trilhas(self, user_id: str) -> list[dict]:
        resultado: list[dict] = []
        progresso_usuario = self.progressos.get(user_id, {})
        for trilha in self.trilhas:
            progresso = deepcopy(progresso_usuario.get(trilha["id"], {}))
            total_etapas = len(trilha["etapas"])
            concluidas = int(progresso.get("etapas_concluidas", 0))
            percentual = round((concluidas / total_etapas) * 100, 2) if total_etapas else 0
            resultado.append(
                {
                    **deepcopy(trilha),
                    "etapas_concluidas": concluidas,
                    "progresso_percentual": percentual,
                    "badge_emitido": percentual == 100,
                }
            )
        return resultado

    def update_progress(self, user_id: str, trilha_id: str, etapas_concluidas: int) -> dict | None:
        trilha = next((item for item in self.trilhas if item["id"] == trilha_id), None)
        if not trilha:
            return None

        total_etapas = len(trilha["etapas"])
        concluidas = max(0, min(etapas_concluidas, total_etapas))
        progresso_usuario = self.progressos.setdefault(user_id, {})
        progresso_usuario[trilha_id] = {"etapas_concluidas": concluidas}
        percentual = round((concluidas / total_etapas) * 100, 2) if total_etapas else 0
        return {
            **deepcopy(trilha),
            "etapas_concluidas": concluidas,
            "progresso_percentual": percentual,
            "badge_emitido": percentual == 100,
        }


knowledge_base_store = KnowledgeBaseStore()
