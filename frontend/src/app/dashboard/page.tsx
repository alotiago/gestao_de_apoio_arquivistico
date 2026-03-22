"use client";

import { useEntrevistasResumo, useMetricsSummary } from "@/hooks/use-api";
import {
  BarChart3,
  FileText,
  FolderTree,
  Clock,
  AlertTriangle,
  ClipboardList,
  CheckCircle2,
  RotateCcw,
  Send,
  XCircle,
  Loader2,
} from "lucide-react";
import {
  DashboardPlaceholderChartCard,
  DashboardStatCard,
} from "@/components/dashboard/dashboard-cards";

type MetricsSummary = {
  requests_total: number;
  errors_total: number;
  availability_pct: number;
  avg_latency_ms: number;
  incidents_open: number;
};

type EntrevistasResumo = {
  total: number;
  por_status: Record<string, number>;
  esta_semana: number;
  este_mes: number;
};

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; icon: React.ElementType }
> = {
  em_andamento: {
    label: "Em andamento",
    color: "text-yellow-700",
    bg: "bg-yellow-50 border-yellow-200",
    icon: Loader2,
  },
  submetida: {
    label: "Submetidas",
    color: "text-blue-700",
    bg: "bg-blue-50 border-blue-200",
    icon: Send,
  },
  devolvida: {
    label: "Devolvidas",
    color: "text-red-700",
    bg: "bg-red-50 border-red-200",
    icon: RotateCcw,
  },
  concluida: {
    label: "Concluídas",
    color: "text-green-700",
    bg: "bg-green-50 border-green-200",
    icon: CheckCircle2,
  },
  cancelada: {
    label: "Canceladas",
    color: "text-gray-500",
    bg: "bg-gray-50 border-gray-200",
    icon: XCircle,
  },
};

export default function DashboardPage() {
  const { data: metricsRaw } = useMetricsSummary();
  const metrics = (metricsRaw as MetricsSummary | undefined) ?? null;

  const { data: resumoRaw } = useEntrevistasResumo();
  const resumo = (resumoRaw as EntrevistasResumo | undefined) ?? null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground">
          Visão geral do sistema de gestão arquivística
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardStatCard
          title="Requests API"
          value={String(metrics?.requests_total ?? 0)}
          description="Chamadas monitoradas na janela atual"
          icon={FileText}
        />
        <DashboardStatCard
          title="Disponibilidade"
          value={`${metrics?.availability_pct ?? 100}%`}
          description="SLO de disponibilidade observado"
          icon={FolderTree}
        />
        <DashboardStatCard
          title="Latência Média"
          value={`${metrics?.avg_latency_ms ?? 0}ms`}
          description="Média de latência das requisições"
          icon={Clock}
        />
        <DashboardStatCard
          title="Incidentes"
          value={String(metrics?.incidents_open ?? 0)}
          description="Alertas abertos por SLO/erro"
          icon={AlertTriangle}
        />
      </div>

      {/* Painel de Entrevistas */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <ClipboardList className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">
            Painel de Entrevistas
          </h2>
          {resumo && (
            <span className="ml-auto text-sm text-muted-foreground">
              {resumo.esta_semana} esta semana &middot; {resumo.este_mes} este mês
            </span>
          )}
        </div>

        {/* Total + status grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* Card total */}
          <div className="col-span-1 rounded-xl border border-primary/20 bg-primary/5 p-4 flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Total
            </span>
            <span className="text-3xl font-bold text-primary">
              {resumo?.total ?? "—"}
            </span>
            <span className="text-xs text-muted-foreground">entrevistas</span>
          </div>

          {/* Cards por status */}
          {Object.entries(STATUS_CONFIG).map(([st, cfg]) => {
            const Icon = cfg.icon;
            const count = resumo?.por_status?.[st] ?? 0;
            return (
              <div
                key={st}
                className={`rounded-xl border p-4 flex flex-col gap-1 ${cfg.bg}`}
              >
                <div className="flex items-center gap-1.5">
                  <Icon className={`h-3.5 w-3.5 ${cfg.color}`} />
                  <span
                    className={`text-xs font-medium uppercase tracking-wide ${cfg.color}`}
                  >
                    {cfg.label}
                  </span>
                </div>
                <span className={`text-3xl font-bold ${cfg.color}`}>
                  {resumo ? count : "—"}
                </span>
              </div>
            );
          })}
        </div>

        {/* Barra de progresso proporcional */}
        {resumo && resumo.total > 0 && (
          <div className="mt-4">
            <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted gap-0.5">
              {Object.entries(STATUS_CONFIG).map(([st, cfg]) => {
                const count = resumo.por_status?.[st] ?? 0;
                const pct = (count / resumo.total) * 100;
                if (pct === 0) return null;
                return (
                  <div
                    key={st}
                    title={`${cfg.label}: ${count} (${pct.toFixed(0)}%)`}
                    style={{ width: `${pct}%` }}
                    className={`h-full transition-all ${
                      st === "em_andamento"
                        ? "bg-yellow-400"
                        : st === "submetida"
                        ? "bg-blue-400"
                        : st === "devolvida"
                        ? "bg-red-400"
                        : st === "concluida"
                        ? "bg-green-400"
                        : "bg-gray-300"
                    }`}
                  />
                );
              })}
            </div>
            <div className="flex flex-wrap gap-4 mt-2 text-xs text-muted-foreground">
              {Object.entries(STATUS_CONFIG).map(([st, cfg]) => {
                const count = resumo.por_status?.[st] ?? 0;
                return (
                  <span key={st} className="flex items-center gap-1">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        st === "em_andamento"
                          ? "bg-yellow-400"
                          : st === "submetida"
                          ? "bg-blue-400"
                          : st === "devolvida"
                          ? "bg-red-400"
                          : st === "concluida"
                          ? "bg-green-400"
                          : "bg-gray-300"
                      }`}
                    />
                    {cfg.label}: {count}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Placeholder Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardPlaceholderChartCard
          title="Latência e SLO"
          description="Resumo alimentado pelo endpoint de métricas operacionais"
          icon={BarChart3}
        />
        <DashboardPlaceholderChartCard
          title="Erros e Incidentes"
          description="Acompanhe desvios de erro e alertas de confiabilidade"
          icon={FolderTree}
        />
      </div>
    </div>
  );
}
