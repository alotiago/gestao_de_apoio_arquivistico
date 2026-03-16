"use client";

import { useState } from "react";
import api from "@/lib/api";
import { useJobs, useWorkflows } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type WorkflowItem = {
  id: string;
  tipo: string;
  estado: string;
  item_id: string;
  item_tipo: string;
  sla_horas: number;
  comentario: string | null;
  created_at: string;
};

type JobItem = {
  id: string;
  janela_inicio: string;
  janela_fim: string;
  status: string;
  total_analisados: number;
  total_ordens: number;
  idempotency_key: string;
  completed_at?: string | null;
  log_execucao?: {
    execucoes?: Array<{
      status: string;
      mensagem: string;
      timestamp: string;
    }>;
  };
};

type PacoteAuditoria = {
  gerado_em: string;
  gerado_por: string;
  resumo: {
    selos: number;
    workflows: number;
    jobs: number;
    ordens: number;
  };
};

function getNextStates(estado: string): string[] {
  if (estado === "pendente") {
    return ["em_avaliacao"];
  }
  if (estado === "em_avaliacao") {
    return ["aprovado", "rejeitado"];
  }
  if (estado === "aprovado") {
    return ["executado"];
  }
  if (estado === "rejeitado") {
    return ["pendente"];
  }
  return [];
}

export default function CicloVidaPage() {
  const [estadoFiltro, setEstadoFiltro] = useState("");
  const [statusJobFiltro, setStatusJobFiltro] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transicaoLoadingId, setTransicaoLoadingId] = useState<string | null>(null);
  const [jobLoadingId, setJobLoadingId] = useState<string | null>(null);
  const [agendarLoading, setAgendarLoading] = useState(false);
  const [comentario, setComentario] = useState<Record<string, string>>({});
  const [janelaInicio, setJanelaInicio] = useState("");
  const [janelaFim, setJanelaFim] = useState("");
  const [seloEntidade, setSeloEntidade] = useState("job_retencao");
  const [seloEntidadeId, setSeloEntidadeId] = useState("");
  const [seloRazao, setSeloRazao] = useState("");
  const [seloHashGerado, setSeloHashGerado] = useState<string | null>(null);
  const [pacoteAuditoria, setPacoteAuditoria] = useState<PacoteAuditoria | null>(null);
  const [seloLoading, setSeloLoading] = useState(false);
  const [pacoteLoading, setPacoteLoading] = useState(false);

  const {
    data: workflowsRaw,
    mutate: mutateWorkflows,
    isLoading: loadingWorkflows,
  } = useWorkflows(estadoFiltro || undefined);
  const workflows = (workflowsRaw as WorkflowItem[] | undefined) ?? [];

  const {
    data: jobsRaw,
    isLoading: loadingJobs,
    mutate: mutateJobs,
  } = useJobs(statusJobFiltro || undefined);
  const jobs = (jobsRaw as JobItem[] | undefined) ?? [];

  async function handleAgendarJob() {
    setErrorMessage(null);
    if (!janelaInicio || !janelaFim) {
      setErrorMessage("Informe início e fim da janela para agendar o job.");
      return;
    }

    setAgendarLoading(true);
    try {
      await api.post("/ciclo-vida/jobs", {
        janela_inicio: new Date(janelaInicio).toISOString(),
        janela_fim: new Date(janelaFim).toISOString(),
      });
      await mutateJobs();
    } catch {
      setErrorMessage("Falha ao agendar job de retenção.");
    } finally {
      setAgendarLoading(false);
    }
  }

  async function handleExecutarJob(jobId: string) {
    setErrorMessage(null);
    setJobLoadingId(jobId);
    try {
      await api.post(`/ciclo-vida/jobs/${jobId}/executar`);
      await mutateJobs();
    } catch {
      setErrorMessage("Falha ao executar/reprocessar job de retenção.");
    } finally {
      setJobLoadingId(null);
    }
  }

  async function handleTransicao(tarefaId: string, novoEstado: string) {
    setErrorMessage(null);
    setTransicaoLoadingId(tarefaId);
    try {
      await api.patch(`/ciclo-vida/workflows/${tarefaId}/transicao`, {
        novo_estado: novoEstado,
        comentario: comentario[tarefaId] || null,
      });
      await mutateWorkflows();
    } catch {
      setErrorMessage("Falha ao transicionar workflow.");
    } finally {
      setTransicaoLoadingId(null);
    }
  }

  async function handleGerarSelo() {
    setErrorMessage(null);
    if (!seloEntidadeId || !seloRazao.trim()) {
      setErrorMessage("Informe entidade, ID e razão para gerar o selo de evidência.");
      return;
    }

    setSeloLoading(true);
    try {
      const response = await api.post("/ciclo-vida/selos", {
        entidade: seloEntidade,
        entidade_id: seloEntidadeId,
        razao: seloRazao,
        contexto: { origem: "dashboard_ciclo_vida" },
      });
      setSeloHashGerado(response.data.hash_selo);
    } catch {
      setErrorMessage("Falha ao gerar selo de evidência.");
    } finally {
      setSeloLoading(false);
    }
  }

  async function handleConsultarPacote() {
    setErrorMessage(null);
    setPacoteLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("entidade", seloEntidade);
      if (seloEntidadeId) {
        params.set("entidade_id", seloEntidadeId);
      }
      const response = await api.get(`/ciclo-vida/auditoria/pacote?${params.toString()}`);
      setPacoteAuditoria(response.data as PacoteAuditoria);
    } catch {
      setErrorMessage("Falha ao consultar pacote de auditoria.");
    } finally {
      setPacoteLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Ciclo de Vida</h1>
        <p className="text-muted-foreground">
          Sprint 7 (US-030/US-031/US-032): jobs, workflows e trilha de evidências
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
            <CardTitle>Workflows</CardTitle>
            <CardDescription>
              {loadingWorkflows ? "Carregando workflows..." : `${workflows.length} tarefa(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <select
              value={estadoFiltro}
              onChange={(event) => setEstadoFiltro(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Todos os estados</option>
              <option value="pendente">Pendente</option>
              <option value="em_avaliacao">Em Avaliação</option>
              <option value="aprovado">Aprovado</option>
              <option value="rejeitado">Rejeitado</option>
              <option value="executado">Executado</option>
            </select>

            {workflows.map((workflow) => {
              const nextStates = getNextStates(workflow.estado);
              return (
                <div key={workflow.id} className="rounded-md border border-border p-3">
                  <p className="text-sm font-medium text-foreground">
                    [{workflow.tipo}] {workflow.item_tipo}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Estado: {workflow.estado} · SLA: {workflow.sla_horas}h
                  </p>

                  {nextStates.length > 0 ? (
                    <div className="mt-2 space-y-2">
                      <input
                        value={comentario[workflow.id] ?? ""}
                        onChange={(event) =>
                          setComentario((prev) => ({
                            ...prev,
                            [workflow.id]: event.target.value,
                          }))
                        }
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        placeholder="Comentário da transição (opcional)"
                      />
                      <div className="flex flex-wrap gap-2">
                        {nextStates.map((estado) => (
                          <Button
                            key={estado}
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => handleTransicao(workflow.id, estado)}
                            disabled={transicaoLoadingId === workflow.id}
                          >
                            {transicaoLoadingId === workflow.id
                              ? "Salvando..."
                              : `Ir para ${estado}`}
                          </Button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Jobs de Retenção</CardTitle>
            <CardDescription>
              {loadingJobs ? "Carregando jobs..." : `${jobs.length} job(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <input
                type="datetime-local"
                value={janelaInicio}
                onChange={(event) => setJanelaInicio(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
              <input
                type="datetime-local"
                value={janelaFim}
                onChange={(event) => setJanelaFim(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                size="sm"
                onClick={handleAgendarJob}
                disabled={agendarLoading}
              >
                {agendarLoading ? "Agendando..." : "Agendar Job"}
              </Button>

              <select
                value={statusJobFiltro}
                onChange={(event) => setStatusJobFiltro(event.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos os status</option>
                <option value="agendado">Agendado</option>
                <option value="executando">Executando</option>
                <option value="concluido">Concluído</option>
                <option value="falha">Falha</option>
              </select>
            </div>

            {jobs.map((job) => (
              <div key={job.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">Job {job.id.slice(0, 8)}</p>
                <p className="text-xs text-muted-foreground">
                  Status: {job.status} · Analisados: {job.total_analisados} · Ordens: {job.total_ordens}
                </p>
                <p className="text-xs text-muted-foreground">
                  Janela: {new Date(job.janela_inicio).toLocaleString("pt-BR")} → {" "}
                  {new Date(job.janela_fim).toLocaleString("pt-BR")}
                </p>
                <p className="text-xs text-muted-foreground">
                  Execuções: {job.log_execucao?.execucoes?.length ?? 0}
                </p>

                <div className="mt-2 flex flex-wrap gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => handleExecutarJob(job.id)}
                    disabled={jobLoadingId === job.id}
                  >
                    {jobLoadingId === job.id
                      ? "Processando..."
                      : job.status === "concluido"
                        ? "Reprocessar (idempotente)"
                        : "Executar"}
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Selo de Evidência e Pacote de Auditoria</CardTitle>
          <CardDescription>
            Geração de selo (hash + timestamp + usuário + razão) e consulta JSON da trilha
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-2 lg:grid-cols-3">
            <select
              value={seloEntidade}
              onChange={(event) => setSeloEntidade(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="job_retencao">Job de Retenção</option>
              <option value="workflow_tarefa">Workflow</option>
              <option value="ordem_destinacao">Ordem de Destinação</option>
            </select>

            <input
              value={seloEntidadeId}
              onChange={(event) => setSeloEntidadeId(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="ID da entidade (UUID)"
            />

            <input
              value={seloRazao}
              onChange={(event) => setSeloRazao(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Razão do selo"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" size="sm" onClick={handleGerarSelo} disabled={seloLoading}>
              {seloLoading ? "Gerando selo..." : "Gerar Selo"}
            </Button>
            <Button type="button" size="sm" variant="outline" onClick={handleConsultarPacote} disabled={pacoteLoading}>
              {pacoteLoading ? "Consultando..." : "Consultar Pacote"}
            </Button>
          </div>

          {seloHashGerado ? (
            <p className="text-xs text-muted-foreground">Hash do selo gerado: {seloHashGerado.slice(0, 24)}...</p>
          ) : null}

          {pacoteAuditoria ? (
            <pre className="max-h-64 overflow-auto rounded-md border border-border bg-muted p-3 text-xs text-foreground">
              {JSON.stringify(pacoteAuditoria, null, 2)}
            </pre>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
