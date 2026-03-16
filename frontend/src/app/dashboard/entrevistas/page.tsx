"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import api from "@/lib/api";
import { useRoteiro, useRoteiros } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type RoteiroListItem = {
  id: string;
  titulo: string;
  area: string | null;
  versao: number;
  status: string;
  total_perguntas: number;
};

type RoteirosResponse = {
  items: RoteiroListItem[];
  total: number;
  page: number;
  per_page: number;
};

type CondicaoItem = {
  id: string;
  operador: string;
  valor: Record<string, unknown>;
  acao: string;
  alvo_id: string | null;
};

type PerguntaItem = {
  id: string;
  ordem: number;
  texto: string;
  tipo: string;
  obrigatoria: boolean;
  secao: string | null;
  metadado_alvo: string | null;
  opcoes: Record<string, unknown> | null;
  condicoes: CondicaoItem[];
};

type RoteiroDetalhe = {
  id: string;
  titulo: string;
  descricao: string | null;
  area: string | null;
  versao: number;
  status: string;
  perguntas: PerguntaItem[];
};

type SimulacaoPergunta = {
  id: string;
  ordem: number;
  texto: string;
  tipo: string;
  secao: string | null;
  visivel: boolean;
  obrigatoria: boolean;
};

type SimulacaoResult = {
  perguntas: SimulacaoPergunta[];
  pendencias: string[];
  pode_concluir: boolean;
};

type EntrevistaSessao = {
  id: string;
  roteiro_id: string;
  entrevistador_id: string | null;
  status: string;
  respostas: Record<string, unknown>;
  created_at: string;
  completed_at: string | null;
};

type EvidenciaItem = {
  id: string;
  entrevista_id: string;
  pergunta_id: string | null;
  nome_arquivo: string;
  mime_type: string | null;
  tamanho_bytes: number | null;
  hash_sha256: string;
  storage_path: string;
  created_at: string;
};

type SugestaoClasseResult = {
  entrevista_id: string;
  sugestao_classe: string;
  sugestao_justificativa: string;
};

type AssistentePreviewResult = {
  progresso_percentual: number;
  respostas_preenchidas: number;
  total_perguntas_ativas: number;
  resumo: string;
  pendencias: string[];
  pcd_sugerido: string;
  pcd_justificativa: string;
  ttd_sugerida: string;
  ttd_justificativa: string;
};

type RespostasState = Record<string, string>;

type CondicaoDraft = {
  uiId: string;
  perguntaId: string;
  operador: string;
  valor: string;
  acao: string;
};

function createCondicaoDraft(): CondicaoDraft {
  return {
    uiId: `cond-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    perguntaId: "",
    operador: "EQ",
    valor: "",
    acao: "mostrar",
  };
}

function parseScalarValue(value: string): string | number | boolean {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  const numberValue = Number(value);
  if (!Number.isNaN(numberValue) && value.trim() !== "") {
    return numberValue;
  }
  return value;
}

function buildRespostasPayload(respostas: RespostasState): Record<string, unknown> {
  return Object.entries(respostas).reduce<Record<string, unknown>>(
    (acc, [key, value]) => {
      if (value.trim() === "") {
        return acc;
      }
      acc[key] = parseScalarValue(value);
      return acc;
    },
    {}
  );
}

export default function EntrevistasPage() {
  const [selectedRoteiroId, setSelectedRoteiroId] = useState<string | null>(
    null
  );
  const [creatingRoteiro, setCreatingRoteiro] = useState(false);
  const [addingPergunta, setAddingPergunta] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [simulacao, setSimulacao] = useState<SimulacaoResult | null>(null);

  const [titulo, setTitulo] = useState("");
  const [area, setArea] = useState("");
  const [descricao, setDescricao] = useState("");

  const [ordem, setOrdem] = useState(1);
  const [textoPergunta, setTextoPergunta] = useState("");
  const [tipoPergunta, setTipoPergunta] = useState("texto");
  const [obrigatoriaPergunta, setObrigatoriaPergunta] = useState(true);
  const [usarCondicao, setUsarCondicao] = useState(false);
  const [condicoesDraft, setCondicoesDraft] = useState<CondicaoDraft[]>([]);

  const [respostas, setRespostas] = useState<RespostasState>({});
  const [wizardRespostas, setWizardRespostas] = useState<RespostasState>({});
  const [wizardSimulacao, setWizardSimulacao] = useState<SimulacaoResult | null>(
    null
  );
  const [wizardStepIndex, setWizardStepIndex] = useState(0);
  const [wizardLoading, setWizardLoading] = useState(false);
  const [entrevistaAtivaId, setEntrevistaAtivaId] = useState<string | null>(null);
  const [evidencias, setEvidencias] = useState<EvidenciaItem[]>([]);
  const [arquivoEvidencia, setArquivoEvidencia] = useState<File | null>(null);
  const [arquivoInputKey, setArquivoInputKey] = useState(0);
  const [arquivoPreviewUrl, setArquivoPreviewUrl] = useState<string | null>(null);
  const [perguntaEvidenciaId, setPerguntaEvidenciaId] = useState("");
  const [iniciandoSessaoEvidencia, setIniciandoSessaoEvidencia] = useState(false);
  const [uploadingEvidencia, setUploadingEvidencia] = useState(false);
  const [carregandoPreviewId, setCarregandoPreviewId] = useState<string | null>(
    null
  );
  const [evidenciaPreview, setEvidenciaPreview] = useState<{
    id: string;
    nomeArquivo: string;
    mimeType: string;
    url: string;
  } | null>(null);
  const [gerandoSugestao, setGerandoSugestao] = useState(false);
  const [sugestaoClasse, setSugestaoClasse] =
    useState<SugestaoClasseResult | null>(null);
  const [previewAssistente, setPreviewAssistente] =
    useState<AssistentePreviewResult | null>(null);
  const [carregandoPreviewAssistente, setCarregandoPreviewAssistente] = useState(false);

  const {
    data: roteirosRaw,
    isLoading: loadingRoteiros,
    mutate: mutateRoteiros,
  } = useRoteiros(1, 20);
  const roteirosData = roteirosRaw as RoteirosResponse | undefined;

  const { data: roteiroRaw, mutate: mutateRoteiro } = useRoteiro(
    selectedRoteiroId
  );
  const roteiroSelecionado = roteiroRaw as RoteiroDetalhe | undefined;

  const perguntasOrdenadas = useMemo(() => {
    if (!roteiroSelecionado?.perguntas) {
      return [] as PerguntaItem[];
    }
    return [...roteiroSelecionado.perguntas].sort((a, b) => a.ordem - b.ordem);
  }, [roteiroSelecionado]);

  const perguntasVisiveisWizard = useMemo(() => {
    if (!wizardSimulacao) {
      return [] as PerguntaItem[];
    }

    const perguntasVisiveis = new Set(
      wizardSimulacao.perguntas
        .filter((pergunta) => pergunta.visivel)
        .map((pergunta) => pergunta.id)
    );

    return perguntasOrdenadas.filter((pergunta) => perguntasVisiveis.has(pergunta.id));
  }, [perguntasOrdenadas, wizardSimulacao]);

  const perguntaAtualWizard = perguntasVisiveisWizard[wizardStepIndex] ?? null;

  const perguntasPorId = useMemo(
    () => new Map(perguntasOrdenadas.map((pergunta) => [pergunta.id, pergunta])),
    [perguntasOrdenadas]
  );

  useEffect(() => {
    if (!arquivoEvidencia) {
      setArquivoPreviewUrl(null);
      return;
    }

    const objectUrl = URL.createObjectURL(arquivoEvidencia);
    setArquivoPreviewUrl(objectUrl);

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [arquivoEvidencia]);

  useEffect(() => {
    return () => {
      if (evidenciaPreview?.url) {
        URL.revokeObjectURL(evidenciaPreview.url);
      }
    };
  }, [evidenciaPreview]);

  function formatBytes(size: number | null): string {
    if (size === null) {
      return "0 B";
    }
    if (size < 1024) {
      return `${size} B`;
    }
    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(1)} KB`;
    }
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  function limparPreviewRemoto() {
    if (evidenciaPreview?.url) {
      URL.revokeObjectURL(evidenciaPreview.url);
    }
    setEvidenciaPreview(null);
  }

  function resetExecucao() {
    setSimulacao(null);
    setRespostas({});
    setWizardRespostas({});
    setWizardSimulacao(null);
    setWizardStepIndex(0);
    setUsarCondicao(false);
    setCondicoesDraft([]);
    setEntrevistaAtivaId(null);
    setEvidencias([]);
    setArquivoEvidencia(null);
    setArquivoInputKey((prev) => prev + 1);
    setArquivoPreviewUrl(null);
    setPerguntaEvidenciaId("");
    setSugestaoClasse(null);
    setPreviewAssistente(null);
    limparPreviewRemoto();
  }

  async function carregarEvidencias(entrevistaId: string) {
    const { data } = await api.get<EvidenciaItem[]>(
      `/roteiros/entrevistas/${entrevistaId}/evidencias`
    );
    setEvidencias(data);
  }

  function handleToggleCondicao(checked: boolean) {
    setUsarCondicao(checked);
    if (checked) {
      setCondicoesDraft((prev) => (prev.length > 0 ? prev : [createCondicaoDraft()]));
      return;
    }
    setCondicoesDraft([]);
  }

  function handleAdicionarRegraCondicao() {
    setCondicoesDraft((prev) => [...prev, createCondicaoDraft()]);
  }

  function handleRemoverRegraCondicao(uiId: string) {
    setCondicoesDraft((prev) => prev.filter((item) => item.uiId !== uiId));
  }

  function handleAtualizarCondicao(
    uiId: string,
    campo: "perguntaId" | "operador" | "valor" | "acao",
    valor: string
  ) {
    setCondicoesDraft((prev) =>
      prev.map((item) => (item.uiId === uiId ? { ...item, [campo]: valor } : item))
    );
  }

  const getPerguntaLabel = useCallback((perguntaId: string) => {
    const pergunta = perguntasPorId.get(perguntaId);
    if (!pergunta) {
      return "Pergunta não selecionada";
    }
    return `#${pergunta.ordem} ${pergunta.texto}`;
  }, [perguntasPorId]);

  async function executarSimulacaoWizard(nextRespostas: RespostasState) {
    if (!selectedRoteiroId) {
      return null;
    }

    const { data } = await api.post<SimulacaoResult>(
      `/roteiros/${selectedRoteiroId}/simular`,
      { respostas: buildRespostasPayload(nextRespostas) }
    );

    setWizardSimulacao(data);
    return data;
  }

  async function handleCriarRoteiro(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setCreatingRoteiro(true);
    try {
      const { data } = await api.post<RoteiroDetalhe>("/roteiros", {
        titulo,
        area: area || null,
        descricao: descricao || null,
        perguntas: [],
      });
      setTitulo("");
      setArea("");
      setDescricao("");
      setSelectedRoteiroId(data.id);
      setOrdem(1);
      resetExecucao();
      await mutateRoteiros();
    } catch {
      setErrorMessage("Não foi possível criar o roteiro. Verifique o login.");
    } finally {
      setCreatingRoteiro(false);
    }
  }

  async function handleAdicionarPergunta(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRoteiroId) {
      setErrorMessage("Selecione um roteiro antes de adicionar perguntas.");
      return;
    }

    const condicoes =
      usarCondicao
        ? condicoesDraft
            .filter((item) => item.perguntaId)
            .map((item) => ({
              operador: item.operador,
              valor: {
                pergunta_id: item.perguntaId,
                valor: parseScalarValue(item.valor),
              },
              acao: item.acao,
              alvo_id: null,
            }))
        : [];

    if (usarCondicao && condicoes.length === 0) {
      setErrorMessage("Adicione ao menos uma regra de condição válida.");
      return;
    }

    setErrorMessage(null);
    setAddingPergunta(true);
    try {
      await api.post(`/roteiros/${selectedRoteiroId}/perguntas`, {
        ordem,
        texto: textoPergunta,
        tipo: tipoPergunta,
        obrigatoria: obrigatoriaPergunta,
        secao: null,
        metadado_alvo: null,
        opcoes: null,
        condicoes,
      });

      setTextoPergunta("");
      setTipoPergunta("texto");
      setObrigatoriaPergunta(true);
      setUsarCondicao(false);
      setCondicoesDraft([]);

      await mutateRoteiro();
      setOrdem((prev) => prev + 1);
    } catch {
      setErrorMessage("Não foi possível adicionar a pergunta.");
    } finally {
      setAddingPergunta(false);
    }
  }

  async function handleSimular() {
    if (!selectedRoteiroId) {
      setErrorMessage("Selecione um roteiro para executar o dry-run.");
      return;
    }
    setErrorMessage(null);
    setSimulating(true);
    try {
      const { data } = await api.post<SimulacaoResult>(
        `/roteiros/${selectedRoteiroId}/simular`,
        { respostas: buildRespostasPayload(respostas) }
      );
      setSimulacao(data);
    } catch {
      setErrorMessage("Falha ao simular roteiro.");
    } finally {
      setSimulating(false);
    }
  }

  async function handleIniciarEntrevista() {
    if (!selectedRoteiroId) {
      setErrorMessage("Selecione um roteiro para iniciar a entrevista.");
      return;
    }

    setErrorMessage(null);
    setWizardLoading(true);
    try {
      const data = await executarSimulacaoWizard(wizardRespostas);
      const primeiraVisivel = data?.perguntas.findIndex((pergunta) => pergunta.visivel) ?? 0;
      setWizardStepIndex(primeiraVisivel >= 0 ? primeiraVisivel : 0);
    } catch {
      setErrorMessage("Não foi possível iniciar o executor da entrevista.");
    } finally {
      setWizardLoading(false);
    }
  }

  async function handleProximaEtapa() {
    if (!selectedRoteiroId || !perguntaAtualWizard) {
      return;
    }

    setErrorMessage(null);
    setWizardLoading(true);
    try {
      const data = await executarSimulacaoWizard(wizardRespostas);
      if (!data) {
        return;
      }

      const perguntasVisiveis = data.perguntas.filter((pergunta) => pergunta.visivel);
      const indiceAtual = perguntasVisiveis.findIndex(
        (pergunta) => pergunta.id === perguntaAtualWizard.id
      );

      if (indiceAtual === -1) {
        setWizardStepIndex(0);
      } else {
        setWizardStepIndex(
          Math.min(indiceAtual + 1, Math.max(perguntasVisiveis.length - 1, 0))
        );
      }
    } catch {
      setErrorMessage("Não foi possível avançar a entrevista.");
    } finally {
      setWizardLoading(false);
    }
  }

  function handleVoltarEtapa() {
    setWizardStepIndex((prev) => Math.max(prev - 1, 0));
  }

  function handleReiniciarEntrevista() {
    setWizardRespostas({});
    setWizardSimulacao(null);
    setWizardStepIndex(0);
  }

  async function handleIniciarSessaoEvidencias() {
    if (!selectedRoteiroId) {
      setErrorMessage("Selecione um roteiro para iniciar anexos/evidências.");
      return;
    }

    setErrorMessage(null);
    setIniciandoSessaoEvidencia(true);
    try {
      if (entrevistaAtivaId) {
        await carregarEvidencias(entrevistaAtivaId);
        return;
      }

      const { data } = await api.post<EntrevistaSessao>(
        `/roteiros/${selectedRoteiroId}/entrevistas`,
        { respostas: buildRespostasPayload(wizardRespostas) }
      );
      setEntrevistaAtivaId(data.id);
      await carregarEvidencias(data.id);
    } catch {
      setErrorMessage("Não foi possível iniciar a sessão de evidências.");
    } finally {
      setIniciandoSessaoEvidencia(false);
    }
  }

  async function handleUploadEvidencia(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!entrevistaAtivaId) {
      setErrorMessage("Inicie uma sessão de evidências antes do upload.");
      return;
    }
    if (!arquivoEvidencia) {
      setErrorMessage("Selecione um arquivo para anexar.");
      return;
    }

    setErrorMessage(null);
    setUploadingEvidencia(true);
    try {
      const formData = new FormData();
      formData.append("file", arquivoEvidencia);
      if (perguntaEvidenciaId) {
        formData.append("pergunta_id", perguntaEvidenciaId);
      }

      await api.post(
        `/roteiros/entrevistas/${entrevistaAtivaId}/evidencias`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setArquivoEvidencia(null);
      setArquivoInputKey((prev) => prev + 1);
      setPerguntaEvidenciaId("");
      await carregarEvidencias(entrevistaAtivaId);
    } catch {
      setErrorMessage("Falha ao anexar evidência.");
    } finally {
      setUploadingEvidencia(false);
    }
  }

  async function handlePrevisualizarEvidencia(evidencia: EvidenciaItem) {
    setErrorMessage(null);
    setCarregandoPreviewId(evidencia.id);
    try {
      const { data } = await api.get(
        `/roteiros/evidencias/${evidencia.id}/download`,
        {
          responseType: "blob",
        }
      );

      if (evidenciaPreview?.url) {
        URL.revokeObjectURL(evidenciaPreview.url);
      }

      const url = URL.createObjectURL(data as Blob);
      setEvidenciaPreview({
        id: evidencia.id,
        nomeArquivo: evidencia.nome_arquivo,
        mimeType: evidencia.mime_type || (data as Blob).type || "application/octet-stream",
        url,
      });
    } catch {
      setErrorMessage("Não foi possível carregar a pré-visualização do anexo.");
    } finally {
      setCarregandoPreviewId(null);
    }
  }

  async function handleGerarSugestaoClasse() {
    if (!entrevistaAtivaId) {
      setErrorMessage("Inicie uma sessão de entrevista para gerar sugestão.");
      return;
    }

    setErrorMessage(null);
    setGerandoSugestao(true);
    try {
      const { data } = await api.post<SugestaoClasseResult>(
        `/roteiros/entrevistas/${entrevistaAtivaId}/sugestao-classe`,
        { respostas: buildRespostasPayload(wizardRespostas) }
      );
      setSugestaoClasse(data);
    } catch {
      setErrorMessage("Não foi possível gerar a sugestão automática de classe.");
    } finally {
      setGerandoSugestao(false);
    }
  }

  async function handleGerarPreviewAssistido() {
    if (!selectedRoteiroId) {
      setErrorMessage("Selecione um roteiro para gerar a prévia assistida.");
      return;
    }

    setErrorMessage(null);
    setCarregandoPreviewAssistente(true);
    try {
      const { data } = await api.post<AssistentePreviewResult>(
        `/roteiros/${selectedRoteiroId}/assistente-preview`,
        { respostas: buildRespostasPayload(wizardRespostas) }
      );
      setPreviewAssistente(data);
    } catch {
      setErrorMessage("Não foi possível gerar a prévia assistida da entrevista.");
    } finally {
      setCarregandoPreviewAssistente(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Entrevistas</h1>
        <p className="text-muted-foreground">
          Sprint 2 (US-002): builder de condições, simulação e execução
          step-by-step
        </p>
      </div>

      {errorMessage ? (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Novo Roteiro</CardTitle>
            <CardDescription>
              Crie um roteiro para iniciar o fluxo da entrevista dinâmica
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCriarRoteiro} className="space-y-3">
              <input
                required
                value={titulo}
                onChange={(event) => setTitulo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Título do roteiro"
              />
              <input
                value={area}
                onChange={(event) => setArea(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Área (ex.: RH)"
              />
              <textarea
                value={descricao}
                onChange={(event) => setDescricao(event.target.value)}
                className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Descrição do roteiro"
              />
              <Button type="submit" className="w-full" disabled={creatingRoteiro}>
                {creatingRoteiro ? "Criando..." : "Criar roteiro"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Catálogo de Roteiros</CardTitle>
            <CardDescription>
              {loadingRoteiros
                ? "Carregando roteiros..."
                : `${roteirosData?.total ?? 0} roteiro(s) encontrado(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {roteirosData?.items?.map((roteiro) => (
                <button
                  key={roteiro.id}
                  type="button"
                  onClick={() => {
                    setSelectedRoteiroId(roteiro.id);
                    setOrdem(roteiro.total_perguntas + 1);
                    resetExecucao();
                  }}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    selectedRoteiroId === roteiro.id
                      ? "border-primary bg-primary/5"
                      : "border-border bg-background hover:bg-muted/40"
                  }`}
                >
                  <p className="font-medium text-foreground">{roteiro.titulo}</p>
                  <p className="text-xs text-muted-foreground">
                    Área: {roteiro.area || "—"} · Versão {roteiro.versao} ·
                    Perguntas: {roteiro.total_perguntas} · Status: {roteiro.status}
                  </p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Perguntas do Roteiro</CardTitle>
            <CardDescription>
              {roteiroSelecionado
                ? `Roteiro selecionado: ${roteiroSelecionado.titulo}`
                : "Selecione um roteiro no catálogo"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleAdicionarPergunta} className="space-y-3">
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <input
                  type="number"
                  min={1}
                  value={ordem}
                  onChange={(event) => setOrdem(Number(event.target.value))}
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Ordem"
                />
                <select
                  value={tipoPergunta}
                  onChange={(event) => setTipoPergunta(event.target.value)}
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="texto">Texto</option>
                  <option value="numero">Número</option>
                  <option value="boolean">Booleano</option>
                </select>
                <label className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm text-foreground">
                  <input
                    type="checkbox"
                    checked={obrigatoriaPergunta}
                    onChange={(event) => setObrigatoriaPergunta(event.target.checked)}
                  />
                  Obrigatória
                </label>
              </div>

              <input
                required
                value={textoPergunta}
                onChange={(event) => setTextoPergunta(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Texto da pergunta"
              />

              <label className="inline-flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={usarCondicao}
                  onChange={(event) => handleToggleCondicao(event.target.checked)}
                />
                Aplicar condições (builder visual)
              </label>

              {usarCondicao ? (
                <div className="space-y-3 rounded-lg border border-border p-3">
                  {condicoesDraft.map((condicao, index) => (
                    <div key={condicao.uiId} className="space-y-3 rounded-md border border-input p-3">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold uppercase text-muted-foreground">
                          Regra {index + 1}
                        </p>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoverRegraCondicao(condicao.uiId)}
                          disabled={condicoesDraft.length === 1}
                        >
                          Remover
                        </Button>
                      </div>

                      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                        <select
                          value={condicao.perguntaId}
                          onChange={(event) =>
                            handleAtualizarCondicao(
                              condicao.uiId,
                              "perguntaId",
                              event.target.value
                            )
                          }
                          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                          <option value="">Pergunta de referência</option>
                          {perguntasOrdenadas.map((pergunta) => (
                            <option key={pergunta.id} value={pergunta.id}>
                              #{pergunta.ordem} - {pergunta.texto}
                            </option>
                          ))}
                        </select>

                        <select
                          value={condicao.operador}
                          onChange={(event) =>
                            handleAtualizarCondicao(condicao.uiId, "operador", event.target.value)
                          }
                          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                          <option value="EQ">Igual (EQ)</option>
                          <option value="NEQ">Diferente (NEQ)</option>
                          <option value="GT">Maior que (GT)</option>
                          <option value="LT">Menor que (LT)</option>
                          <option value="GTE">Maior ou igual (GTE)</option>
                          <option value="LTE">Menor ou igual (LTE)</option>
                        </select>

                        <input
                          value={condicao.valor}
                          onChange={(event) =>
                            handleAtualizarCondicao(condicao.uiId, "valor", event.target.value)
                          }
                          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                          placeholder="Valor esperado"
                        />

                        <select
                          value={condicao.acao}
                          onChange={(event) =>
                            handleAtualizarCondicao(condicao.uiId, "acao", event.target.value)
                          }
                          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                          <option value="mostrar">Mostrar pergunta</option>
                          <option value="ocultar">Ocultar pergunta</option>
                          <option value="obrigar">Tornar obrigatória</option>
                        </select>
                      </div>

                      <p className="text-xs text-muted-foreground">
                        Se {getPerguntaLabel(condicao.perguntaId)} {condicao.operador} valor
                        {" "}
                        {condicao.valor || "..."}, então: {condicao.acao}.
                      </p>
                    </div>
                  ))}

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleAdicionarRegraCondicao}
                    >
                      Adicionar regra
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setCondicoesDraft([createCondicaoDraft()])}
                    >
                      Limpar regras
                    </Button>
                  </div>
                </div>
              ) : null}

              <Button
                type="submit"
                disabled={addingPergunta || !selectedRoteiroId}
                className="w-full"
              >
                {addingPergunta ? "Adicionando..." : "Adicionar pergunta"}
              </Button>
            </form>

            <div className="space-y-2">
              {perguntasOrdenadas.map((pergunta) => (
                <div key={pergunta.id} className="rounded-lg border border-border p-3">
                  <p className="text-sm font-medium text-foreground">
                    #{pergunta.ordem} · {pergunta.texto}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Tipo: {pergunta.tipo} · Obrigatória: {pergunta.obrigatoria
                      ? "Sim"
                      : "Não"}{" "}
                    · Condições: {pergunta.condicoes.length}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dry-run Condicional</CardTitle>
            <CardDescription>
              Simule respostas para validar visibilidade e obrigatoriedade das
              perguntas
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {perguntasOrdenadas.map((pergunta) => (
              <div key={pergunta.id} className="space-y-1">
                <label className="text-sm font-medium text-foreground">
                  #{pergunta.ordem} {pergunta.texto}
                </label>
                {pergunta.tipo === "boolean" ? (
                  <select
                    value={respostas[pergunta.id] ?? ""}
                    onChange={(event) =>
                      setRespostas((prev) => ({
                        ...prev,
                        [pergunta.id]: event.target.value,
                      }))
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Selecionar</option>
                    <option value="true">Sim</option>
                    <option value="false">Não</option>
                  </select>
                ) : (
                  <input
                    type={pergunta.tipo === "numero" ? "number" : "text"}
                    value={respostas[pergunta.id] ?? ""}
                    onChange={(event) =>
                      setRespostas((prev) => ({
                        ...prev,
                        [pergunta.id]: event.target.value,
                      }))
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                )}
              </div>
            ))}

            <Button
              type="button"
              onClick={handleSimular}
              disabled={simulating || !selectedRoteiroId}
              className="w-full"
            >
              {simulating ? "Simulando..." : "Executar dry-run"}
            </Button>

            {simulacao ? (
              <div className="space-y-3 rounded-lg border border-border p-3">
                <p className="text-sm font-medium text-foreground">
                  Pode concluir: {simulacao.pode_concluir ? "Sim" : "Não"}
                </p>
                <div className="space-y-1">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Pendências
                  </p>
                  {simulacao.pendencias.length === 0 ? (
                    <p className="text-sm text-foreground">Nenhuma pendência.</p>
                  ) : (
                    simulacao.pendencias.map((pendencia) => (
                      <p key={pendencia} className="text-sm text-destructive">
                        • {pendencia}
                      </p>
                    ))
                  )}
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Resultado por pergunta
                  </p>
                  {simulacao.perguntas.map((pergunta) => (
                    <p key={pergunta.id} className="text-sm text-foreground">
                      #{pergunta.ordem} · {pergunta.visivel ? "Visível" : "Oculta"}
                      {" · "}
                      {pergunta.obrigatoria ? "Obrigatória" : "Opcional"}
                    </p>
                  ))}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Executor de Entrevista</CardTitle>
          <CardDescription>
            Wizard step-by-step para percorrer apenas as perguntas visíveis no
            fluxo condicional atual
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!selectedRoteiroId ? (
            <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
              Selecione um roteiro no catálogo para iniciar a entrevista guiada.
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-3 rounded-lg border border-border p-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {roteiroSelecionado?.titulo || "Roteiro selecionado"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {wizardSimulacao
                      ? `${perguntasVisiveisWizard.length} pergunta(s) ativa(s) no fluxo atual`
                      : "Clique em iniciar para calcular o fluxo com as regras condicionais."}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleReiniciarEntrevista}
                    disabled={wizardLoading}
                  >
                    Limpar fluxo
                  </Button>
                  <Button
                    type="button"
                    onClick={handleIniciarEntrevista}
                    disabled={wizardLoading || perguntasOrdenadas.length === 0}
                  >
                    {wizardLoading && !wizardSimulacao
                      ? "Iniciando..."
                      : wizardSimulacao
                        ? "Recalcular fluxo"
                        : "Iniciar entrevista"}
                  </Button>
                </div>
              </div>

              {wizardSimulacao && perguntaAtualWizard ? (
                <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
                  <div className="space-y-4 rounded-lg border border-border p-4">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Etapa {wizardStepIndex + 1} de {perguntasVisiveisWizard.length}
                      </p>
                      <h3 className="text-lg font-semibold text-foreground">
                        #{perguntaAtualWizard.ordem} · {perguntaAtualWizard.texto}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Tipo: {perguntaAtualWizard.tipo} · Obrigatória: {perguntaAtualWizard.obrigatoria
                          ? "Sim"
                          : "Não"}
                      </p>
                    </div>

                    {perguntaAtualWizard.tipo === "boolean" ? (
                      <select
                        value={wizardRespostas[perguntaAtualWizard.id] ?? ""}
                        onChange={(event) =>
                          setWizardRespostas((prev) => ({
                            ...prev,
                            [perguntaAtualWizard.id]: event.target.value,
                          }))
                        }
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">Selecionar</option>
                        <option value="true">Sim</option>
                        <option value="false">Não</option>
                      </select>
                    ) : (
                      <input
                        type={perguntaAtualWizard.tipo === "numero" ? "number" : "text"}
                        value={wizardRespostas[perguntaAtualWizard.id] ?? ""}
                        onChange={(event) =>
                          setWizardRespostas((prev) => ({
                            ...prev,
                            [perguntaAtualWizard.id]: event.target.value,
                          }))
                        }
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        placeholder="Digite a resposta desta etapa"
                      />
                    )}

                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleVoltarEtapa}
                        disabled={wizardLoading || wizardStepIndex === 0}
                      >
                        Voltar
                      </Button>
                      <Button type="button" onClick={handleProximaEtapa} disabled={wizardLoading}>
                        {wizardLoading
                          ? "Atualizando..."
                          : wizardStepIndex >= perguntasVisiveisWizard.length - 1
                            ? "Validar conclusão"
                            : "Próxima etapa"}
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-4 rounded-lg border border-border p-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Situação do fluxo
                      </p>
                      <p className="mt-1 text-sm text-foreground">
                        Pode concluir: {wizardSimulacao.pode_concluir ? "Sim" : "Não"}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Perguntas ativas
                      </p>
                      {perguntasVisiveisWizard.map((pergunta, index) => (
                        <div
                          key={pergunta.id}
                          className={`rounded-md border p-2 text-sm ${
                            pergunta.id === perguntaAtualWizard.id
                              ? "border-primary bg-primary/5 text-foreground"
                              : "border-border text-muted-foreground"
                          }`}
                        >
                          {index + 1}. #{pergunta.ordem} · {pergunta.texto}
                        </div>
                      ))}
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Pendências
                      </p>
                      {wizardSimulacao.pendencias.length === 0 ? (
                        <p className="text-sm text-foreground">Nenhuma pendência crítica.</p>
                      ) : (
                        wizardSimulacao.pendencias.map((pendencia) => (
                          <p key={pendencia} className="text-sm text-destructive">
                            • {pendencia}
                          </p>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              ) : wizardSimulacao ? (
                <div className="rounded-lg border border-border p-4 text-sm text-muted-foreground">
                  Nenhuma pergunta ficou visível com as respostas atuais.
                </div>
              ) : null}
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evidências e Anexos</CardTitle>
          <CardDescription>
            US-003: anexar arquivos com hash e vínculo opcional à pergunta da
            entrevista
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!selectedRoteiroId ? (
            <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
              Selecione um roteiro para habilitar upload de evidências.
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    Sessão ativa: {entrevistaAtivaId ?? "não iniciada"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Inicie uma sessão para registrar anexos da execução atual.
                  </p>
                </div>
                <Button
                  type="button"
                  onClick={handleIniciarSessaoEvidencias}
                  disabled={iniciandoSessaoEvidencia}
                >
                  {iniciandoSessaoEvidencia
                    ? "Preparando..."
                    : entrevistaAtivaId
                      ? "Atualizar lista"
                      : "Iniciar sessão"}
                </Button>
              </div>

              {entrevistaAtivaId ? (
                <form onSubmit={handleUploadEvidencia} className="space-y-3 rounded-lg border border-border p-3">
                  <input
                    key={arquivoInputKey}
                    type="file"
                    onChange={(event) =>
                      setArquivoEvidencia(event.target.files?.[0] ?? null)
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />

                  <select
                    value={perguntaEvidenciaId}
                    onChange={(event) => setPerguntaEvidenciaId(event.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Sem vínculo direto com pergunta</option>
                    {perguntasOrdenadas.map((pergunta) => (
                      <option key={pergunta.id} value={pergunta.id}>
                        #{pergunta.ordem} - {pergunta.texto}
                      </option>
                    ))}
                  </select>

                  <Button type="submit" disabled={uploadingEvidencia || !arquivoEvidencia}>
                    {uploadingEvidencia ? "Enviando..." : "Anexar evidência"}
                  </Button>
                </form>
              ) : null}

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Arquivos anexados
                </p>
                {evidencias.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Nenhum anexo registrado nesta sessão.
                  </p>
                ) : (
                  evidencias.map((evidencia) => (
                    <div key={evidencia.id} className="rounded-md border border-border p-3">
                      <p className="text-sm font-medium text-foreground">
                        {evidencia.nome_arquivo}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Hash: {evidencia.hash_sha256.slice(0, 16)}... ·
                        Tamanho: {evidencia.tamanho_bytes ?? 0} bytes
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(evidencia.created_at).toLocaleString("pt-BR")}
                      </p>
                      <div className="mt-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handlePrevisualizarEvidencia(evidencia)}
                          disabled={carregandoPreviewId === evidencia.id}
                        >
                          {carregandoPreviewId === evidencia.id
                            ? "Carregando..."
                            : "Pré-visualizar"}
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Assistente de Entrevista</CardTitle>
          <CardDescription>
            US-090: barra de progresso, resumo e prévia de PCD/TTD sugeridos com justificativas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              onClick={handleGerarPreviewAssistido}
              disabled={carregandoPreviewAssistente || !selectedRoteiroId}
            >
              {carregandoPreviewAssistente ? "Atualizando prévia..." : "Atualizar prévia assistida"}
            </Button>
            <p className="text-xs text-muted-foreground">
              A prévia usa as respostas atuais do wizard para indicar PCD, TTD e pendências.
            </p>
          </div>

          {previewAssistente ? (
            <div className="grid gap-4 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
              <div className="space-y-3 rounded-lg border border-border p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Progresso da entrevista
                </p>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary"
                    style={{ width: `${previewAssistente.progresso_percentual}%` }}
                  />
                </div>
                <p className="text-sm text-foreground">
                  {previewAssistente.respostas_preenchidas}/{previewAssistente.total_perguntas_ativas} respostas ativas · {previewAssistente.progresso_percentual}%
                </p>
                <p className="text-sm text-muted-foreground">{previewAssistente.resumo}</p>
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Pendências
                  </p>
                  {previewAssistente.pendencias.length === 0 ? (
                    <p className="text-sm text-foreground">Nenhuma pendência crítica.</p>
                  ) : (
                    previewAssistente.pendencias.map((pendencia) => (
                      <p key={pendencia} className="text-sm text-destructive">
                        • {pendencia}
                      </p>
                    ))
                  )}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2 rounded-lg border border-border p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Prévia PCD
                  </p>
                  <p className="text-sm font-semibold text-foreground">
                    {previewAssistente.pcd_sugerido}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {previewAssistente.pcd_justificativa}
                  </p>
                </div>
                <div className="space-y-2 rounded-lg border border-border p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Prévia TTD
                  </p>
                  <p className="text-sm font-semibold text-foreground">
                    {previewAssistente.ttd_sugerida}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {previewAssistente.ttd_justificativa}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Gere a prévia assistida para visualizar progresso, resumo e recomendações PCD/TTD.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sugestão de Classe</CardTitle>
          <CardDescription>
            US-004 (início): gerar sugestão automática de classe documental com
            base no contexto da entrevista
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              onClick={handleGerarSugestaoClasse}
              disabled={gerandoSugestao || !entrevistaAtivaId}
            >
              {gerandoSugestao ? "Gerando..." : "Gerar sugestão"}
            </Button>
            <p className="text-xs text-muted-foreground">
              Requer sessão ativa de entrevista
            </p>
          </div>

          {sugestaoClasse ? (
            <div className="space-y-2 rounded-lg border border-border p-3">
              <p className="text-sm font-semibold text-foreground">
                Classe sugerida: {sugestaoClasse.sugestao_classe}
              </p>
              <p className="text-sm text-muted-foreground">
                {sugestaoClasse.sugestao_justificativa}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Nenhuma sugestão calculada nesta sessão.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preview Avançado de Anexos</CardTitle>
          <CardDescription>
            Visualização local antes do envio e preview remoto autenticado dos
            anexos já salvos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2 rounded-lg border border-border p-3">
              <p className="text-xs font-semibold uppercase text-muted-foreground">
                Pré-visualização local
              </p>
              {arquivoEvidencia && arquivoPreviewUrl ? (
                <>
                  <p className="text-sm text-foreground">{arquivoEvidencia.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {arquivoEvidencia.type || "tipo não informado"} ·
                    {" "}
                    {formatBytes(arquivoEvidencia.size)}
                  </p>
                  {arquivoEvidencia.type.startsWith("image/") ? (
                    <Image
                      src={arquivoPreviewUrl}
                      alt={arquivoEvidencia.name}
                      width={960}
                      height={640}
                      unoptimized
                      className="max-h-56 w-full rounded-md border border-border object-contain"
                    />
                  ) : arquivoEvidencia.type === "application/pdf" ? (
                    <iframe
                      src={arquivoPreviewUrl}
                      title="Prévia local PDF"
                      className="h-64 w-full rounded-md border border-border"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Prévia inline indisponível para este tipo de arquivo.
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Selecione um arquivo no formulário de evidências para pré-visualizar.
                </p>
              )}
            </div>

            <div className="space-y-2 rounded-lg border border-border p-3">
              <p className="text-xs font-semibold uppercase text-muted-foreground">
                Pré-visualização remota
              </p>
              {evidenciaPreview ? (
                <>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-foreground">{evidenciaPreview.nomeArquivo}</p>
                    <Button type="button" variant="ghost" size="sm" onClick={limparPreviewRemoto}>
                      Fechar
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">{evidenciaPreview.mimeType}</p>
                  {evidenciaPreview.mimeType.startsWith("image/") ? (
                    <Image
                      src={evidenciaPreview.url}
                      alt={evidenciaPreview.nomeArquivo}
                      width={960}
                      height={640}
                      unoptimized
                      className="max-h-56 w-full rounded-md border border-border object-contain"
                    />
                  ) : evidenciaPreview.mimeType === "application/pdf" ? (
                    <iframe
                      src={evidenciaPreview.url}
                      title="Prévia remota PDF"
                      className="h-64 w-full rounded-md border border-border"
                    />
                  ) : (
                    <a
                      href={evidenciaPreview.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-primary underline-offset-4 hover:underline"
                    >
                      Abrir conteúdo em nova aba
                    </a>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Clique em “Pré-visualizar” em um anexo já salvo para carregar o conteúdo.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
