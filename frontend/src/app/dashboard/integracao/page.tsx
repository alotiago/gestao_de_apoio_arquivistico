"use client";

import { useState } from "react";
import api from "@/lib/api";
import { useImportacoesAcervo } from "@/hooks/use-api";
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
  resultados: Array<{
    linha: number;
    status: string;
    codigo?: string;
    titulo?: string;
    classe_codigo?: string;
    erros?: string[];
  }>;
  created_at: string;
};

const defaultMapping = {
  codigo: "codigo_doc",
  titulo: "titulo_doc",
  classe_codigo: "classe_ref",
  descricao: "descricao_doc",
};

export default function IntegracaoPage() {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [mappingJson, setMappingJson] = useState(JSON.stringify(defaultMapping, null, 2));
  const [statusFiltro, setStatusFiltro] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const {
    data: importacoesRaw,
    isLoading,
    mutate,
  } = useImportacoesAcervo(statusFiltro || undefined);
  const importacoes = (importacoesRaw as ImportacaoItem[] | undefined) ?? [];

  async function handleImportar() {
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!arquivo) {
      setErrorMessage("Selecione um arquivo CSV para importar.");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("arquivo", arquivo);
      formData.append("mapping_json", mappingJson);

      const response = await api.post("/integracao/importacoes", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const body = response.data as ImportacaoItem;
      setSuccessMessage(
        `Importação concluída: ${body.total_sucesso} sucesso(s), ${body.total_erros} erro(s).`
      );
      await mutate();
    } catch {
      setErrorMessage("Falha ao importar acervo CSV.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Integração</h1>
        <p className="text-muted-foreground">
          EP6 (US-052): importação interna de acervo com mapeamento e validação
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

      <Card>
        <CardHeader>
          <CardTitle>Importar inventário CSV</CardTitle>
          <CardDescription>
            Envie o arquivo e informe o mapeamento das colunas para os campos internos.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            type="file"
            accept=".csv"
            onChange={(event) => setArquivo(event.target.files?.[0] ?? null)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <textarea
            value={mappingJson}
            onChange={(event) => setMappingJson(event.target.value)}
            rows={8}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
          />
          <Button type="button" onClick={handleImportar} disabled={uploading}>
            {uploading ? "Importando..." : "Importar Acervo"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Histórico de Importações</CardTitle>
          <CardDescription>
            {isLoading ? "Carregando importações..." : `${importacoes.length} importação(ões)`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <select
            value={statusFiltro}
            onChange={(event) => setStatusFiltro(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Todos os status</option>
            <option value="processado">Processado</option>
            <option value="concluido_com_erros">Concluído com erros</option>
            <option value="falha">Falha</option>
          </select>

          {importacoes.map((item) => (
            <div key={item.id} className="rounded-md border border-border p-3">
              <p className="text-sm font-medium text-foreground">{item.nome_arquivo}</p>
              <p className="text-xs text-muted-foreground">
                Status: {item.status} · Registros: {item.total_registros} · Sucessos: {item.total_sucesso} · Erros: {item.total_erros}
              </p>
              <p className="text-xs text-muted-foreground">
                Processado em {new Date(item.created_at).toLocaleString("pt-BR")}
              </p>

              <div className="mt-2 space-y-2">
                {item.resultados.slice(0, 5).map((resultado) => (
                  <div key={`${item.id}-${resultado.linha}`} className="rounded border border-border/60 p-2">
                    <p className="text-xs font-medium text-foreground">
                      Linha {resultado.linha} · {resultado.status}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {resultado.codigo ?? "—"} · {resultado.titulo ?? "—"} · {resultado.classe_codigo ?? "—"}
                    </p>
                    {resultado.erros?.length ? (
                      <p className="text-xs text-destructive">{resultado.erros.join(", ")}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
