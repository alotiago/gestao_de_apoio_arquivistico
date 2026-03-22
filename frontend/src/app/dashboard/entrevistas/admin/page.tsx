"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Download,
  Eye,
  Filter,
  Loader2,
  RotateCcw,
  Search,
  Send,
  X,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useEntrevistasResumo } from "@/hooks/use-api";

// ─── Tipos ────────────────────────────────────────────────────────────────────

type EntrevistaAdminItem = {
  id: string;
  roteiro_id: string;
  roteiro_titulo: string;
  entrevistador_id: string | null;
  cliente_id: string | null;
  cliente_email: string | null;
  status: string;
  motivo_devolucao: string | null;
  total_respostas: number;
  created_at: string;
  completed_at: string | null;
};

type EntrevistaAdminPaginado = {
  items: EntrevistaAdminItem[];
  total: number;
  page: number;
  per_page: number;
};

type EntrevistaDetalhe = EntrevistaAdminItem & {
  respostas: Record<string, unknown>;
};

type EntrevistasResumo = {
  total: number;
  por_status: Record<string, number>;
  esta_semana: number;
  este_mes: number;
};

// ─── Configurações de status ───────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; dot: string; icon: React.ReactNode }
> = {
  em_andamento: {
    label: "Em Andamento",
    bg: "bg-yellow-50",
    text: "text-yellow-700",
    dot: "bg-yellow-400",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  submetida: {
    label: "Submetida",
    bg: "bg-blue-50",
    text: "text-blue-700",
    dot: "bg-blue-500",
    icon: <Send className="h-3 w-3" />,
  },
  devolvida: {
    label: "Devolvida",
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
    icon: <RotateCcw className="h-3 w-3" />,
  },
  concluida: {
    label: "Concluída",
    bg: "bg-green-50",
    text: "text-green-700",
    dot: "bg-green-500",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  cancelada: {
    label: "Cancelada",
    bg: "bg-gray-100",
    text: "text-gray-500",
    dot: "bg-gray-400",
    icon: <XCircle className="h-3 w-3" />,
  },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? {
    label: status,
    bg: "bg-gray-100",
    text: "text-gray-600",
    dot: "bg-gray-400",
    icon: null,
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.bg} ${cfg.text}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function KpiCard({
  label,
  value,
  sub,
  color,
  icon,
}: {
  label: string;
  value: number | string;
  sub?: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 pt-5 pb-4">
        <div className={`rounded-xl p-3 ${color}`}>{icon}</div>
        <div>
          <p className="text-2xl font-bold leading-none">{value}</p>
          <p className="mt-1 text-sm font-medium text-muted-foreground">{label}</p>
          {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function fmt(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function shortId(id: string) {
  return id.slice(0, 8).toUpperCase();
}

function exportCsv(items: EntrevistaAdminItem[]) {
  const header = [
    "ID",
    "Roteiro",
    "Cliente",
    "Status",
    "Respostas",
    "Criado em",
    "Concluído em",
    "Motivo Devolução",
  ].join(";");
  const rows = items.map((e) =>
    [
      e.id,
      `"${e.roteiro_titulo}"`,
      e.cliente_email ?? "",
      e.status,
      e.total_respostas,
      fmt(e.created_at),
      fmt(e.completed_at),
      `"${e.motivo_devolucao ?? ""}"`,
    ].join(";")
  );
  const blob = new Blob([header + "\n" + rows.join("\n")], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `entrevistas_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Componente principal ──────────────────────────────────────────────────────

export default function AdminEntrevistasPage() {
  // resumo SWR
  const { data: resumoData } = useEntrevistasResumo();
  const resumo = resumoData as EntrevistasResumo | undefined;

  // listagem
  const [data, setData] = useState<EntrevistaAdminPaginado | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // filtros
  const [filtroStatus, setFiltroStatus] = useState("");
  const [filtroRoteiro, setFiltroRoteiro] = useState("");
  const [filtroBusca, setFiltroBusca] = useState("");
  const [filtroDataDe, setFiltroDataDe] = useState("");
  const [filtroDataAte, setFiltroDataAte] = useState("");
  const [page, setPage] = useState(1);

  // ações
  const [modalDevolver, setModalDevolver] = useState<EntrevistaAdminItem | null>(null);
  const [motivoDevolucao, setMotivoDevolucao] = useState("");
  const [modalConfirm, setModalConfirm] = useState<{
    item: EntrevistaAdminItem;
    acao: "concluida" | "cancelada";
  } | null>(null);
  const [modalDetalhe, setModalDetalhe] = useState<EntrevistaDetalhe | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // roteiros disponíveis para filtro
  const [roteiros, setRoteiros] = useState<{ id: string; titulo: string }[]>([]);

  const carregar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filtroStatus) params.set("status", filtroStatus);
      if (filtroRoteiro) params.set("roteiro_id", filtroRoteiro);
      if (filtroBusca) params.set("busca", filtroBusca);
      if (filtroDataDe) params.set("data_de", new Date(filtroDataDe).toISOString());
      if (filtroDataAte) params.set("data_ate", new Date(filtroDataAte).toISOString());
      params.set("page", String(page));
      params.set("per_page", "20");
      const { data: res } = await api.get<EntrevistaAdminPaginado>(
        `/roteiros/entrevistas?${params.toString()}`
      );
      setData(res);
    } catch {
      setError("Erro ao carregar entrevistas.");
    } finally {
      setLoading(false);
    }
  }, [filtroStatus, filtroRoteiro, filtroBusca, filtroDataDe, filtroDataAte, page]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useEffect(() => {
    api
      .get<{ items: { id: string; titulo: string }[] }>("/roteiros?per_page=100")
      .then(({ data: r }) => setRoteiros(r.items))
      .catch(() => {});
  }, []);

  function resetFiltros() {
    setFiltroStatus("");
    setFiltroRoteiro("");
    setFiltroBusca("");
    setFiltroDataDe("");
    setFiltroDataAte("");
    setPage(1);
  }

  // ─── Ver detalhes ─────────────────────────────────────────────────────────────
  async function verDetalhes(item: EntrevistaAdminItem) {
    try {
      const { data: det } = await api.get<EntrevistaDetalhe>(
        `/roteiros/entrevistas/${item.id}`
      );
      setModalDetalhe(det);
    } catch {
      setModalDetalhe({ ...item, respostas: {} });
    }
  }

  // ─── Devolver ─────────────────────────────────────────────────────────────────
  async function executarDevolucao() {
    if (!modalDevolver || !motivoDevolucao.trim()) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await api.patch(`/roteiros/entrevistas/${modalDevolver.id}`, {
        status: "devolvida",
        motivo_devolucao: motivoDevolucao.trim(),
      });
      setModalDevolver(null);
      setMotivoDevolucao("");
      carregar();
    } catch {
      setActionError("Falha ao devolver a entrevista. Verifique se o status é 'submetida'.");
    } finally {
      setActionLoading(false);
    }
  }

  // ─── Concluir / Cancelar ──────────────────────────────────────────────────────
  async function executarAcao() {
    if (!modalConfirm) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await api.patch(`/roteiros/entrevistas/${modalConfirm.item.id}`, {
        status: modalConfirm.acao,
      });
      setModalConfirm(null);
      carregar();
    } catch {
      setActionError(`Não foi possível alterar o status. Verifique se a transição é permitida.`);
    } finally {
      setActionLoading(false);
    }
  }

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  // ─── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <ClipboardList className="h-6 w-6 text-primary" />
            Administração de Entrevistas
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie, revise e acompanhe todas as entrevistas do sistema.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => data && exportCsv(data.items)}
          disabled={!data || data.items.length === 0}
        >
          <Download className="mr-2 h-4 w-4" />
          Exportar CSV
        </Button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          label="Total de Entrevistas"
          value={resumo?.total ?? "—"}
          sub={`${resumo?.esta_semana ?? 0} esta semana`}
          color="bg-primary/10"
          icon={<ClipboardList className="h-5 w-5 text-primary" />}
        />
        <KpiCard
          label="Em Andamento"
          value={resumo?.por_status?.em_andamento ?? "—"}
          color="bg-yellow-100"
          icon={<Loader2 className="h-5 w-5 text-yellow-600" />}
        />
        <KpiCard
          label="Submetidas"
          value={resumo?.por_status?.submetida ?? "—"}
          sub="Aguardando análise"
          color="bg-blue-100"
          icon={<Send className="h-5 w-5 text-blue-600" />}
        />
        <KpiCard
          label="Concluídas"
          value={resumo?.por_status?.concluida ?? "—"}
          sub={`${resumo?.este_mes ?? 0} este mês`}
          color="bg-green-100"
          icon={<CheckCircle2 className="h-5 w-5 text-green-600" />}
        />
      </div>

      {/* Relatório por status */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Distribuição por Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-3">
            {Object.entries(STATUS_CONFIG).map(([st, cfg]) => (
              <button
                key={st}
                className={`rounded-lg border p-3 text-left transition hover:opacity-80 ${
                  filtroStatus === st ? "ring-2 ring-primary" : ""
                }`}
                onClick={() => {
                  setFiltroStatus(filtroStatus === st ? "" : st);
                  setPage(1);
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`inline-block h-2 w-2 rounded-full ${cfg.dot}`} />
                  <span className="text-xs font-medium text-muted-foreground">{cfg.label}</span>
                </div>
                <p className="text-xl font-bold">
                  {resumo?.por_status?.[st] ?? 0}
                </p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filtros */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Filter className="h-4 w-4" /> Filtros
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={resetFiltros}>
              <X className="mr-1 h-3 w-3" /> Limpar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            {/* Busca */}
            <div className="relative lg:col-span-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                className="w-full rounded-md border bg-background pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Email do cliente"
                value={filtroBusca}
                onChange={(e) => { setFiltroBusca(e.target.value); setPage(1); }}
              />
            </div>

            {/* Status */}
            <select
              className="rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={filtroStatus}
              onChange={(e) => { setFiltroStatus(e.target.value); setPage(1); }}
            >
              <option value="">Todos os status</option>
              {Object.entries(STATUS_CONFIG).map(([st, cfg]) => (
                <option key={st} value={st}>{cfg.label}</option>
              ))}
            </select>

            {/* Roteiro */}
            <select
              className="rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={filtroRoteiro}
              onChange={(e) => { setFiltroRoteiro(e.target.value); setPage(1); }}
            >
              <option value="">Todos os roteiros</option>
              {roteiros.map((r) => (
                <option key={r.id} value={r.id}>{r.titulo}</option>
              ))}
            </select>

            {/* Data de */}
            <div>
              <label className="block text-xs text-muted-foreground mb-1">De</label>
              <input
                type="date"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={filtroDataDe}
                onChange={(e) => { setFiltroDataDe(e.target.value); setPage(1); }}
              />
            </div>

            {/* Data até */}
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Até</label>
              <input
                type="date"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={filtroDataAte}
                onChange={(e) => { setFiltroDataAte(e.target.value); setPage(1); }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabela */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              Entrevistas{" "}
              {data && (
                <span className="text-muted-foreground font-normal">
                  ({data.total} resultado{data.total !== 1 ? "s" : ""})
                </span>
              )}
            </CardTitle>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {error && (
            <div className="p-6 text-sm text-red-600 bg-red-50">{error}</div>
          )}

          {!error && (
            <>
              {/* Desktop Table */}
              <div className="hidden sm:block overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">ID</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Roteiro</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Cliente</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Respostas</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Criado em</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Concluído em</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.items.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-4 py-10 text-center text-muted-foreground">
                          Nenhuma entrevista encontrada com os filtros aplicados.
                        </td>
                      </tr>
                    )}
                    {data?.items.map((item) => (
                      <tr key={item.id} className="border-b last:border-0 hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                          {shortId(item.id)}
                        </td>
                        <td className="px-4 py-3 max-w-[180px] truncate font-medium">
                          {item.roteiro_titulo}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground max-w-[160px] truncate">
                          {item.cliente_email ?? <span className="italic">Sem cliente</span>}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={item.status} />
                          {item.motivo_devolucao && (
                            <p className="mt-1 text-xs text-red-500 truncate max-w-[140px]" title={item.motivo_devolucao}>
                              {item.motivo_devolucao}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-muted text-xs font-semibold">
                            {item.total_respostas}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                          {fmt(item.created_at)}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                          {fmt(item.completed_at)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            {/* Detalhes */}
                            <button
                              title="Ver detalhes"
                              className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition"
                              onClick={() => verDetalhes(item)}
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            {/* Devolver (só se submetida) */}
                            {item.status === "submetida" && (
                              <button
                                title="Devolver"
                                className="rounded p-1.5 text-red-400 hover:bg-red-50 hover:text-red-600 transition"
                                onClick={() => { setModalDevolver(item); setMotivoDevolucao(""); setActionError(null); }}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </button>
                            )}
                            {/* Concluir */}
                            {(item.status === "em_andamento" || item.status === "submetida") && (
                              <button
                                title="Concluir"
                                className="rounded p-1.5 text-green-500 hover:bg-green-50 hover:text-green-700 transition"
                                onClick={() => { setModalConfirm({ item, acao: "concluida" }); setActionError(null); }}
                              >
                                <CheckCircle2 className="h-4 w-4" />
                              </button>
                            )}
                            {/* Cancelar */}
                            {item.status !== "concluida" && item.status !== "cancelada" && (
                              <button
                                title="Cancelar"
                                className="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition"
                                onClick={() => { setModalConfirm({ item, acao: "cancelada" }); setActionError(null); }}
                              >
                                <XCircle className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="sm:hidden space-y-3">
                {data?.items.length === 0 && (
                  <div className="text-center py-10 text-muted-foreground">
                    Nenhuma entrevista encontrada com os filtros aplicados.
                  </div>
                )}
                {data?.items.map((item) => (
                  <div key={item.id} className="border rounded-lg p-4 bg-card hover:bg-muted/50 transition-colors space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium line-clamp-2">{item.roteiro_titulo}</p>
                        <p className="text-xs text-muted-foreground">{item.cliente_email ?? "Sem cliente"}</p>
                      </div>
                      <StatusBadge status={item.status} />
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-muted-foreground">ID</p>
                        <p className="font-mono text-xs">{shortId(item.id)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Respostas</p>
                        <p className="font-semibold">{item.total_respostas}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Criado em</p>
                        <p className="text-xs">{fmt(item.created_at)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Concluído em</p>
                        <p className="text-xs">{fmt(item.completed_at) || "—"}</p>
                      </div>
                    </div>

                    {item.motivo_devolucao && (
                      <div className="bg-red-50 border border-red-200 rounded p-2">
                        <p className="text-xs font-medium text-red-600">Motivo:</p>
                        <p className="text-xs text-red-600 line-clamp-2">{item.motivo_devolucao}</p>
                      </div>
                    )}

                    {/* Actions Row */}
                    <div className="flex items-center gap-2 pt-2 border-t">
                      <button
                        title="Ver detalhes"
                        className="flex-1 px-2 py-2 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition text-xs font-medium flex items-center justify-center gap-1"
                        onClick={() => verDetalhes(item)}
                      >
                        <Eye className="h-4 w-4" /> Detalhes
                      </button>
                      {item.status === "submetida" && (
                        <button
                          title="Devolver"
                          className="flex-1 px-2 py-2 rounded bg-red-50 hover:bg-red-100 text-red-600 transition text-xs font-medium flex items-center justify-center gap-1"
                          onClick={() => { setModalDevolver(item); setMotivoDevolucao(""); setActionError(null); }}
                        >
                          <RotateCcw className="h-4 w-4" /> Devolver
                        </button>
                      )}
                      {(item.status === "em_andamento" || item.status === "submetida") && (
                        <button
                          title="Concluir"
                          className="flex-1 px-2 py-2 rounded bg-green-50 hover:bg-green-100 text-green-600 transition text-xs font-medium flex items-center justify-center gap-1"
                          onClick={() => { setModalConfirm({ item, acao: "concluida" }); setActionError(null); }}
                        >
                          <CheckCircle2 className="h-4 w-4" /> Concluir
                        </button>
                      )}
                      {item.status !== "concluida" && item.status !== "cancelada" && (
                        <button
                          title="Cancelar"
                          className="flex-1 px-2 py-2 rounded bg-gray-100 hover:bg-gray-200 text-gray-600 transition text-xs font-medium flex items-center justify-center gap-1"
                          onClick={() => { setModalConfirm({ item, acao: "cancelada" }); setActionError(null); }}
                        >
                          <XCircle className="h-4 w-4" /> Cancelar
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Paginação */}
          {data && totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <span className="text-xs text-muted-foreground">
                Página {page} de {totalPages} · {data.total} entrevistas
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ─── Modal: Devolver ──────────────────────────────────────────────────── */}
      {modalDevolver && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl border bg-background shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b px-5 py-4">
              <h2 className="font-semibold flex items-center gap-2">
                <RotateCcw className="h-4 w-4 text-red-500" />
                Devolver Entrevista
              </h2>
              <button onClick={() => setModalDevolver(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="px-5 py-4 space-y-4">
              <div className="rounded-lg bg-muted/50 p-3 text-sm">
                <p className="font-medium">{modalDevolver.roteiro_titulo}</p>
                <p className="text-muted-foreground text-xs mt-1">
                  Cliente: {modalDevolver.cliente_email ?? "—"} · ID: {shortId(modalDevolver.id)}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium block mb-1.5">
                  Motivo da devolução <span className="text-red-500">*</span>
                </label>
                <textarea
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows={4}
                  placeholder="Descreva o motivo, ex: Faltam documentos comprobatórios da série X..."
                  value={motivoDevolucao}
                  onChange={(e) => setMotivoDevolucao(e.target.value)}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {motivoDevolucao.length} caracteres
                </p>
              </div>

              {actionError && (
                <p className="text-sm text-red-600 bg-red-50 rounded p-2">{actionError}</p>
              )}
            </div>
            <div className="flex justify-end gap-2 border-t px-5 py-4">
              <Button variant="outline" onClick={() => setModalDevolver(null)} disabled={actionLoading}>
                Cancelar
              </Button>
              <Button
                variant="destructive"
                onClick={executarDevolucao}
                disabled={actionLoading || !motivoDevolucao.trim()}
              >
                {actionLoading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Devolvendo...</>
                ) : (
                  <><RotateCcw className="mr-2 h-4 w-4" /> Devolver</>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Modal: Confirmar Concluir/Cancelar ──────────────────────────────── */}
      {modalConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl border bg-background shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b px-5 py-4">
              <h2 className="font-semibold">
                {modalConfirm.acao === "concluida" ? "Concluir Entrevista" : "Cancelar Entrevista"}
              </h2>
              <button onClick={() => setModalConfirm(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="px-5 py-4 space-y-3">
              <p className="text-sm text-muted-foreground">
                {modalConfirm.acao === "concluida"
                  ? "Confirma a conclusão desta entrevista? Ela será marcada como concluída e não poderá ser alterada."
                  : "Confirma o cancelamento? Esta ação não pode ser desfeita."}
              </p>
              <div className="rounded-lg bg-muted/50 p-3 text-sm">
                <p className="font-medium">{modalConfirm.item.roteiro_titulo}</p>
                <p className="text-muted-foreground text-xs mt-1">
                  {modalConfirm.item.cliente_email ?? "Sem cliente"} · <StatusBadge status={modalConfirm.item.status} />
                </p>
              </div>
              {actionError && (
                <p className="text-sm text-red-600 bg-red-50 rounded p-2">{actionError}</p>
              )}
            </div>
            <div className="flex justify-end gap-2 border-t px-5 py-4">
              <Button variant="outline" onClick={() => setModalConfirm(null)} disabled={actionLoading}>
                Não
              </Button>
              <Button
                variant={modalConfirm.acao === "concluida" ? "default" : "destructive"}
                onClick={executarAcao}
                disabled={actionLoading}
              >
                {actionLoading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Aguarde...</>
                ) : modalConfirm.acao === "concluida" ? (
                  <><CheckCircle2 className="mr-2 h-4 w-4" /> Sim, Concluir</>
                ) : (
                  <><XCircle className="mr-2 h-4 w-4" /> Sim, Cancelar</>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Modal: Detalhes ──────────────────────────────────────────────────── */}
      {modalDetalhe && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-xl border bg-background shadow-xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b px-5 py-4 shrink-0">
              <h2 className="font-semibold flex items-center gap-2">
                <Eye className="h-4 w-4 text-primary" />
                Detalhes da Entrevista
              </h2>
              <button onClick={() => setModalDetalhe(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="overflow-y-auto px-5 py-4 space-y-4">
              {/* Cabeçalho */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">ID</p>
                  <p className="font-mono">{modalDetalhe.id}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Status</p>
                  <StatusBadge status={modalDetalhe.status} />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Roteiro</p>
                  <p className="font-medium">{modalDetalhe.roteiro_titulo}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Cliente</p>
                  <p>{modalDetalhe.cliente_email ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Criado em</p>
                  <p>{fmt(modalDetalhe.created_at)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Concluído em</p>
                  <p>{fmt(modalDetalhe.completed_at)}</p>
                </div>
              </div>

              {/* Motivo devolução */}
              {modalDetalhe.motivo_devolucao && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-3">
                  <p className="text-xs font-medium text-red-700 mb-1">Motivo da Devolução</p>
                  <p className="text-sm text-red-800">{modalDetalhe.motivo_devolucao}</p>
                </div>
              )}

              {/* Respostas */}
              <div>
                <p className="text-sm font-medium mb-2">
                  Respostas ({Object.keys(modalDetalhe.respostas ?? {}).length})
                </p>
                {Object.keys(modalDetalhe.respostas ?? {}).length === 0 ? (
                  <p className="text-sm text-muted-foreground italic">Nenhuma resposta registrada.</p>
                ) : (
                  <div className="rounded-lg border divide-y max-h-64 overflow-y-auto">
                    {Object.entries(modalDetalhe.respostas ?? {}).map(([k, v]) => (
                      <div key={k} className="px-3 py-2 text-sm">
                        <p className="text-xs font-mono text-muted-foreground">{k}</p>
                        <p className="mt-0.5 truncate">{String(v)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end border-t px-5 py-4 shrink-0">
              <Button variant="outline" onClick={() => setModalDetalhe(null)}>
                Fechar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
