# 📌 Matriz de Priorização Frontend (HW1)

**Data:** 10/03/2026  
**Escopo:** Sistema interno (execução enxuta, sem relatório formal de entrega externa)  
**Diretriz visual:** Toda interface deve seguir identidade visual HW1 (tokens + componentes do design system).

---

## Legenda

- **Impacto Frontend Alto**: demanda telas/fluxos centrais, interação intensa ou componentes complexos.
- **Impacto Frontend Médio**: exige interface relevante, porém com menor complexidade de fluxo.
- **Impacto Frontend Baixo**: foco principal em backend/infra; UI é apoio administrativo ou consulta pontual.

**Prioridade UI**
- **P1**: executar no ciclo atual.
- **P2**: executar após núcleo P1.
- **P3**: executar conforme dependências e maturidade backend.

---

## Matriz US → Impacto Frontend

| US | Épico | Impacto Frontend | Prioridade UI | Observação objetiva |
|---|---|---|---|---|
| US-001 | EP1-ENTREVISTAS | **Alto** | **P1** | Catálogo e editor de roteiros dinâmicos são núcleo da experiência de uso. |
| US-002 | EP1-ENTREVISTAS | **Alto** | **P1** | Motor condicional exige fluxo interativo de perguntas e validações em tempo real. |
| US-003 | EP1-ENTREVISTAS | **Alto** | **P1** | Upload de evidências e vínculo com respostas requer UX robusta de anexos. |
| US-004 | EP1-ENTREVISTAS | **Médio** | **P2** | Exibição/ajuste de sugestões automáticas de classes sobre fluxo já existente. |
| US-010 | EP2-PCD | **Alto** | **P1** | Construtor hierárquico do PCD (árvore + formulários) é componente visual crítico. |
| US-011 | EP2-PCD | **Médio** | **P2** | Fluxo de versionamento/aprovação com telas de estado e histórico. |
| US-012 | EP2-PCD | **Médio** | **P2** | Configuração de metadados e segurança demanda formulários administrativos. |
| US-020 | EP3-TTD | **Alto** | **P1** | Cadastro de regras de retenção/eventos exige modelagem visual de regras. |
| US-021 | EP3-TTD | **Médio** | **P2** | Gestão de exceções/legal hold com controles de suspensão e retomada. |
| US-022 | EP3-TTD | **Alto** | **P1** | Geração/validação de ordens e termos envolve fluxo operacional de decisão. |
| US-030 | EP4-CICLO-VIDA | **Baixo** | **P3** | Agendamento e processamento são majoritariamente de motor backend. |
| US-031 | EP4-CICLO-VIDA | **Alto** | **P1** | Workflows com SLA e 4-olhos dependem de telas de tarefa e aprovação. |
| US-032 | EP4-CICLO-VIDA | **Médio** | **P2** | Consulta de selo/pacote de auditoria pede interface de busca e visualização. |
| US-040 | EP5-GOVERNANCA | **Alto** | **P1** | Matriz de rastreabilidade e drill-down exige interface analítica dedicada. |
| US-041 | EP5-GOVERNANCA | **Baixo** | **P3** | Verificação de integridade de logs é predominantemente técnica/backend. |
| US-050 | EP6-INTEGRACAO | **Baixo** | **P3** | APIs REST/GraphQL são foco de integração, com baixa demanda de UI. |
| US-051 | EP6-INTEGRACAO | **Baixo** | **P3** | Eventos internos/webhooks concentram esforço em mensageria e contratos. |
| US-052 | EP6-INTEGRACAO | **Médio** | **P2** | Importação com mapeamento de campos requer tela operacional específica. |
| US-060 | EP7-SEGURANCA | **Médio** | **P2** | Administração RBAC/ABAC precisa de painel de políticas e perfis. |
| US-061 | EP7-SEGURANCA | **Baixo** | **P3** | LGPD/criptografia é majoritariamente infraestrutura e processamento de dados. |
| US-070 | EP8-OBSERVABILIDADE | **Médio** | **P2** | Dashboards de telemetria/SLOs possuem consumo visual recorrente. |
| US-071 | EP8-OBSERVABILIDADE | **Baixo** | **P3** | HA/DR e backup têm baixa superfície de UI no ciclo inicial. |
| US-080 | EP9-DADOS-MIGRACAO | **Médio** | **P2** | Inventário e score de qualidade exigem visão tabular/indicadores. |
| US-081 | EP9-DADOS-MIGRACAO | **Médio** | **P2** | Planejamento por ondas requer telas de acompanhamento e dependências. |
| US-090 | EP10-UX-ADOCao | **Alto** | **P1** | Assistente de entrevista é funcionalidade orientada diretamente à experiência. |
| US-091 | EP10-UX-ADOCao | **Médio** | **P2** | Base de conhecimento e trilhas pedem navegação e consumo de conteúdo. |

---

## Sequência Recomendada (Execução Interna)

1. **P1 (núcleo de valor visual):** US-001, US-002, US-003, US-010, US-020, US-022, US-031, US-040, US-090.
2. **P2 (consolidação funcional):** US-004, US-011, US-012, US-021, US-032, US-052, US-060, US-070, US-080, US-081, US-091.
3. **P3 (suporte técnico e operacional):** US-030, US-041, US-050, US-051, US-061, US-071.

---

## Nota de Governança

- Esta matriz orienta prioridade de **frontend**; prioridade final de execução pode ser ajustada por dependências técnicas entre squads.
- Toda entrega de UI deve manter consistência com a identidade visual HW1 e evitar cores hardcoded.