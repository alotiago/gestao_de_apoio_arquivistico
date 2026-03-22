"use client";

import { useState, useEffect, useCallback, type FormEvent } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

/* ================================================================
   Tipos
   ================================================================ */
interface PrazoVencidoItem {
  pcd_nivel_id: string;
  codigo: string;
  titulo: string;
  tipo: string;
  regra_id: string;
  evento_inicio: string;
  prazo_dias: number;
  fase_corrente: number;
  fase_intermediaria: number;
  destinacao_final: string;
  base_legal: string | null;
  regra_criada_em: string;
  tem_hold_ativo: boolean;
}

interface DashboardTemporalidade {
  total_regras: number;
  total_com_hold: number;
  por_destinacao: Record<string, number>;
  itens: PrazoVencidoItem[];
}

interface BuscaItem {
  id: string;
  pai_id: string | null;
  tipo: string;
  codigo: string;
  titulo: string;
  descricao: string | null;
  codigo_conarq: string | null;
  status: string;
  nivel_sigilo: string;
}

interface TermoEliminacao {
  titulo: string;
  data_geracao: string;
  gerado_por: string;
  itens: { codigo: string; titulo: string; tipo: string; destinacao_final: string; base_legal: string | null; fase_corrente: number; fase_intermediaria: number; observacoes: string | null }[];
  total_itens: number;
}

interface RelatorioTransferencia {
  titulo: string;
  tipo_relatorio: string;
  data_geracao: string;
  gerado_por: string;
  itens: { codigo: string; titulo: string; tipo: string; destinacao_final: string; fase_corrente: number; fase_intermediaria: number; base_legal: string | null }[];
  total_itens: number;
}

interface ImportResult {
  criados: number;
  erros: string[];
}

const LABEL_TIPO: Record<string, string> = {
  funcao: "Função",
  subfuncao: "Subfunção",
  atividade: "Atividade",
  serie: "Série",
  classe: "Classe",
  tipo_documental: "Tipo Documental",
};

const LABEL_DEST: Record<string, string> = {
  eliminacao: "Eliminação",
  guarda_permanente: "Guarda Permanente",
  microfilmagem: "Microfilmagem",
  amostragem: "Amostragem",
};

/* ================================================================
   Componente principal
   ================================================================ */
export default function RelatoriosPage() {
  // === Dashboard temporalidade ===
  const [dashboard, setDashboard] = useState<DashboardTemporalidade | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  // === Busca avançada ===
  const [buscaQ, setBuscaQ] = useState("");
  const [buscaTipo, setBuscaTipo] = useState("");
  const [buscaSigilo, setBuscaSigilo] = useState("");
  const [buscaStatus, setBuscaStatus] = useState("");
  const [buscaDest, setBuscaDest] = useState("");
  const [resultadoBusca, setResultadoBusca] = useState<BuscaItem[]>([]);
  const [buscando, setBuscando] = useState(false);

  // === Termo eliminação ===
  const [termoElim, setTermoElim] = useState<TermoEliminacao | null>(null);

  // === Relatório transferência ===
  const [relTransf, setRelTransf] = useState<RelatorioTransferencia | null>(null);
  const [tipoTransf, setTipoTransf] = useState("transferencia");

  // === Importação ===
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importando, setImportando] = useState(false);

  // === Erros ===
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // ─── Dashboard ───
  const carregarDashboard = useCallback(async () => {
    setLoadingDashboard(true);
    try {
      const { data } = await api.get<DashboardTemporalidade>("/relatorios/dashboard-temporalidade");
      setDashboard(data);
    } catch {
      setErrorMessage("Erro ao carregar dashboard de temporalidade.");
    } finally {
      setLoadingDashboard(false);
    }
  }, []);

  useEffect(() => {
    carregarDashboard();
  }, [carregarDashboard]);

  // ─── Busca ───
  async function handleBuscar(e: FormEvent) {
    e.preventDefault();
    setBuscando(true);
    setErrorMessage(null);
    try {
      const params = new URLSearchParams();
      if (buscaQ) params.set("q", buscaQ);
      if (buscaTipo) params.set("tipo", buscaTipo);
      if (buscaSigilo) params.set("nivel_sigilo", buscaSigilo);
      if (buscaStatus) params.set("status", buscaStatus);
      if (buscaDest) params.set("destinacao_final", buscaDest);
      const { data } = await api.get<BuscaItem[]>(`/relatorios/busca?${params.toString()}`);
      setResultadoBusca(data);
    } catch {
      setErrorMessage("Erro na busca.");
    } finally {
      setBuscando(false);
    }
  }

  // ─── Exportações ───
  async function handleDownload(endpoint: string, filename: string) {
    try {
      const { data } = await api.get(endpoint, { responseType: "blob" });
      const url = URL.createObjectURL(data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setErrorMessage(`Erro ao exportar ${filename}`);
    }
  }

  // ─── Termo eliminação ───
  async function carregarTermoEliminacao() {
    try {
      const { data } = await api.get<TermoEliminacao>("/relatorios/termo-eliminacao");
      setTermoElim(data);
    } catch {
      setErrorMessage("Erro ao carregar termo de eliminação.");
    }
  }

  // ─── Relatório transferência ───
  async function carregarRelTransferencia() {
    try {
      const { data } = await api.get<RelatorioTransferencia>(`/relatorios/relatorio-transferencia?tipo=${tipoTransf}`);
      setRelTransf(data);
    } catch {
      setErrorMessage("Erro ao carregar relatório de transferência.");
    }
  }

  // ─── Importação ───
  async function handleImportar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setImportando(true);
    setImportResult(null);
    setErrorMessage(null);
    const formData = new FormData(e.currentTarget);
    try {
      const { data } = await api.post<ImportResult>("/relatorios/importar/excel", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportResult(data);
    } catch {
      setErrorMessage("Erro na importação.");
    } finally {
      setImportando(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Relatórios, Exportação e Importação</h1>

      {errorMessage && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {errorMessage}
        </div>
      )}

      {/* ============================================================
          DASHBOARD DE TEMPORALIDADE (HU-035)
          ============================================================ */}
      <Card>
        <CardHeader>
          <CardTitle>Dashboard de Temporalidade</CardTitle>
          <CardDescription>Visão geral das regras de retenção e prazos (HU-035)</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingDashboard ? (
            <p className="text-muted-foreground text-sm">Carregando...</p>
          ) : dashboard ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">{dashboard.total_regras}</p>
                  <p className="text-xs text-muted-foreground">Total de Regras</p>
                </div>
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold text-yellow-600">{dashboard.total_com_hold}</p>
                  <p className="text-xs text-muted-foreground">Com Hold Ativo</p>
                </div>
                {Object.entries(dashboard.por_destinacao).map(([dest, count]) => (
                  <div key={dest} className="rounded-lg border p-3 text-center">
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-xs text-muted-foreground">{LABEL_DEST[dest] ?? dest}</p>
                  </div>
                ))}
              </div>

              {dashboard.itens.length > 0 && (
                <div className="max-h-80 overflow-auto rounded border">
                  <table className="w-full text-xs">
                    <thead className="bg-muted sticky top-0">
                      <tr>
                        <th className="p-2 text-left">Código</th>
                        <th className="p-2 text-left">Título</th>
                        <th className="p-2">Tipo</th>
                        <th className="p-2">Corrente</th>
                        <th className="p-2">Intermed.</th>
                        <th className="p-2">Destinação</th>
                        <th className="p-2">Hold</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.itens.map((item) => (
                        <tr key={item.regra_id} className={item.tem_hold_ativo ? "bg-yellow-50" : ""}>
                          <td className="p-2 font-mono">{item.codigo}</td>
                          <td className="p-2">{item.titulo}</td>
                          <td className="p-2 text-center">{LABEL_TIPO[item.tipo] ?? item.tipo}</td>
                          <td className="p-2 text-center">{item.fase_corrente}a</td>
                          <td className="p-2 text-center">{item.fase_intermediaria}a</td>
                          <td className="p-2 text-center">{LABEL_DEST[item.destinacao_final] ?? item.destinacao_final}</td>
                          <td className="p-2 text-center">{item.tem_hold_ativo ? "⚠️" : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* ============================================================
          EXPORTAÇÃO (HU-032 / HU-033)
          ============================================================ */}
      <Card>
        <CardHeader>
          <CardTitle>Exportação CCD / TTD</CardTitle>
          <CardDescription>Exportar a estrutura completa em diferentes formatos (HU-032, HU-033)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => handleDownload("/relatorios/exportar/pdf", "CCD_TTD_Completo.pdf")}>
              Exportar PDF
            </Button>
            <Button variant="outline" onClick={() => handleDownload("/relatorios/exportar/csv", "CCD_TTD_Completo.csv")}>
              Exportar CSV
            </Button>
            <Button variant="outline" onClick={() => handleDownload("/relatorios/exportar/excel", "CCD_TTD_Completo.xlsx")}>
              Exportar Excel
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ============================================================
          IMPORTAÇÃO EM LOTE (HU-034)
          ============================================================ */}
      <Card>
        <CardHeader>
          <CardTitle>Importação em Lote</CardTitle>
          <CardDescription>
            Importar níveis PCD e regras TTD a partir de planilha Excel (HU-034).
            Colunas: Código | Código CONARQ | Tipo | Título | Descrição | Sigilo | Código Pai |
            Evento Início | Fase Corrente | Fase Intermediária | Destinação Final | Base Legal |
            Legislação Ref | Observações
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleImportar} className="space-y-3">
            <input type="file" name="file" accept=".xlsx,.xls" required className="text-sm" />
            <Button type="submit" disabled={importando}>
              {importando ? "Importando..." : "Importar Excel"}
            </Button>
          </form>
          {importResult && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium text-green-700">
                ✅ {importResult.criados} nível(is) criado(s) com sucesso.
              </p>
              {importResult.erros.length > 0 && (
                <div className="rounded border border-yellow-300 bg-yellow-50 p-3">
                  <p className="text-sm font-medium text-yellow-800">Avisos ({importResult.erros.length}):</p>
                  <ul className="list-disc pl-5 text-xs text-yellow-700">
                    {importResult.erros.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ============================================================
          BUSCA AVANÇADA (HU-036)
          ============================================================ */}
      <Card>
        <CardHeader>
          <CardTitle>Busca Avançada no PCD</CardTitle>
          <CardDescription>Pesquise por código, título, tipo, sigilo, status ou destinação (HU-036)</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleBuscar} className="space-y-3">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <input
                value={buscaQ}
                onChange={(e) => setBuscaQ(e.target.value)}
                placeholder="Texto livre..."
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
              <select
                value={buscaTipo}
                onChange={(e) => setBuscaTipo(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos os tipos</option>
                <option value="funcao">Função</option>
                <option value="subfuncao">Subfunção</option>
                <option value="atividade">Atividade</option>
                <option value="serie">Série</option>
                <option value="classe">Classe</option>
                <option value="tipo_documental">Tipo Documental</option>
              </select>
              <select
                value={buscaSigilo}
                onChange={(e) => setBuscaSigilo(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos os sigilos</option>
                <option value="publico">Público</option>
                <option value="restrito">Restrito</option>
                <option value="confidencial">Confidencial</option>
                <option value="secreto">Secreto</option>
              </select>
              <select
                value={buscaStatus}
                onChange={(e) => setBuscaStatus(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos os status</option>
                <option value="rascunho">Rascunho</option>
                <option value="ativo">Ativo</option>
                <option value="arquivado">Arquivado</option>
              </select>
              <select
                value={buscaDest}
                onChange={(e) => setBuscaDest(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todas destinações</option>
                <option value="eliminacao">Eliminação</option>
                <option value="guarda_permanente">Guarda Permanente</option>
                <option value="microfilmagem">Microfilmagem</option>
                <option value="amostragem">Amostragem</option>
              </select>
              <Button type="submit" disabled={buscando} className="w-full">
                {buscando ? "Buscando..." : "Buscar"}
              </Button>
            </div>
          </form>

          {resultadoBusca.length > 0 && (
            <div className="mt-4 max-h-60 overflow-auto rounded border">
              <table className="w-full text-xs">
                <thead className="bg-muted sticky top-0">
                  <tr>
                    <th className="p-2 text-left">Código</th>
                    <th className="p-2 text-left">Título</th>
                    <th className="p-2">Tipo</th>
                    <th className="p-2">CONARQ</th>
                    <th className="p-2">Sigilo</th>
                    <th className="p-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {resultadoBusca.map((item) => (
                    <tr key={item.id}>
                      <td className="p-2 font-mono">{item.codigo}</td>
                      <td className="p-2">{item.titulo}</td>
                      <td className="p-2 text-center">{LABEL_TIPO[item.tipo] ?? item.tipo}</td>
                      <td className="p-2 text-center">{item.codigo_conarq || "—"}</td>
                      <td className="p-2 text-center">{item.nivel_sigilo}</td>
                      <td className="p-2 text-center">{item.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ============================================================
          TERMO DE ELIMINAÇÃO (HU-037)
          ============================================================ */}
      <Card>
        <CardHeader>
          <CardTitle>Listagem de Eliminação</CardTitle>
          <CardDescription>Documentos com destinação &quot;eliminação&quot; e sem hold ativo (HU-037)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={carregarTermoEliminacao}>
              Gerar Listagem
            </Button>
            <Button onClick={() => handleDownload("/relatorios/termo-eliminacao/pdf", "Termo_Eliminacao.pdf")}>
              Baixar PDF
            </Button>
          </div>
          {termoElim && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium">{termoElim.titulo} — {termoElim.total_itens} item(ns)</p>
              <div className="max-h-60 overflow-auto rounded border">
                <table className="w-full text-xs">
                  <thead className="bg-muted sticky top-0">
                    <tr>
                      <th className="p-2 text-left">Código</th>
                      <th className="p-2 text-left">Título</th>
                      <th className="p-2">Tipo</th>
                      <th className="p-2">Corrente</th>
                      <th className="p-2">Intermed.</th>
                      <th className="p-2 text-left">Base Legal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {termoElim.itens.map((item, i) => (
                      <tr key={i}>
                        <td className="p-2 font-mono">{item.codigo}</td>
                        <td className="p-2">{item.titulo}</td>
                        <td className="p-2 text-center">{LABEL_TIPO[item.tipo] ?? item.tipo}</td>
                        <td className="p-2 text-center">{item.fase_corrente}a</td>
                        <td className="p-2 text-center">{item.fase_intermediaria}a</td>
                        <td className="p-2">{item.base_legal || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ============================================================
          RELATÓRIO TRANSFERÊNCIA / RECOLHIMENTO (HU-038)
          ============================================================ */}
      <Card>
        <CardHeader>
          <CardTitle>Relatório de Transferência / Recolhimento</CardTitle>
          <CardDescription>Documentos com guarda permanente sem hold ativo (HU-038)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={tipoTransf}
              onChange={(e) => setTipoTransf(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="transferencia">Transferência</option>
              <option value="recolhimento">Recolhimento</option>
            </select>
            <Button variant="outline" onClick={carregarRelTransferencia}>
              Gerar Relatório
            </Button>
            <Button onClick={() => handleDownload(`/relatorios/relatorio-transferencia/pdf?tipo=${tipoTransf}`, `Relatorio_${tipoTransf}.pdf`)}>
              Baixar PDF
            </Button>
          </div>
          {relTransf && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium">{relTransf.titulo} — {relTransf.total_itens} item(ns)</p>
              <div className="max-h-60 overflow-auto rounded border">
                <table className="w-full text-xs">
                  <thead className="bg-muted sticky top-0">
                    <tr>
                      <th className="p-2 text-left">Código</th>
                      <th className="p-2 text-left">Título</th>
                      <th className="p-2">Tipo</th>
                      <th className="p-2">Corrente</th>
                      <th className="p-2">Intermed.</th>
                      <th className="p-2 text-left">Base Legal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {relTransf.itens.map((item, i) => (
                      <tr key={i}>
                        <td className="p-2 font-mono">{item.codigo}</td>
                        <td className="p-2">{item.titulo}</td>
                        <td className="p-2 text-center">{LABEL_TIPO[item.tipo] ?? item.tipo}</td>
                        <td className="p-2 text-center">{item.fase_corrente}a</td>
                        <td className="p-2 text-center">{item.fase_intermediaria}a</td>
                        <td className="p-2">{item.base_legal || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
