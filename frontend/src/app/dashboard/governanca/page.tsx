"use client";

import { FormEvent, useMemo, useState } from "react";
import api from "@/lib/api";
import {
  useAuditLogs,
  useMatrizRastreabilidade,
  usePcdArvore,
} from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type PcdNivel = {
  id: string;
  tipo: string;
  codigo: string;
  titulo: string;
  filhos: PcdNivel[];
};

type MatrizItem = {
  id: string;
  pcd_nivel_id: string;
  legislacao: string;
  artigo: string | null;
  norma_interna: string | null;
  risco: string | null;
  evidencia: string | null;
  created_at: string;
};

type AuditItem = {
  id: number;
  acao: string;
  entidade: string;
  entidade_id: string | null;
  usuario_id: string | null;
  ip_address: string | null;
  created_at: string;
};

type IntegridadeResult = {
  total_logs: number;
  total_inconsistencias: number;
  integridade: string;
  inconsistencias: Array<{ id: number; erro: string }>;
};

function flattenPcdTree(nodes: PcdNivel[]): PcdNivel[] {
  const queue = [...nodes];
  const flattened: PcdNivel[] = [];
  while (queue.length > 0) {
    const item = queue.shift();
    if (!item) {
      continue;
    }
    flattened.push(item);
    queue.push(...item.filhos);
  }
  return flattened;
}

export default function GovernancaPage() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [creatingEntrada, setCreatingEntrada] = useState(false);
  const [checkingIntegridade, setCheckingIntegridade] = useState(false);

  const [pcdNivelId, setPcdNivelId] = useState("");
  const [legislacao, setLegislacao] = useState("");
  const [artigo, setArtigo] = useState("");
  const [normaInterna, setNormaInterna] = useState("");
  const [risco, setRisco] = useState("medio");
  const [evidencia, setEvidencia] = useState("");

  const [integridade, setIntegridade] = useState<IntegridadeResult | null>(null);

  const { data: pcdRaw } = usePcdArvore();
  const niveisFlat = useMemo(
    () => flattenPcdTree((pcdRaw as PcdNivel[] | undefined) ?? []),
    [pcdRaw]
  );

  const {
    data: matrizRaw,
    mutate: mutateMatriz,
    isLoading: loadingMatriz,
  } = useMatrizRastreabilidade();
  const matriz = (matrizRaw as MatrizItem[] | undefined) ?? [];

  const { data: logsRaw, isLoading: loadingLogs } = useAuditLogs();
  const logs = (logsRaw as AuditItem[] | undefined) ?? [];

  async function handleCriarEntrada(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!pcdNivelId) {
      setErrorMessage("Selecione um nível do PCD para criar entrada de matriz.");
      return;
    }

    setErrorMessage(null);
    setCreatingEntrada(true);
    try {
      await api.post("/governanca/matriz", {
        pcd_nivel_id: pcdNivelId,
        legislacao,
        artigo: artigo || null,
        norma_interna: normaInterna || null,
        regra_retencao_id: null,
        risco,
        evidencia: evidencia || null,
      });

      setPcdNivelId("");
      setLegislacao("");
      setArtigo("");
      setNormaInterna("");
      setRisco("medio");
      setEvidencia("");
      await mutateMatriz();
    } catch {
      setErrorMessage("Falha ao criar entrada na matriz de rastreabilidade.");
    } finally {
      setCreatingEntrada(false);
    }
  }

  async function handleVerificarIntegridade() {
    setErrorMessage(null);
    setCheckingIntegridade(true);
    try {
      const { data } = await api.get<IntegridadeResult>(
        "/governanca/logs/verificar-integridade"
      );
      setIntegridade(data);
    } catch {
      setErrorMessage("Falha ao verificar integridade dos logs.");
    } finally {
      setCheckingIntegridade(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Governança</h1>
        <p className="text-muted-foreground">
          Sprint 8 (US-040/US-041): matriz de rastreabilidade e auditoria
        </p>
      </div>

      {errorMessage ? (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Nova Entrada da Matriz</CardTitle>
            <CardDescription>
              Vincular nível PCD, base legal e risco na rastreabilidade
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCriarEntrada} className="space-y-3">
              <select
                required
                value={pcdNivelId}
                onChange={(event) => setPcdNivelId(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Nível do PCD</option>
                {niveisFlat.map((nivel) => (
                  <option key={nivel.id} value={nivel.id}>
                    [{nivel.tipo}] {nivel.codigo} - {nivel.titulo}
                  </option>
                ))}
              </select>

              <input
                required
                value={legislacao}
                onChange={(event) => setLegislacao(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Legislação"
              />

              <input
                value={artigo}
                onChange={(event) => setArtigo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Artigo (opcional)"
              />

              <input
                value={normaInterna}
                onChange={(event) => setNormaInterna(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Norma interna (opcional)"
              />

              <select
                value={risco}
                onChange={(event) => setRisco(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="baixo">Baixo</option>
                <option value="medio">Médio</option>
                <option value="alto">Alto</option>
                <option value="critico">Crítico</option>
              </select>

              <textarea
                value={evidencia}
                onChange={(event) => setEvidencia(event.target.value)}
                className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Evidência (opcional)"
              />

              <Button type="submit" className="w-full" disabled={creatingEntrada}>
                {creatingEntrada ? "Salvando..." : "Criar entrada"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Integridade de Logs</CardTitle>
            <CardDescription>
              Verificação da hashchain de auditoria (WORM lógico)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              type="button"
              onClick={handleVerificarIntegridade}
              disabled={checkingIntegridade}
            >
              {checkingIntegridade ? "Verificando..." : "Verificar integridade"}
            </Button>

            {integridade ? (
              <div className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">
                  Integridade: {integridade.integridade}
                </p>
                <p className="text-xs text-muted-foreground">
                  Logs: {integridade.total_logs} · Inconsistências: {integridade.total_inconsistencias}
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Execute a validação para ver o status da hashchain.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Matriz de Rastreabilidade</CardTitle>
            <CardDescription>
              {loadingMatriz ? "Carregando matriz..." : `${matriz.length} entrada(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {matriz.map((item) => (
              <div key={item.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">{item.legislacao}</p>
                <p className="text-xs text-muted-foreground">
                  Risco: {item.risco || "—"} · PCD: {item.pcd_nivel_id}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audit Logs</CardTitle>
            <CardDescription>
              {loadingLogs ? "Carregando logs..." : `${logs.length} registro(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {logs.map((log) => (
              <div key={log.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">
                  #{log.id} · {log.acao} em {log.entidade}
                </p>
                <p className="text-xs text-muted-foreground">
                  {new Date(log.created_at).toLocaleString("pt-BR")} · IP: {log.ip_address || "—"}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
