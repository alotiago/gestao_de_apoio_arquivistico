"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// ===== Types =====

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

type EntrevistaDetalhe = {
  id: string;
  roteiro_id: string;
  roteiro_titulo: string;
  roteiro_area: string | null;
  status: string;
  respostas: Record<string, unknown>;
  motivo_devolucao: string | null;
  created_at: string;
  completed_at: string | null;
  perguntas: PerguntaItem[];
};

// ===== Condition engine (simplified) =====

function evaluateCondition(
  condicao: CondicaoItem,
  respostas: Record<string, unknown>
): boolean {
  const { operador, valor } = condicao;
  const ref = (valor as Record<string, unknown>)?.ref as string | undefined;
  const expected = (valor as Record<string, unknown>)?.valor;
  const actual = ref ? respostas[ref] : undefined;

  switch (operador) {
    case "EQ":
      return actual === expected;
    case "NEQ":
      return actual !== expected;
    case "GT":
      return Number(actual) > Number(expected);
    case "LT":
      return Number(actual) < Number(expected);
    default:
      return true;
  }
}

function isVisible(
  pergunta: PerguntaItem,
  respostas: Record<string, unknown>
): boolean {
  for (const cond of pergunta.condicoes) {
    const result = evaluateCondition(cond, respostas);
    if (cond.acao === "ocultar" && result) return false;
    if (cond.acao === "mostrar" && !result) return false;
  }
  return true;
}

// ===== Status config =====

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  em_andamento: { label: "Em andamento", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  submetida: { label: "Submetida", color: "bg-blue-100 text-blue-800 border-blue-200" },
  devolvida: { label: "Devolvida", color: "bg-red-100 text-red-800 border-red-200" },
  concluida: { label: "Concluída", color: "bg-green-100 text-green-800 border-green-200" },
  cancelada: { label: "Cancelada", color: "bg-gray-100 text-gray-800 border-gray-200" },
};

// ===== Page component =====

export default function EntrevistaClientePage() {
  const params = useParams();
  const router = useRouter();
  const entrevistaId = params.id as string;

  // State
  const [entrevista, setEntrevista] = useState<EntrevistaDetalhe | null>(null);
  const [respostas, setRespostas] = useState<Record<string, unknown>>({});
  const [evidencias, setEvidencias] = useState<EvidenciaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [stepIndex, setStepIndex] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [arquivoInputKey, setArquivoInputKey] = useState(0);

  // Load entrevista + evidencias
  useEffect(() => {
    async function load() {
      try {
        const [entResp, evidResp] = await Promise.all([
          api.get(`/portal/entrevistas/${entrevistaId}`),
          api.get(`/portal/entrevistas/${entrevistaId}/evidencias`),
        ]);
        setEntrevista(entResp.data);
        setRespostas(entResp.data.respostas || {});
        setEvidencias(evidResp.data);
      } catch {
        setError("Não foi possível carregar a entrevista.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [entrevistaId]);

  // Computed
  const editavel = entrevista
    ? entrevista.status === "em_andamento" || entrevista.status === "devolvida"
    : false;

  const perguntasVisiveis = useMemo(() => {
    if (!entrevista) return [];
    return entrevista.perguntas
      .filter((p) => isVisible(p, respostas))
      .sort((a, b) => a.ordem - b.ordem);
  }, [entrevista, respostas]);

  const perguntaAtual = perguntasVisiveis[stepIndex] ?? null;

  const obrigatoriasRespondidas = useMemo(() => {
    const obrigatorias = perguntasVisiveis.filter((p) => p.obrigatoria);
    const respondidas = obrigatorias.filter((p) => {
      const v = respostas[p.id];
      return v !== undefined && v !== null && String(v).trim() !== "";
    });
    return { total: obrigatorias.length, done: respondidas.length };
  }, [perguntasVisiveis, respostas]);

  const progresso =
    obrigatoriasRespondidas.total > 0
      ? Math.round(
          (obrigatoriasRespondidas.done / obrigatoriasRespondidas.total) * 100
        )
      : 0;

  // Handlers
  const handleRespostaChange = useCallback(
    (perguntaId: string, valor: unknown) => {
      setRespostas((prev) => ({ ...prev, [perguntaId]: valor }));
    },
    []
  );

  const handleSalvar = useCallback(async () => {
    if (!editavel) return;
    setSaving(true);
    setError("");
    try {
      await api.patch(`/portal/entrevistas/${entrevistaId}`, { respostas });
      setSuccessMsg("Respostas salvas!");
      setTimeout(() => setSuccessMsg(""), 2000);
    } catch {
      setError("Erro ao salvar respostas.");
    } finally {
      setSaving(false);
    }
  }, [entrevistaId, respostas, editavel]);

  const handleSubmeter = useCallback(async () => {
    if (!editavel) return;
    setSubmitting(true);
    setError("");
    try {
      // Salvar antes de submeter
      await api.patch(`/portal/entrevistas/${entrevistaId}`, { respostas });
      const { data } = await api.post(
        `/portal/entrevistas/${entrevistaId}/submeter`
      );
      setEntrevista((prev) => (prev ? { ...prev, status: data.status } : prev));
      setSuccessMsg("Entrevista submetida com sucesso!");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr.response?.data?.detail || "Erro ao submeter entrevista."
      );
    } finally {
      setSubmitting(false);
    }
  }, [entrevistaId, respostas, editavel]);

  const handleUpload = useCallback(async () => {
    if (!arquivo || !editavel) return;
    setUploading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", arquivo);
      if (perguntaAtual) form.append("pergunta_id", perguntaAtual.id);
      const { data } = await api.post(
        `/portal/entrevistas/${entrevistaId}/evidencias`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setEvidencias((prev) => [data, ...prev]);
      setArquivo(null);
      setArquivoInputKey((k) => k + 1);
    } catch {
      setError("Erro ao enviar arquivo.");
    } finally {
      setUploading(false);
    }
  }, [arquivo, editavel, entrevistaId, perguntaAtual]);

  const handleExcluirEvidencia = useCallback(
    async (evidenciaId: string) => {
      if (!editavel) return;
      try {
        await api.delete(
          `/portal/entrevistas/${entrevistaId}/evidencias/${evidenciaId}`
        );
        setEvidencias((prev) => prev.filter((e) => e.id !== evidenciaId));
      } catch {
        setError("Erro ao excluir evidência.");
      }
    },
    [entrevistaId, editavel]
  );

  // ===== Render =====

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center text-muted-foreground">
        Carregando entrevista...
      </div>
    );
  }

  if (!entrevista) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center">
        <p className="text-destructive">Entrevista não encontrada.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/portal")}>
          Voltar
        </Button>
      </div>
    );
  }

  const statusCfg = STATUS_CONFIG[entrevista.status] || STATUS_CONFIG.em_andamento;
  const evidenciasPergunta = perguntaAtual
    ? evidencias.filter((e) => e.pergunta_id === perguntaAtual.id)
    : [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/portal")}
            className="mb-1 -ml-2"
          >
            ← Voltar
          </Button>
          <h1 className="text-2xl font-bold text-foreground">
            {entrevista.roteiro_titulo}
          </h1>
          <p className="text-sm text-muted-foreground">
            {entrevista.roteiro_area && `${entrevista.roteiro_area} · `}
            Criada em{" "}
            {new Date(entrevista.created_at).toLocaleDateString("pt-BR")}
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusCfg.color}`}
        >
          {statusCfg.label}
        </span>
      </div>

      {/* Devolução banner */}
      {entrevista.status === "devolvida" && entrevista.motivo_devolucao && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <strong>Motivo da devolução:</strong> {entrevista.motivo_devolucao}
        </div>
      )}

      {/* Messages */}
      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          {successMsg}
        </div>
      )}

      {/* Progress bar */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-muted-foreground">Progresso</span>
            <span className="font-medium">
              {obrigatoriasRespondidas.done}/{obrigatoriasRespondidas.total} obrigatórias · {progresso}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${progresso}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
            <span>
              Pergunta {Math.min(stepIndex + 1, perguntasVisiveis.length)} de{" "}
              {perguntasVisiveis.length}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Wizard step */}
      {perguntaAtual && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                {perguntaAtual.ordem}
              </span>
              <CardTitle className="text-base">{perguntaAtual.texto}</CardTitle>
            </div>
            {perguntaAtual.secao && (
              <CardDescription>Seção: {perguntaAtual.secao}</CardDescription>
            )}
            {perguntaAtual.obrigatoria && (
              <span className="text-xs text-destructive">* Obrigatória</span>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Input by type */}
            {renderInput(
              perguntaAtual,
              respostas[perguntaAtual.id],
              editavel,
              handleRespostaChange
            )}

            {/* Evidencias for this question */}
            <div className="border-t pt-4 space-y-3">
              <p className="text-sm font-medium text-foreground">Evidências</p>
              {evidenciasPergunta.map((ev) => (
                <div
                  key={ev.id}
                  className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                >
                  <span className="truncate">{ev.nome_arquivo}</span>
                  {editavel && (
                    <button
                      type="button"
                      onClick={() => handleExcluirEvidencia(ev.id)}
                      className="ml-2 text-xs text-destructive hover:underline"
                    >
                      Excluir
                    </button>
                  )}
                </div>
              ))}
              {editavel && (
                <div className="flex items-center gap-2">
                  <input
                    key={arquivoInputKey}
                    type="file"
                    onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
                    className="text-sm"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!arquivo || uploading}
                    onClick={handleUpload}
                  >
                    {uploading ? "Enviando..." : "Enviar"}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          disabled={stepIndex === 0}
          onClick={() => {
            setStepIndex((i) => Math.max(0, i - 1));
            setArquivo(null);
          }}
        >
          ← Anterior
        </Button>

        <div className="flex gap-2">
          {editavel && (
            <Button variant="outline" disabled={saving} onClick={handleSalvar}>
              {saving ? "Salvando..." : "Salvar"}
            </Button>
          )}

          {stepIndex < perguntasVisiveis.length - 1 ? (
            <Button
              onClick={() => {
                if (editavel) handleSalvar();
                setStepIndex((i) => Math.min(perguntasVisiveis.length - 1, i + 1));
                setArquivo(null);
              }}
            >
              Próxima →
            </Button>
          ) : editavel ? (
            <Button
              disabled={submitting || obrigatoriasRespondidas.done < obrigatoriasRespondidas.total}
              onClick={() => {
                if (
                  confirm(
                    "Após submeter, você não poderá editar até uma eventual devolução. Confirma?"
                  )
                ) {
                  handleSubmeter();
                }
              }}
            >
              {submitting ? "Submetendo..." : "Submeter Entrevista"}
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ===== Input renderer =====

function renderInput(
  pergunta: PerguntaItem,
  valor: unknown,
  editavel: boolean,
  onChange: (id: string, val: unknown) => void
) {
  const { id, tipo, opcoes } = pergunta;
  const strVal = valor !== undefined && valor !== null ? String(valor) : "";

  switch (tipo) {
    case "texto":
      return (
        <textarea
          value={strVal}
          disabled={!editavel}
          onChange={(e) => onChange(id, e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-input px-3 py-2 text-sm disabled:bg-muted disabled:cursor-not-allowed"
          placeholder="Digite sua resposta..."
        />
      );

    case "numero":
      return (
        <input
          type="number"
          value={strVal}
          disabled={!editavel}
          onChange={(e) => onChange(id, e.target.value ? Number(e.target.value) : "")}
          className="w-full rounded-lg border border-input px-3 py-2 text-sm disabled:bg-muted disabled:cursor-not-allowed"
          placeholder="0"
        />
      );

    case "boolean":
      return (
        <div className="flex gap-4">
          {[
            { label: "Sim", val: true },
            { label: "Não", val: false },
          ].map((opt) => (
            <label key={String(opt.val)} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name={`bool-${id}`}
                checked={valor === opt.val}
                disabled={!editavel}
                onChange={() => onChange(id, opt.val)}
                className="accent-primary"
              />
              {opt.label}
            </label>
          ))}
        </div>
      );

    case "select": {
      const items = (opcoes as Record<string, unknown>)?.items;
      const list = Array.isArray(items) ? (items as string[]) : [];
      return (
        <select
          value={strVal}
          disabled={!editavel}
          onChange={(e) => onChange(id, e.target.value)}
          className="w-full rounded-lg border border-input px-3 py-2 text-sm disabled:bg-muted disabled:cursor-not-allowed"
        >
          <option value="">Selecione...</option>
          {list.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      );
    }

    case "multi_select": {
      const items = (opcoes as Record<string, unknown>)?.items;
      const list = Array.isArray(items) ? (items as string[]) : [];
      const selected = Array.isArray(valor) ? (valor as string[]) : [];
      return (
        <div className="space-y-2">
          {list.map((item) => (
            <label key={item} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={selected.includes(item)}
                disabled={!editavel}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...selected, item]
                    : selected.filter((s) => s !== item);
                  onChange(id, next);
                }}
                className="accent-primary"
              />
              {item}
            </label>
          ))}
        </div>
      );
    }

    default:
      return (
        <input
          type="text"
          value={strVal}
          disabled={!editavel}
          onChange={(e) => onChange(id, e.target.value)}
          className="w-full rounded-lg border border-input px-3 py-2 text-sm disabled:bg-muted disabled:cursor-not-allowed"
        />
      );
  }
}
