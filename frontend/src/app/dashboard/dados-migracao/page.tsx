"use client";

import { useMemo, useState } from "react";
import api from "@/lib/api";
import {
  useImportacoesAcervo,
  useInventariosQualidade,
  useOndasMigracao,
  useRegrasCleansing,
} from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ImportacaoItem = {
  id: string;
  nome_arquivo: string;
  status: string;
  total_registros: number;
  total_sucesso: number;
  total_erros: number;
  created_at: string;
};

type RegraCleansing = {
  id: string;
  nome: string;
  tipo: string;
  campo?: string | null;
  ativo: boolean;
  created_at: string;
};

type InventarioQualidade = {
  id: string;
  importacao_id: string;
  total_registros: number;
  score_geral: number;
  score_completude: number;
  score_unicidade: number;
  score_conformidade: number;
  status_qualidade: string;
  indicadores: {
    campos_nulos?: Record<string, number>;
    invalidos_formato?: Record<string, number>;
    duplicidades_codigo?: string[];
    registros_conformes?: number;
    registros_com_erro?: number;
    transformacoes_aplicadas?: number;
    amostra_transformacoes?: Array<{
      campo: string;
      antes: string;
      depois: string;
      regra: string;
    }>;
  };
  recomendacoes: string[];
  comparativo_anterior?: {
    score_geral_delta: number;
    completude_delta: number;
    unicidade_delta: number;
    conformidade_delta: number;
  } | null;
  created_at: string;
};

type OndaMigracao = {
  id: string;
  nome: string;
  unidade: string;
  processo: string;
  ordem: number;
  status: string;
  estrategia_corte: string;
  data_corte_planejada?: string | null;
  inventario_id?: string | null;
  dependencias: Array<{
    id: string;
    nome: string;
    status: string;
    tipo: string;
  }>;
  fases: Array<{
    id: string;
    nome: string;
    ordem: number;
    status: string;
    rollback_script: string[];
  }>;
  historico: Array<{
    evento: string;
    timestamp: string;
  }>;
  created_at: string;
};

type OndaValidacao = {
  onda_id: string;
  pronta: boolean;
  status_planejamento: string;
  score_qualidade: number | null;
  dependencias_pendentes: string[];
  fases_pendentes: string[];
  checklist: string[];
};

const tiposRegra = [
  { value: "trim", label: "Trim" },
  { value: "collapse_spaces", label: "Colapsar espaços" },
  { value: "upper", label: "Uppercase" },
  { value: "title_case", label: "Title Case" },
];

export default function DadosMigracaoPage() {
  const [selectedImportacaoId, setSelectedImportacaoId] = useState("");
  const [selectedRuleIds, setSelectedRuleIds] = useState<string[]>([]);
  const [usarSomenteSucesso, setUsarSomenteSucesso] = useState(false);
  const [nomeRegra, setNomeRegra] = useState("");
  const [tipoRegra, setTipoRegra] = useState("trim");
  const [campoRegra, setCampoRegra] = useState("");
  const [statusFiltroOnda, setStatusFiltroOnda] = useState("");
  const [nomeOnda, setNomeOnda] = useState("");
  const [unidadeOnda, setUnidadeOnda] = useState("");
  const [processoOnda, setProcessoOnda] = useState("");
  const [ordemOnda, setOrdemOnda] = useState("1");
  const [dataCorteOnda, setDataCorteOnda] = useState("");
  const [inventarioOndaId, setInventarioOndaId] = useState("");
  const [dependenciaIds, setDependenciaIds] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [validacaoAtual, setValidacaoAtual] = useState<OndaValidacao | null>(null);

  const { data: importacoesRaw } = useImportacoesAcervo();
  const { data: inventariosRaw, mutate: mutateInventarios, isLoading: inventariosLoading } =
    useInventariosQualidade(selectedImportacaoId || undefined);
  const { data: inventariosGlobaisRaw } = useInventariosQualidade();
  const { data: regrasRaw, mutate: mutateRegras } = useRegrasCleansing(true);
  const { data: ondasRaw, mutate: mutateOndas } = useOndasMigracao(statusFiltroOnda || undefined);

  const importacoes = useMemo(
    () => (importacoesRaw as ImportacaoItem[] | undefined) ?? [],
    [importacoesRaw]
  );
  const inventarios = useMemo(
    () => (inventariosRaw as InventarioQualidade[] | undefined) ?? [],
    [inventariosRaw]
  );
  const inventariosGlobais = useMemo(
    () => (inventariosGlobaisRaw as InventarioQualidade[] | undefined) ?? [],
    [inventariosGlobaisRaw]
  );
  const regras = useMemo(
    () => (regrasRaw as RegraCleansing[] | undefined) ?? [],
    [regrasRaw]
  );
  const ondas = useMemo(
    () => (ondasRaw as OndaMigracao[] | undefined) ?? [],
    [ondasRaw]
  );

  const inventarioAtual = inventarios[0] ?? null;
  const importacaoSelecionada = useMemo(
    () => importacoes.find((item) => item.id === selectedImportacaoId) ?? null,
    [importacoes, selectedImportacaoId]
  );

  async function handleGerarInventario() {
    if (!selectedImportacaoId) {
      setErrorMessage("Selecione uma importação para gerar o inventário.");
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("scan");
    try {
      const { data } = await api.post<InventarioQualidade>("/dados-migracao/inventarios/scan", {
        importacao_id: selectedImportacaoId,
        regra_ids: selectedRuleIds,
        incluir_apenas_sucesso: usarSomenteSucesso,
      });
      setSuccessMessage(`Inventário gerado com score ${data.score_geral.toFixed(2)}.`);
      await mutateInventarios();
    } catch {
      setErrorMessage("Falha ao gerar inventário de qualidade.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleCriarRegra() {
    if (!nomeRegra.trim()) {
      setErrorMessage("Informe um nome para a regra de cleansing.");
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("regra");
    try {
      await api.post("/dados-migracao/regras-cleansing", {
        nome: nomeRegra,
        tipo: tipoRegra,
        campo: campoRegra.trim() || null,
        configuracao: {},
        ativo: true,
      });
      setNomeRegra("");
      setCampoRegra("");
      setSuccessMessage("Regra de cleansing cadastrada com sucesso.");
      await mutateRegras();
    } catch {
      setErrorMessage("Falha ao criar regra de cleansing.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleCriarOnda() {
    if (!nomeOnda.trim() || !unidadeOnda.trim() || !processoOnda.trim()) {
      setErrorMessage("Informe nome, unidade e processo para criar a onda.");
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("onda");
    try {
      await api.post("/dados-migracao/ondas", {
        nome: nomeOnda,
        unidade: unidadeOnda,
        processo: processoOnda,
        ordem: Number(ordemOnda) || 1,
        estrategia_corte: "ondas",
        data_corte_planejada: dataCorteOnda ? new Date(dataCorteOnda).toISOString() : null,
        inventario_id: inventarioOndaId || null,
        dependencia_ids: dependenciaIds,
        fases: [],
      });
      setNomeOnda("");
      setUnidadeOnda("");
      setProcessoOnda("");
      setOrdemOnda("1");
      setDataCorteOnda("");
      setInventarioOndaId("");
      setDependenciaIds([]);
      setSuccessMessage("Onda de migração criada com sucesso.");
      await mutateOndas();
    } catch {
      setErrorMessage("Falha ao criar onda de migração.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleValidarOnda(ondaId: string) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`validar-${ondaId}`);
    try {
      const { data } = await api.post<OndaValidacao>(`/dados-migracao/ondas/${ondaId}/validar`);
      setValidacaoAtual(data);
      await mutateOndas();
    } catch {
      setErrorMessage("Falha ao validar a onda selecionada.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleConcluirOnda(ondaId: string) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`concluir-${ondaId}`);
    try {
      await api.patch(`/dados-migracao/ondas/${ondaId}/status`, { status: "concluida" });
      setSuccessMessage("Onda marcada como concluída.");
      await mutateOndas();
    } catch {
      setErrorMessage("Falha ao concluir a onda.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleRollbackOnda(ondaId: string) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`rollback-${ondaId}`);
    try {
      await api.post(`/dados-migracao/ondas/${ondaId}/rollback`, {
        motivo: "Rollback operacional acionado pelo planner visual",
      });
      setSuccessMessage("Rollback da onda executado com sucesso.");
      await mutateOndas();
    } catch {
      setErrorMessage("Falha ao executar rollback da onda.");
    } finally {
      setLoadingAction(null);
    }
  }

  function toggleRule(ruleId: string) {
    setSelectedRuleIds((current) =>
      current.includes(ruleId) ? current.filter((id) => id !== ruleId) : [...current, ruleId]
    );
  }

  function toggleDependencia(ondaId: string) {
    setDependenciaIds((current) =>
      current.includes(ondaId) ? current.filter((id) => id !== ondaId) : [...current, ondaId]
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dados &amp; Migração</h1>
        <p className="text-muted-foreground">
          EP9 (US-080 e US-081): qualidade do acervo, planner por ondas e rollback operacional
        </p>
      </div>

      {errorMessage ? (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {errorMessage}
        </div>
      ) : null}
      {successMessage ? (
        <div className="rounded-lg border border-primary/20 bg-primary/10 p-3 text-sm text-primary">
          {successMessage}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Gerar inventário de qualidade</CardTitle>
            <CardDescription>
              {importacoes.length} importação(ões) disponíveis para avaliação de completude, unicidade e conformidade.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <select
              value={selectedImportacaoId}
              onChange={(event) => setSelectedImportacaoId(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Selecione uma importação</option>
              {importacoes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome_arquivo} · {item.status} · {item.total_registros} registro(s)
                </option>
              ))}
            </select>

            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={usarSomenteSucesso}
                onChange={(event) => setUsarSomenteSucesso(event.target.checked)}
              />
              Considerar apenas linhas com status de sucesso
            </label>

            <div className="space-y-2 rounded-md border border-border p-3">
              <p className="text-sm font-medium text-foreground">Regras ativas de cleansing</p>
              {regras.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Nenhuma regra cadastrada. O scan usará regras padrão de trim e normalização.
                </p>
              ) : (
                regras.map((regra) => (
                  <label key={regra.id} className="flex items-center gap-2 text-sm text-foreground">
                    <input
                      type="checkbox"
                      checked={selectedRuleIds.includes(regra.id)}
                      onChange={() => toggleRule(regra.id)}
                    />
                    <span>
                      {regra.nome} · {regra.tipo}
                      {regra.campo ? ` · campo ${regra.campo}` : " · todos os campos"}
                    </span>
                  </label>
                ))
              )}
            </div>

            <Button type="button" onClick={handleGerarInventario} disabled={loadingAction !== null}>
              {loadingAction === "scan" ? "Gerando..." : "Gerar inventário"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Nova regra de cleansing</CardTitle>
            <CardDescription>
              Cadastre regras operacionais para padronizar os dados antes do corte de migração.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              value={nomeRegra}
              onChange={(event) => setNomeRegra(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Nome da regra"
            />
            <select
              value={tipoRegra}
              onChange={(event) => setTipoRegra(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {tiposRegra.map((tipo) => (
                <option key={tipo.value} value={tipo.value}>
                  {tipo.label}
                </option>
              ))}
            </select>
            <input
              value={campoRegra}
              onChange={(event) => setCampoRegra(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Campo alvo opcional (ex.: codigo)"
            />
            <Button type="button" variant="outline" onClick={handleCriarRegra} disabled={loadingAction !== null}>
              {loadingAction === "regra" ? "Salvando..." : "Cadastrar regra"}
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Score Geral</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">{inventarioAtual?.score_geral?.toFixed(2) ?? "0.00"}</p>
            <p className="text-xs text-muted-foreground">Status: {inventarioAtual?.status_qualidade ?? "sem scan"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Completude</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">{inventarioAtual?.score_completude?.toFixed(2) ?? "0.00"}%</p>
            <p className="text-xs text-muted-foreground">Campos obrigatórios preenchidos</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Unicidade</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">{inventarioAtual?.score_unicidade?.toFixed(2) ?? "0.00"}%</p>
            <p className="text-xs text-muted-foreground">Duplicidades por código documental</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Conformidade</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">{inventarioAtual?.score_conformidade?.toFixed(2) ?? "0.00"}%</p>
            <p className="text-xs text-muted-foreground">Registros aderentes ao padrão</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <CardTitle>Resumo do scan atual</CardTitle>
            <CardDescription>
              {importacaoSelecionada
                ? `Importação selecionada: ${importacaoSelecionada.nome_arquivo}`
                : "Selecione uma importação para exibir o resumo."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!inventarioAtual ? (
              <p className="text-sm text-muted-foreground">
                {inventariosLoading ? "Carregando histórico..." : "Nenhum inventário gerado para a seleção atual."}
              </p>
            ) : (
              <>
                <p className="text-sm text-foreground">
                  Registros avaliados: <strong>{inventarioAtual.total_registros}</strong> · Conformes: {inventarioAtual.indicadores.registros_conformes ?? 0} · Com erro: {inventarioAtual.indicadores.registros_com_erro ?? 0}
                </p>
                <p className="text-sm text-muted-foreground">
                  Duplicidades detectadas: {(inventarioAtual.indicadores.duplicidades_codigo ?? []).join(", ") || "nenhuma"}
                </p>
                <div className="space-y-1">
                  {Object.entries(inventarioAtual.indicadores.campos_nulos ?? {}).map(([campo, total]) => (
                    <p key={campo} className="text-xs text-muted-foreground">
                      Nulos em {campo}: {total}
                    </p>
                  ))}
                </div>
                <div className="space-y-1">
                  {Object.entries(inventarioAtual.indicadores.invalidos_formato ?? {}).map(([campo, total]) => (
                    <p key={campo} className="text-xs text-muted-foreground">
                      Formatos inválidos em {campo}: {total}
                    </p>
                  ))}
                </div>
                {inventarioAtual.comparativo_anterior ? (
                  <div className="rounded-md border border-border p-3 text-xs text-muted-foreground">
                    <p>Δ score geral: {inventarioAtual.comparativo_anterior.score_geral_delta}</p>
                    <p>Δ completude: {inventarioAtual.comparativo_anterior.completude_delta}</p>
                    <p>Δ unicidade: {inventarioAtual.comparativo_anterior.unicidade_delta}</p>
                    <p>Δ conformidade: {inventarioAtual.comparativo_anterior.conformidade_delta}</p>
                  </div>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recomendações e histórico</CardTitle>
            <CardDescription>
              Histórico de scores antes/depois para orientar cleansing e corte por ondas.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {(inventarioAtual?.recomendacoes ?? []).map((recomendacao) => (
                <div key={recomendacao} className="rounded-md border border-primary/20 bg-primary/5 p-3 text-sm text-foreground">
                  {recomendacao}
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">Últimos inventários</p>
              {inventarios.map((inventario) => (
                <div key={inventario.id} className="rounded-md border border-border p-3">
                  <p className="text-sm font-medium text-foreground">
                    Score {inventario.score_geral.toFixed(2)} · {inventario.status_qualidade}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(inventario.created_at).toLocaleString("pt-BR")} · {inventario.total_registros} registro(s)
                  </p>
                </div>
              ))}
            </div>

            {inventarioAtual?.indicadores.amostra_transformacoes?.length ? (
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">Amostra de transformações</p>
                {inventarioAtual.indicadores.amostra_transformacoes.map((item, index) => (
                  <div key={`${item.campo}-${index}`} className="rounded-md border border-border p-3 text-xs text-muted-foreground">
                    <p className="font-medium text-foreground">{item.regra} · campo {item.campo}</p>
                    <p>Antes: {item.antes}</p>
                    <p>Depois: {item.depois}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <CardTitle>Planejar onda de migração</CardTitle>
            <CardDescription>
              Vincule a onda ao inventário mais recente e defina dependências antes do corte por unidade/processo.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              value={nomeOnda}
              onChange={(event) => setNomeOnda(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Nome da onda"
            />
            <input
              value={unidadeOnda}
              onChange={(event) => setUnidadeOnda(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Unidade responsável"
            />
            <input
              value={processoOnda}
              onChange={(event) => setProcessoOnda(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Processo / domínio de dados"
            />

            <div className="grid gap-3 md:grid-cols-2">
              <input
                value={ordemOnda}
                onChange={(event) => setOrdemOnda(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Ordem"
                inputMode="numeric"
              />
              <input
                type="date"
                value={dataCorteOnda}
                onChange={(event) => setDataCorteOnda(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            <select
              value={inventarioOndaId}
              onChange={(event) => setInventarioOndaId(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Selecione um inventário de qualidade</option>
              {inventariosGlobais.map((inventario) => (
                <option key={inventario.id} value={inventario.id}>
                  Score {inventario.score_geral.toFixed(2)} · importação {inventario.importacao_id.slice(0, 8)}
                </option>
              ))}
            </select>

            <div className="space-y-2 rounded-md border border-border p-3">
              <p className="text-sm font-medium text-foreground">Dependências da onda</p>
              {ondas.length === 0 ? (
                <p className="text-xs text-muted-foreground">Nenhuma onda existente para dependência.</p>
              ) : (
                ondas.map((onda) => (
                  <label key={onda.id} className="flex items-center gap-2 text-sm text-foreground">
                    <input
                      type="checkbox"
                      checked={dependenciaIds.includes(onda.id)}
                      onChange={() => toggleDependencia(onda.id)}
                    />
                    <span>
                      #{onda.ordem} · {onda.nome} · {onda.status}
                    </span>
                  </label>
                ))
              )}
            </div>

            <Button type="button" onClick={handleCriarOnda} disabled={loadingAction !== null}>
              {loadingAction === "onda" ? "Criando..." : "Criar onda"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Validação da onda</CardTitle>
            <CardDescription>
              Checklist de prontidão com score de qualidade, dependências pendentes e fases do cronograma.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!validacaoAtual ? (
              <p className="text-sm text-muted-foreground">
                Execute a validação em uma onda para visualizar o checklist operacional.
              </p>
            ) : (
              <>
                <p className="text-sm font-medium text-foreground">
                  Status: {validacaoAtual.status_planejamento} · Pronta: {validacaoAtual.pronta ? "sim" : "não"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Score de qualidade: {validacaoAtual.score_qualidade?.toFixed(2) ?? "não vinculado"}
                </p>
                <div className="space-y-1">
                  {validacaoAtual.checklist.map((item) => (
                    <p key={item} className="text-xs text-muted-foreground">
                      • {item}
                    </p>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Dependências pendentes: {validacaoAtual.dependencias_pendentes.join(", ") || "nenhuma"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Fases pendentes: {validacaoAtual.fases_pendentes.join(", ") || "nenhuma"}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cronograma visual de ondas</CardTitle>
          <CardDescription>
            Acompanhe a sequência, status e rollback por fase para reduzir risco na migração.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <select
            value={statusFiltroOnda}
            onChange={(event) => setStatusFiltroOnda(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm md:max-w-xs"
          >
            <option value="">Todos os status</option>
            <option value="planejada">Planejada</option>
            <option value="pronta">Pronta</option>
            <option value="bloqueada">Bloqueada</option>
            <option value="concluida">Concluída</option>
            <option value="rollback_executado">Rollback executado</option>
          </select>

          <div className="grid gap-4 lg:grid-cols-2">
            {ondas.map((onda) => (
              <div key={onda.id} className="rounded-xl border border-border p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      #{onda.ordem} · {onda.nome}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {onda.unidade} · {onda.processo} · {onda.estrategia_corte}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Corte planejado: {onda.data_corte_planejada ? new Date(onda.data_corte_planejada).toLocaleDateString("pt-BR") : "não informado"}
                    </p>
                  </div>
                  <span className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs text-primary">
                    {onda.status}
                  </span>
                </div>

                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-foreground">Dependências</p>
                  <p className="text-xs text-muted-foreground">
                    {onda.dependencias.length
                      ? onda.dependencias.map((item) => `${item.nome} (${item.status})`).join(", ")
                      : "Nenhuma dependência registrada"}
                  </p>
                </div>

                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-foreground">Fases</p>
                  {onda.fases.map((fase) => (
                    <div key={fase.id} className="rounded-md border border-border/60 p-2 text-xs text-muted-foreground">
                      <p className="font-medium text-foreground">
                        {fase.ordem}. {fase.nome} · {fase.status}
                      </p>
                      <p>{fase.rollback_script.join(" · ")}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => handleValidarOnda(onda.id)}
                    disabled={loadingAction !== null}
                  >
                    {loadingAction === `validar-${onda.id}` ? "Validando..." : "Validar"}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => handleConcluirOnda(onda.id)}
                    disabled={loadingAction !== null}
                  >
                    {loadingAction === `concluir-${onda.id}` ? "Concluindo..." : "Concluir"}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => handleRollbackOnda(onda.id)}
                    disabled={loadingAction !== null}
                  >
                    {loadingAction === `rollback-${onda.id}` ? "Executando rollback..." : "Rollback"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
