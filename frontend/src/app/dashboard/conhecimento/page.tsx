"use client";

import { useMemo, useState } from "react";
import api from "@/lib/api";
import { useTemplatesConhecimento, useTrilhasConhecimento } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type TemplateConhecimento = {
  slug: string;
  titulo: string;
  categoria: string;
  descricao: string;
  tags: string[];
};

type TemplateDownload = {
  nome_arquivo: string;
  conteudo: string;
};

type TrilhaConhecimento = {
  id: string;
  nome: string;
  perfil: string;
  duracao_estimada_min: number;
  etapas: string[];
  etapas_concluidas: number;
  progresso_percentual: number;
  badge_emitido: boolean;
};

export default function ConhecimentoPage() {
  const [query, setQuery] = useState("Termo de eliminação");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const { data: templatesRaw, mutate: mutateTemplates } = useTemplatesConhecimento(query);
  const { data: trilhasRaw, mutate: mutateTrilhas } = useTrilhasConhecimento();

  const templates = useMemo(
    () => (templatesRaw as TemplateConhecimento[] | undefined) ?? [],
    [templatesRaw]
  );
  const trilhas = useMemo(
    () => (trilhasRaw as TrilhaConhecimento[] | undefined) ?? [],
    [trilhasRaw]
  );

  async function handleDownload(slug: string, tipo: "template" | "guia") {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`${tipo}-${slug}`);
    try {
      const { data } = await api.get<TemplateDownload>(`/conhecimento/templates/${slug}/download?tipo=${tipo}`);
      const blob = new Blob([data.conteudo], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = data.nome_arquivo;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
      setSuccessMessage(`Download iniciado: ${data.nome_arquivo}`);
    } catch {
      setErrorMessage("Falha ao baixar o material solicitado.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleAtualizarProgresso(trilha: TrilhaConhecimento) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`trilha-${trilha.id}`);
    try {
      const proximasEtapas = Math.min(trilha.etapas_concluidas + 1, trilha.etapas.length);
      await api.post(`/conhecimento/trilhas/${trilha.id}/progresso`, {
        etapas_concluidas: proximasEtapas,
      });
      await mutateTrilhas();
      setSuccessMessage(`Progresso atualizado para a trilha ${trilha.nome}.`);
    } catch {
      setErrorMessage("Falha ao atualizar progresso da trilha.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleBuscar() {
    setErrorMessage(null);
    setSuccessMessage(null);
    await mutateTemplates();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Base de Conhecimento</h1>
        <p className="text-muted-foreground">
          EP10 (US-091): templates oficiais, guias rápidos e trilhas de onboarding interno
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
          <CardTitle>Buscar templates oficiais</CardTitle>
          <CardDescription>
            Pesquise por termos como “Termo de eliminação”, PCD ou implantação para baixar o material padrão.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col gap-3 md:flex-row">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Buscar template ou guia"
            />
            <Button type="button" onClick={handleBuscar}>
              Buscar
            </Button>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {templates.map((template) => (
              <div key={template.slug} className="rounded-xl border border-border p-4 shadow-sm">
                <p className="text-sm font-semibold text-foreground">{template.titulo}</p>
                <p className="text-xs text-muted-foreground">
                  {template.categoria} · {template.tags.join(", ")}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">{template.descricao}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleDownload(template.slug, "template")}
                    disabled={loadingAction !== null}
                  >
                    {loadingAction === `template-${template.slug}` ? "Baixando..." : "Baixar template"}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => handleDownload(template.slug, "guia")}
                    disabled={loadingAction !== null}
                  >
                    {loadingAction === `guia-${template.slug}` ? "Baixando..." : "Baixar guia"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trilhas de onboarding</CardTitle>
          <CardDescription>
            Atualize a evolução por perfil e libere badge interno ao concluir a trilha.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-3">
          {trilhas.map((trilha) => (
            <div key={trilha.id} className="rounded-xl border border-border p-4 shadow-sm">
              <p className="text-sm font-semibold text-foreground">{trilha.nome}</p>
              <p className="text-xs text-muted-foreground">
                {trilha.perfil} · {trilha.duracao_estimada_min} min
              </p>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary"
                  style={{ width: `${trilha.progresso_percentual}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {trilha.etapas_concluidas}/{trilha.etapas.length} etapas · {trilha.progresso_percentual}%
              </p>
              <div className="mt-3 space-y-1">
                {trilha.etapas.map((etapa, index) => (
                  <p key={etapa} className="text-xs text-muted-foreground">
                    {index + 1}. {etapa}
                  </p>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => handleAtualizarProgresso(trilha)}
                  disabled={loadingAction !== null || trilha.badge_emitido}
                >
                  {loadingAction === `trilha-${trilha.id}` ? "Atualizando..." : "Concluir próxima etapa"}
                </Button>
                {trilha.badge_emitido ? (
                  <span className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs text-primary">
                    Badge emitido
                  </span>
                ) : null}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
