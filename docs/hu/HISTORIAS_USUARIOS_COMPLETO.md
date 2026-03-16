# 📚 Histórias de Usuários — Backlog Completo

**Projeto:** Gestão de Apoio Arquivístico (HW1)  
**Data:** 10/03/2026  
**Total de Histórias:** 26 US

**Contexto:** Sistema de uso interno corporativo, com acompanhamento enxuto no board e sem exigência de relatórios formais de entrega externa.

---

## 🧭 Diretrizes Transversais (Interno + Frontend HW1)

- As histórias devem ser refinadas para uso interno, priorizando fluxo operacional e rastreabilidade essencial.
- Evidências de avanço devem ser objetivas (status do board, critérios de aceite e changelog curto).
- Para histórias com impacto em interface, aplicar identidade visual HW1 obrigatoriamente:
	- tokens de tema e componentes do design system;
	- consistência de contraste e espaçamento;
	- evitar cores hardcoded fora do padrão HW1.

---

## 🚀 Próxima Etapa de Execução

- Foco imediato em EP1 e EP2 (base funcional de entrevistas + classificação PCD).
- Concluir fluxos de UI com padrão HW1 antes de expandir para módulos dependentes.
- Manter backlog técnico orientado por valor interno (operações, conformidade e produtividade da equipe).

---

## 📑 Índice por Épico

- [EP1 — Entrevistas](#ep1---entrevistas) (4 US)
- [EP2 — Classificação de Documentos (PCD)](#ep2---classificação-de-documentos-pcd) (3 US)
- [EP3 — Tabela de Temporalidade e Destinação (TTD)](#ep3---tabela-de-temporalidade-e-destinação-ttd) (3 US)
- [EP4 — Ciclo de Vida dos Documentos](#ep4---ciclo-de-vida-dos-documentos) (3 US)
- [EP5 — Governança](#ep5---governança) (2 US)
- [EP6 — Integração Interna entre Módulos](#ep6---integração-interna-entre-módulos) (3 US)
- [EP7 — Segurança](#ep7---segurança) (2 US)
- [EP8 — Observabilidade](#ep8---observabilidade) (2 US)
- [EP9 — Dados e Migração](#ep9---dados-e-migração) (2 US)
- [EP10 — UX e Adoção](#ep10---ux-e-adoção) (2 US)

---

## 🎯 EP1 — Entrevistas

### US-001 — Catálogo de Roteiros Dinâmicos
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Arquivista, quero cadastrar e versionar roteiros por área/processo com lógica condicional, para identificar séries documentais, base legal e metadados com precisão.

**Principais Recursos:**
- Editor com autosave (30s) e validações
- Perguntas mapeiam decisões (classe, evento, base legal, risco, sigilo)
- Versionamento com justificativa
- Ramificações condicionais (ex: se LGPD, exibir blocos específicos)

---

### US-002 — Motor Condicional com Lógica Booleana
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como PO, quero que o sistema execute roteiros com lógica AND/OR/NOT entre respostas, para permitir árvores de decisão complexas e automação de classificação.

**Principais Recursos:**
- Operadores booleanos (AND, OR, NOT)
- Saltos entre seções baseados em condições
- Simulador de execução (dry-run)
- Auditoria de decisões tomadas

---

### US-003 — Evidências de Classificação e Anexos
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Auditor, quero que cada classificação documental seja rastreável com evidências de decisão e anexos legais/normativos, para garantir conformidade.

**Principais Recursos:**
- Anexação de legislação (PDF), jurisprudência
- Histórico de quem decidiu e quando
- Rastreabilidade completa de mudanças
- Reprodução de passos da entrevista

---

### US-004 — Mapeamento de Roteiros para Classes Documentais
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Classificador, quero que o roteiro mapeie diretamente para classes documentais (CONARQ), para evitar erros humans
os e acelerar classificação em massa.

**Principais Recursos:**
- Mapeamento automático (roteiro → CONARQ ID)
- Validação contra padrão CONARQ
- Batch processing de documentos
- Checklist de conformidade interno

---

## 📂 EP2 — Classificação de Documentos (PCD)

### US-010 — Modelagem Hierárquica de Plano de Classificação
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Classificador, quero estruturar o plano de classificação em hierarquias (Fundo → Subgrupo → Série → Subserie), para representar fidelidade ao contexto organizacional.

**Principais Recursos:**
- Interface de árvore (drag-and-drop)
- Validação de unicidade por nível
- Export/import de estruturas (XML, JSON)
- Suporte a múltiplos planos simultâneos

---

### US-011 — Versionamento e Controle de Mudanças do PCD
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Gestor, quero versionar o plano de classificação com rastreamento de alterações, para manter histórico e rolar back se necessário.

**Principais Recursos:**
- Versionamento semântico (1.0, 1.1, etc)
- Diff visual entre versões
- Aprovação com workflow
- Notificação de mudanças aos usuários

---

### US-012 — Metadados e Controle de Acesso ao PCD
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Admin, quero definir metadados (responsável, data, status) e permissões de acesso ao plano de classificação, para garantir governança.

**Principais Recursos:**
- RBAC (role-based access control) por classe
- Matriz de permissões (view, edit, approve)
- Auditoria de acesso
- Labels e tags para organização

---

## 📅 EP3 — Tabela de Temporalidade e Destinação (TTD)

### US-020 — Regras de Retenção, Eventos e Prazos
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Gestor de Documentos, quero definir regras de retenção baseadas em eventos (ex: fim de contrato + 5 anos), para automatizar prazos de guarda.

**Principais Recursos:**
- Biblioteca de eventos (fim de contrato, rescisão, prescrição)
- Cálculos de prazos automáticos
- Suporte a legislação (CLT, CC, LGPD)
- Simulador de datas (quando será descartado?)

---

### US-021 — Exceções, Holds e Litígios
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Comply Officer, quero aplicar holds (congelamento) em documentos por litígio ou investigação, para suspender automaticamente destruição.

**Principais Recursos:**
- Hold por série, período, critério custom
- Motivo e data de expiração do hold
- Notificação automática ao expirar
- Painel interno de documentos em hold

---

### US-022 — Ordens de Destinação e Termos de Destruição
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Analista, quero gerar ordens de destinação (eliminação ou arquivo permanente) com assinatura eletrônica, para formalizar destruição em conformidade.

**Principais Recursos:**
- Template de Termo de Eliminação/Recolhimento
- Assinatura digital (certificado A1/A3)
- QR code de rastreamento
- Integração com destino (lixo, arquivo, microfilme)

---

## ♻️ EP4 — Ciclo de Vida dos Documentos

### US-030 — Motor de Retenção e Descarte Automático
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Sistema, quero executar rotinas diárias de análise de prazos e gerar automaticamente ordens de descarte, para eliminar manualmente tarefas de rastreamento.

**Principais Recursos:**
- Job scheduler (Cron/Quartz)
- API de retenção integrada
- Notificação de prazos vencidos
- Painel operacional de documentos a descartar

---

### US-031 — Workflows de Avaliação e Auditoria
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Auditor, quero que cada documento passe por workflow de avaliação (originador → supervisor → gestor), para validar classificação e retenção antes de descarte.

**Principais Recursos:**
- States: Avaliação → Aprovação → Arquivado/Descartado
- Comentários e justificativas em cada etapa
- SLA de aprovação (de X dias)
- Escalação automática se vencida

---

### US-032 — Selo de Evidência Criptográfico
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Compliance, quero que cada documento destruído seja marcado com selo criptográfico (hash + timestamp), para prova de destruição irrefutável.

**Principais Recursos:**
- Hash (SHA-256) do documento + metadados
- Timestamp do Servidor de Tempo (STN)
- Blockchain mínimo (cadeia de hashes)
- Certificado de destruição assinado

---

## 🏛️ EP5 — Governança

### US-040 — Matriz de Rastreabilidade entre Legislação → TTD → Série
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Compliance Officer, quero mapear cada série documental para base legal (artigo de lei → norma interna → TTD), para auditoria de conformidade.

**Principais Recursos:**
- Matriz visual (legislação × série)
- Query reversa (dado um artigo, quais séries?)
- Consulta filtrada de conformidade
- Validação automática de gaps (séries sem lei)

---

### US-041 — Logs WORM (Write Once Read Many) e Hashchain
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Auditor Interno, quero garantir que logs de operações (criação, alteração, eliminação) sejam imutáveis, para sustentar compliance e auditoria contínua.

**Principais Recursos:**
- Armazenamento WORM (S3 Object Lock, Azure Immutable)
- Hashchain (cada log referencia o anterior)
- API read-only sobre logs
- Verificação de integridade no painel (validação de hashes)

---

## 🔌 EP6 — Integração Interna entre Módulos

### US-050 — APIs REST/GraphQL de Acesso ao Catálogo
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Desenvolvedor Interno, quero consumir APIs (REST/GraphQL) para query de séries, plano de classificação e roteiros, para integrar módulos internos da plataforma.

**Principais Recursos:**
- Endpoints: `/series`, `/plano-classificacao`, `/roteiros`
- GraphQL schema com queries e mutations
- Rate limiting e autenticação OAuth2
- Documentação OpenAPI 3.0

---

### US-051 — Webhooks e Eventos Assíncronos
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Módulo Interno, quero receber eventos (série criada, documento retido, ordem de descarte gerada), para sincronizar estado entre componentes da plataforma.

**Principais Recursos:**
- Eventos: `serie.created`, `document.retained`, `disposal.ordered`
- Retry mechanism (exponential backoff)
- Painel de eventos internos
- Log operacional de eventos e falhas

---

### US-052 — Importação Interna de Acervo e Mapeamento
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Admin, quero importar acervos e mapear campos para a estrutura interna, para acelerar adoção sem integrações externas obrigatórias.

**Principais Recursos:**
- Importação CSV/JSON de acervo
- Mapeamento de campos (drag-and-drop)
- Validação de consistência
- Reprocessamento controlado

---

## 🔒 EP7 — Segurança

### US-060 — RBAC (Role-Based) / ABAC (Attribute-Based) de Acesso
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Admin, quero definir controles de acesso granulares (ex: apenas Auditor vê séries sensíveis), para garantir segregação de duties e confidencialidade.

**Principais Recursos:**
- Roles: Admin, Gestor, Classificador, Auditor, Diretor
- Attributes: departamento, nível de sigilo, projeto
- Políticas dinâmicas (ex: "se sigilo=Confidencial E role=Auditor ENTÃO read-only")
- Auditoria de quem fez o quê

---

### US-061 — LGPD: Criptografia, Anonimização, Direito ao Esquecimento
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Compliance, quero que dados pessoais sejam criptografados em repouso e trânsito, com suporte a anonimização e direito ao esquecimento (LGPD), para garantir privacidade.

**Principais Recursos:**
- Criptografia AES-256 (repouso) / TLS 1.3 (trânsito)
- Masking de dados sensíveis (CPF, email)
- Right to be forgotten (soft delete com TTL)
- Checklist operacional de conformidade LGPD

---

## 📊 EP8 — Observabilidade

### US-070 — Telemetria, SLOs e Alertas
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como DevOps, quero medir SLOs (tempo de query, taxa de erro) e receber alertas, para garantir performance e disponibilidade.

**Principais Recursos:**
- Prometheus metrics: query latency, retention jobs, API errors
- Grafana dashboards por módulo
- Alertas (PagerDuty) se latency > 500ms
- SLA dashboard (uptime, error rate)

---

### US-071 — HA/DR, Backup e Disaster Recovery
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Compliance Officer, quero que o sistema tenha HA/DR (failover automático, backup diário, RTO/RPO mínimos), para zero downtime e recuperação rápida.

**Principais Recursos:**
- Active-passive replication (PostgreSQL Streaming)
- Backup diário com retenção de 30 dias
- RTO <1h, RPO <15 min
- Teste de DR mensal
- Plan de recuperação documentado

---

## 📦 EP9 — Dados e Migração

### US-080 — Inventário de Qualidade de Dados
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Master Data Manager, quero avaliar qualidade dos dados migrados (completude, unicidade, conformidade), para identificar gaps e limpar dados.

**Principais Recursos:**
- Scan de data quality (duplicatas, nulos, formatos inválidos)
- Painel de qualidade (% completo, % válido)
- Rules de cleansing (trim, normalize)
- Histórico de scores (antes/depois)

---

### US-081 — Estratégia de Corte de Ondas e Rollback
**Status:** Backlog  
**Prioridade:** Alta  
**Pontos:** TBD

**Descrição:**
Como Migration Manager, quero executar migração em ondas (Phase 1: Legislação, Phase 2: Séries, Phase 3: TTD), com rollback por fase se necessário.

**Principais Recursos:**
- Wave planning (sequência, dependências)
- Data validation após cada wave
- Rollback script testado
- Notificação interna opcional por wave

---

## 💡 EP10 — UX e Adoção

### US-090 — Assistente Virtual para Entrevistas
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Usuário Novato, quero que um assistente chatbot guie minha entrevista em linguagem natural, respondendo dúvidas sobre legislação e fornecendo sugestões inteligentes.

**Principais Recursos:**
- Chatbot com LLM (GPT-4 Fine-tuned)
- Base de conhecimento (legislação, jurisprudência)
- Sugestões context-aware
- Feedback loop (melhorar modelo com interações)

---

### US-091 — Treinamento, Base de Conhecimento e Onboarding
**Status:** Backlog  
**Prioridade:** Média  
**Pontos:** TBD

**Descrição:**
Como Gestor de Adoção, quero disponibilizar vídeos, FAQs e guias rápidos para acelerar adoção e reduzir ticket de suporte.

**Principais Recursos:**
- Portal de aprendizado (videoteca, FAQ)
- Trilha interna por perfil
- Checklist de onboarding
- Analytics de engajamento (% conclusão)

---

## 📊 Resumo Estatístico

| Épico | Histórias | Status |
|-------|-----------|--------|
| EP1 — Entrevistas | 4 | Backlog |
| EP2 — PCD | 3 | Backlog |
| EP3 — TTD | 3 | Backlog |
| EP4 — Ciclo de Vida | 3 | Backlog |
| EP5 — Governança | 2 | Backlog |
| EP6 — Integração | 3 | Backlog |
| EP7 — Segurança | 2 | Backlog |
| EP8 — Observabilidade | 2 | Backlog |
| EP9 — Dados | 2 | Backlog |
| EP10 — UX | 2 | Backlog |
| **TOTAL** | **26 US** | **100% Backlog** |

---

## 🎯 Próximas Etapas

1. **Refinamento** — Quebrar US em tasks de dev
2. **Estimativa** — Atribuir story points (Planning Poker)
3. **Priorização** — Ordenar por valor/risco para Sprint Planning
4. **Dependências** — Mapear bloqueadores (ex: EP1 → EP2)

---

> **Backlog HW1** — Gestão de Apoio Arquivístico  
> Gerado em: 05/03/2026  
> Total: 26 Histórias de Usuários
