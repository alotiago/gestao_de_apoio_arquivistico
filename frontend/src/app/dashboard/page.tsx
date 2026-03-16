"use client";

import { useMetricsSummary } from "@/hooks/use-api";
import {
  BarChart3,
  FileText,
  FolderTree,
  Clock,
  AlertTriangle,
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

export default function DashboardPage() {
  const { data: metricsRaw } = useMetricsSummary();
  const metrics = (metricsRaw as MetricsSummary | undefined) ?? null;

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
