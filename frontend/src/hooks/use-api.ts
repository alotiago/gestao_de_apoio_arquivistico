import useSWR, { type SWRConfiguration } from "swr";
import api from "@/lib/api";

const fetcher = (url: string) => api.get(url).then((res) => res.data);

const dashboardSWRConfig: SWRConfiguration = {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  dedupingInterval: 30000,
};

function useDashboardSWR(key: string | null) {
  return useSWR(key, fetcher, dashboardSWRConfig);
}

// ===== Roteiros (EP1) =====

export function useRoteiros(page = 1, perPage = 20) {
  return useDashboardSWR(`/roteiros?page=${page}&per_page=${perPage}`);
}

export function useRoteiro(id: string | null) {
  return useDashboardSWR(id ? `/roteiros/${id}` : null);
}

// ===== PCD (EP2) =====

export function usePcdArvore() {
  return useDashboardSWR("/pcd/arvore");
}

export function usePcdNivel(id: string | null) {
  return useDashboardSWR(id ? `/pcd/${id}` : null);
}

// ===== TTD (EP3) =====

export function useRegrasRetencao() {
  return useDashboardSWR("/ttd/regras");
}

export function useLegalHolds() {
  return useDashboardSWR("/ttd/holds");
}

export function useOrdensDestinacao(status?: string) {
  const params = status ? `?status_filter=${status}` : "";
  return useDashboardSWR(`/ttd/ordens${params}`);
}

// ===== Ciclo de Vida (EP4) =====

export function useWorkflows(estado?: string) {
  const params = estado ? `?estado=${estado}` : "";
  return useDashboardSWR(`/ciclo-vida/workflows${params}`);
}

export function useJobs(status?: string) {
  const params = status ? `?status=${status}` : "";
  return useDashboardSWR(`/ciclo-vida/jobs${params}`);
}

// ===== Integração (EP6) =====

export function useImportacoesAcervo(status?: string) {
  const params = status ? `?status=${status}` : "";
  return useDashboardSWR(`/integracao/importacoes${params}`);
}

// ===== Dados e Migração (EP9) =====

export function useInventariosQualidade(importacaoId?: string) {
  const params = importacaoId ? `?importacao_id=${importacaoId}` : "";
  return useDashboardSWR(`/dados-migracao/inventarios${params}`);
}

export function useRegrasCleansing(ativo?: boolean) {
  const params = typeof ativo === "boolean" ? `?ativo=${ativo}` : "";
  return useDashboardSWR(`/dados-migracao/regras-cleansing${params}`);
}

export function useOndasMigracao(status?: string) {
  const params = status ? `?status=${status}` : "";
  return useDashboardSWR(`/dados-migracao/ondas${params}`);
}

// ===== Conhecimento (EP10) =====

export function useTemplatesConhecimento(query?: string) {
  const params = query ? `?query=${encodeURIComponent(query)}` : "";
  return useDashboardSWR(`/conhecimento/templates${params}`);
}

export function useTrilhasConhecimento() {
  return useDashboardSWR(`/conhecimento/trilhas`);
}

// ===== Governança (EP5) =====

export function useMatrizRastreabilidade(pcdNivelId?: string) {
  const params = pcdNivelId ? `?pcd_nivel_id=${pcdNivelId}` : "";
  return useDashboardSWR(`/governanca/matriz${params}`);
}

export function useAuditLogs(page = 1, perPage = 50) {
  return useDashboardSWR(`/governanca/logs?page=${page}&per_page=${perPage}`);
}

// ===== Admin =====

export function useUsuarios(page = 1, perPage = 20) {
  return useDashboardSWR(`/admin/usuarios?page=${page}&per_page=${perPage}`);
}

export function useStats() {
  return useDashboardSWR("/admin/stats");
}

export function useMetricsSummary() {
  return useDashboardSWR("/metrics/summary");
}

export function useEntrevistasResumo() {
  return useDashboardSWR("/roteiros/entrevistas/resumo");
}
