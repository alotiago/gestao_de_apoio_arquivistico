"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
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
  pai_id: string | null;
  tipo: string;
  codigo: string;
  titulo: string;
  descricao: string | null;
  codigo_conarq: string | null;
  versao: number;
  status: string;
  nivel_sigilo: string;
  metadados: Record<string, unknown>;
  filhos: PcdNivel[];
};

type PcdVersao = {
  id: string;
  pcd_nivel_id: string;
  versao: number;
  dados_snapshot: Record<string, unknown>;
  justificativa: string;
  status: string;
  created_at: string;
};

type DiffItem = {
  campo: string;
  valorA: string;
  valorB: string;
};

type ControleSeguranca = {
  pcd_nivel_id: string;
  metadados_obrigatorios: string[];
  permissoes_por_papel: Record<string, string[]>;
  unidades_autorizadas: string[];
};

type ValidacaoMetadados = {
  pcd_nivel_id: string;
  valido: boolean;
  faltantes: string[];
};

type ValidacaoAcesso = {
  pcd_nivel_id: string;
  permitido: boolean;
  acao: string;
  papel: string;
  unidade_usuario: string | null;
  nivel_sigilo: string;
  motivos: string[];
};

function flattenNiveis(niveis: PcdNivel[]): PcdNivel[] {
  const queue = [...niveis];
  const all: PcdNivel[] = [];
  while (queue.length > 0) {
    const current = queue.shift();
    if (!current) {
      continue;
    }
    all.push(current);
    queue.push(...current.filhos);
  }
  return all;
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

function renderNivelTree(
  nivel: PcdNivel,
  selectedId: string | null,
  onSelect: (nivelId: string) => void,
  depth = 0
): JSX.Element {
  const isSelected = selectedId === nivel.id;

  return (
    <div key={nivel.id} className={depth > 0 ? "ml-4 border-l border-border pl-3" : ""}>
      <button
        type="button"
        onClick={() => onSelect(nivel.id)}
        className={`w-full rounded-md border p-2 text-left ${
          isSelected
            ? "border-primary bg-primary/10"
            : "border-border bg-background hover:bg-muted/40"
        }`}
      >
        <p className="text-sm font-medium text-foreground">
          [{nivel.tipo}] {nivel.codigo} · {nivel.titulo}
        </p>
        <p className="text-xs text-muted-foreground">
          Versão {nivel.versao} · Status {nivel.status} · Sigilo {nivel.nivel_sigilo}
        </p>
      </button>
      {nivel.filhos.length > 0 ? (
        <div className="mt-2 space-y-2">
          {nivel.filhos.map((filho) => renderNivelTree(filho, selectedId, onSelect, depth + 1))}
        </div>
      ) : null}
    </div>
  );
}

export default function PcdPage() {
  const [niveisRaiz, setNiveisRaiz] = useState<PcdNivel[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedNivelId, setSelectedNivelId] = useState<string | null>(null);

  const [paiId, setPaiId] = useState("");
  const [tipo, setTipo] = useState("funcao");
  const [codigo, setCodigo] = useState("");
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [codigoConarq, setCodigoConarq] = useState("");
  const [nivelSigilo, setNivelSigilo] = useState("publico");

  const [editTitulo, setEditTitulo] = useState("");
  const [editDescricao, setEditDescricao] = useState("");
  const [editCodigoConarq, setEditCodigoConarq] = useState("");
  const [editNivelSigilo, setEditNivelSigilo] = useState("publico");
  const [editStatus, setEditStatus] = useState("rascunho");
  const [editMetadados, setEditMetadados] = useState("{}");
  const [savingEdit, setSavingEdit] = useState(false);

  const [versoes, setVersoes] = useState<PcdVersao[]>([]);
  const [loadingVersoes, setLoadingVersoes] = useState(false);
  const [creatingVersao, setCreatingVersao] = useState(false);
  const [justificativaVersao, setJustificativaVersao] = useState("");
  const [updatingVersaoId, setUpdatingVersaoId] = useState<string | null>(null);
  const [compararVersaoA, setCompararVersaoA] = useState("");
  const [compararVersaoB, setCompararVersaoB] = useState("");

  const [controleMetadadosObrigatorios, setControleMetadadosObrigatorios] = useState("");
  const [controlePermissoesJson, setControlePermissoesJson] = useState("{}");
  const [controleUnidadesAutorizadas, setControleUnidadesAutorizadas] = useState("");
  const [salvandoControle, setSalvandoControle] = useState(false);
  const [metadadosParaValidarJson, setMetadadosParaValidarJson] = useState("{}");
  const [validandoMetadados, setValidandoMetadados] = useState(false);
  const [resultadoValidacao, setResultadoValidacao] = useState<ValidacaoMetadados | null>(null);
  const [acaoAcesso, setAcaoAcesso] = useState("ler");
  const [validandoAcesso, setValidandoAcesso] = useState(false);
  const [resultadoAcesso, setResultadoAcesso] = useState<ValidacaoAcesso | null>(null);

  const niveisDisponiveis = useMemo(() => flattenNiveis(niveisRaiz), [niveisRaiz]);
  const selectedNivel = useMemo(
    () => niveisDisponiveis.find((nivel) => nivel.id === selectedNivelId) ?? null,
    [niveisDisponiveis, selectedNivelId]
  );
  const selectedNivelEhClasse = selectedNivel?.tipo === "classe";

  const handleSelecionarNivel = useCallback((nivelId: string) => {
    setSelectedNivelId(nivelId);
  }, []);

  const arvoreNiveisRenderizada = useMemo(
    () =>
      niveisRaiz.map((nivel) =>
        renderNivelTree(nivel, selectedNivelId, handleSelecionarNivel)
      ),
    [handleSelecionarNivel, niveisRaiz, selectedNivelId]
  );

  const versaoA = useMemo(
    () => versoes.find((item) => item.id === compararVersaoA) ?? null,
    [versoes, compararVersaoA]
  );
  const versaoB = useMemo(
    () => versoes.find((item) => item.id === compararVersaoB) ?? null,
    [versoes, compararVersaoB]
  );

  const diffVersoes = useMemo<DiffItem[]>(() => {
    if (!versaoA || !versaoB) {
      return [];
    }

    const campos = ["tipo", "codigo", "titulo", "descricao", "codigo_conarq", "metadados"];
    return campos
      .map((campo) => {
        const valorA = stringifyValue(versaoA.dados_snapshot[campo]);
        const valorB = stringifyValue(versaoB.dados_snapshot[campo]);
        return { campo, valorA, valorB };
      })
      .filter((item) => item.valorA !== item.valorB);
  }, [versaoA, versaoB]);

  const carregarArvore = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<PcdNivel[]>("/pcd/arvore");
      setNiveisRaiz(data);
    } catch {
      setErrorMessage("Não foi possível carregar a árvore do PCD.");
    } finally {
      setLoading(false);
    }
  }, []);

  const carregarVersoes = useCallback(async (nivelId: string) => {
    setLoadingVersoes(true);
    try {
      const { data } = await api.get<PcdVersao[]>(`/pcd/${nivelId}/versoes`);
      setVersoes(data);
      setCompararVersaoA((current) => current || data[0]?.id || "");
      setCompararVersaoB((current) => current || data[1]?.id || data[0]?.id || "");
    } catch {
      setErrorMessage("Não foi possível carregar o histórico de versões.");
      setVersoes([]);
      setCompararVersaoA("");
      setCompararVersaoB("");
    } finally {
      setLoadingVersoes(false);
    }
  }, []);

  const carregarControleSeguranca = useCallback(async (nivelId: string) => {
    try {
      const { data } = await api.get<ControleSeguranca>(`/pcd/${nivelId}/controle-seguranca`);
      setControleMetadadosObrigatorios(data.metadados_obrigatorios.join("\n"));
      setControlePermissoesJson(JSON.stringify(data.permissoes_por_papel, null, 2));
      setControleUnidadesAutorizadas(data.unidades_autorizadas.join("\n"));
    } catch {
      setControleMetadadosObrigatorios("");
      setControlePermissoesJson("{}");
      setControleUnidadesAutorizadas("");
      setErrorMessage("Não foi possível carregar o controle de metadados e permissões da classe.");
    }
  }, []);

  useEffect(() => {
    void carregarArvore();
  }, [carregarArvore]);

  useEffect(() => {
    if (!selectedNivelId) {
      setVersoes([]);
      setCompararVersaoA("");
      setCompararVersaoB("");
      return;
    }

    void carregarVersoes(selectedNivelId);
  }, [selectedNivelId, carregarVersoes]);

  useEffect(() => {
    if (!selectedNivel) {
      setEditTitulo("");
      setEditDescricao("");
      setEditCodigoConarq("");
      setEditNivelSigilo("publico");
      setEditStatus("rascunho");
      setEditMetadados("{}");
      setControleMetadadosObrigatorios("");
      setControlePermissoesJson("{}");
      setMetadadosParaValidarJson("{}");
      setResultadoValidacao(null);
      setControleUnidadesAutorizadas("");
      setResultadoAcesso(null);
      return;
    }

    setEditTitulo(selectedNivel.titulo);
    setEditDescricao(selectedNivel.descricao || "");
    setEditCodigoConarq(selectedNivel.codigo_conarq || "");
    setEditNivelSigilo(selectedNivel.nivel_sigilo);
    setEditStatus(selectedNivel.status);
    setEditMetadados(JSON.stringify(selectedNivel.metadados ?? {}, null, 2));
    setResultadoValidacao(null);
  }, [selectedNivel]);

  useEffect(() => {
    if (!selectedNivel || selectedNivel.tipo !== "classe") {
      setControleMetadadosObrigatorios("");
      setControlePermissoesJson("{}");
      setControleUnidadesAutorizadas("");
      return;
    }

    void carregarControleSeguranca(selectedNivel.id);
  }, [selectedNivel, carregarControleSeguranca]);

  async function handleCriarNivel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setCreating(true);
    try {
      await api.post("/pcd", {
        pai_id: paiId || null,
        tipo,
        codigo,
        titulo,
        descricao: descricao || null,
        codigo_conarq: codigoConarq || null,
        nivel_sigilo: nivelSigilo,
        metadados: {},
      });

      setPaiId("");
      setTipo("funcao");
      setCodigo("");
      setTitulo("");
      setDescricao("");
      setCodigoConarq("");
      setNivelSigilo("publico");

      await carregarArvore();
    } catch {
      setErrorMessage("Não foi possível criar o nível do PCD.");
    } finally {
      setCreating(false);
    }
  }

  async function handleSalvarEdicao(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedNivelId) {
      setErrorMessage("Selecione um nível da árvore para editar.");
      return;
    }

    let parsedMetadados: Record<string, unknown> = {};
    try {
      parsedMetadados = JSON.parse(editMetadados) as Record<string, unknown>;
    } catch {
      setErrorMessage("Metadados inválidos: informe um JSON válido.");
      return;
    }

    setErrorMessage(null);
    setSavingEdit(true);
    try {
      await api.patch(`/pcd/${selectedNivelId}`, {
        titulo: editTitulo,
        descricao: editDescricao || null,
        codigo_conarq: editCodigoConarq || null,
        nivel_sigilo: editNivelSigilo,
        status: editStatus,
        metadados: parsedMetadados,
      });

      await carregarArvore();
    } catch {
      setErrorMessage("Não foi possível salvar as alterações do nível selecionado.");
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleCriarVersao(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedNivelId) {
      setErrorMessage("Selecione um nível para versionar.");
      return;
    }
    if (!justificativaVersao.trim()) {
      setErrorMessage("Informe uma justificativa para criar a versão.");
      return;
    }

    setErrorMessage(null);
    setCreatingVersao(true);
    try {
      await api.post(`/pcd/${selectedNivelId}/versao`, {
        justificativa: justificativaVersao.trim(),
      });

      setJustificativaVersao("");
      await Promise.all([carregarArvore(), carregarVersoes(selectedNivelId)]);
    } catch {
      setErrorMessage("Não foi possível criar a versão do nível selecionado.");
    } finally {
      setCreatingVersao(false);
    }
  }

  async function handleAtualizarStatusVersao(versaoId: string, novoStatus: "aprovado" | "rejeitado") {
    if (!selectedNivelId) {
      setErrorMessage("Selecione um nível para atualizar a versão.");
      return;
    }

    setErrorMessage(null);
    setUpdatingVersaoId(versaoId);
    try {
      await api.patch(`/pcd/${selectedNivelId}/versoes/${versaoId}/status`, {
        status: novoStatus,
      });

      await Promise.all([carregarArvore(), carregarVersoes(selectedNivelId)]);
    } catch {
      setErrorMessage("Não foi possível atualizar o status da versão.");
    } finally {
      setUpdatingVersaoId(null);
    }
  }

  async function handleSalvarControleSeguranca(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedNivel || selectedNivel.tipo !== "classe") {
      setErrorMessage("Selecione um nível do tipo classe para configurar controle e segurança.");
      return;
    }

    let permissoesPorPapel: Record<string, string[]> = {};
    try {
      permissoesPorPapel = JSON.parse(controlePermissoesJson) as Record<string, string[]>;
    } catch {
      setErrorMessage("Permissões inválidas: informe um JSON válido.");
      return;
    }

    const metadadosObrigatorios = controleMetadadosObrigatorios
      .split("\n")
      .map((campo) => campo.trim())
      .filter((campo) => campo.length > 0);
    const unidadesAutorizadas = controleUnidadesAutorizadas
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    setErrorMessage(null);
    setSalvandoControle(true);
    try {
      const { data } = await api.patch<ControleSeguranca>(
        `/pcd/${selectedNivel.id}/controle-seguranca`,
        {
          metadados_obrigatorios: metadadosObrigatorios,
          permissoes_por_papel: permissoesPorPapel,
          unidades_autorizadas: unidadesAutorizadas,
        }
      );

      setControleMetadadosObrigatorios(data.metadados_obrigatorios.join("\n"));
      setControlePermissoesJson(JSON.stringify(data.permissoes_por_papel, null, 2));
      setControleUnidadesAutorizadas(data.unidades_autorizadas.join("\n"));
    } catch {
      setErrorMessage("Não foi possível salvar controle de metadados e permissões.");
    } finally {
      setSalvandoControle(false);
    }
  }

  async function handleValidarMetadadosClasse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedNivel || selectedNivel.tipo !== "classe") {
      setErrorMessage("Selecione um nível do tipo classe para validar metadados.");
      return;
    }

    let metadadosDocumento: Record<string, unknown> = {};
    try {
      metadadosDocumento = JSON.parse(metadadosParaValidarJson) as Record<string, unknown>;
    } catch {
      setErrorMessage("Metadados do documento inválidos: informe um JSON válido.");
      return;
    }

    setErrorMessage(null);
    setValidandoMetadados(true);
    try {
      const { data } = await api.post<ValidacaoMetadados>(`/pcd/${selectedNivel.id}/validar-metadados`, {
        metadados_documento: metadadosDocumento,
      });
      setResultadoValidacao(data);
    } catch {
      setErrorMessage("Não foi possível validar metadados obrigatórios da classe.");
    } finally {
      setValidandoMetadados(false);
    }
  }

  async function handleValidarAcessoClasse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedNivel || selectedNivel.tipo !== "classe") {
      setErrorMessage("Selecione um nível do tipo classe para validar acesso.");
      return;
    }

    setErrorMessage(null);
    setValidandoAcesso(true);
    try {
      const { data } = await api.post<ValidacaoAcesso>(`/pcd/${selectedNivel.id}/validar-acesso`, {
        acao: acaoAcesso,
      });
      setResultadoAcesso(data);
    } catch {
      setErrorMessage("Não foi possível validar acesso da classe.");
    } finally {
      setValidandoAcesso(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Plano de Classificação (PCD)</h1>
        <p className="text-muted-foreground">
          Sprint 3/4 (US-010/US-011): árvore hierárquica, edição e versionamento visual
        </p>
      </div>

      {errorMessage ? (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Novo Nível</CardTitle>
            <CardDescription>
              Cadastre função, atividade, série ou classe na estrutura do PCD
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCriarNivel} className="space-y-3">
              <select
                value={paiId}
                onChange={(event) => setPaiId(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Sem pai (nível raiz)</option>
                {niveisDisponiveis.map((nivel) => (
                  <option key={nivel.id} value={nivel.id}>
                    [{nivel.tipo}] {nivel.codigo} - {nivel.titulo}
                  </option>
                ))}
              </select>

              <select
                value={tipo}
                onChange={(event) => setTipo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="funcao">Função</option>
                <option value="atividade">Atividade</option>
                <option value="serie">Série</option>
                <option value="classe">Classe</option>
              </select>

              <input
                required
                value={codigo}
                onChange={(event) => setCodigo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Código interno"
              />

              <input
                required
                value={titulo}
                onChange={(event) => setTitulo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Título"
              />

              <textarea
                value={descricao}
                onChange={(event) => setDescricao(event.target.value)}
                className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Descrição"
              />

              <input
                value={codigoConarq}
                onChange={(event) => setCodigoConarq(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Código CONARQ (opcional)"
              />

              <select
                value={nivelSigilo}
                onChange={(event) => setNivelSigilo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="publico">Público</option>
                <option value="restrito">Restrito</option>
                <option value="confidencial">Confidencial</option>
                <option value="secreto">Secreto</option>
              </select>

              <Button type="submit" className="w-full" disabled={creating}>
                {creating ? "Salvando..." : "Criar nível"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Árvore Hierárquica</CardTitle>
            <CardDescription>
              {loading
                ? "Carregando estrutura..."
                : `${niveisDisponiveis.length} nível(is) cadastrado(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {niveisRaiz.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Nenhum nível cadastrado ainda.
              </p>
            ) : (
              <div className="space-y-3">{arvoreNiveisRenderizada}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Edição do Nível Selecionado</CardTitle>
            <CardDescription>
              {selectedNivel
                ? `Editando [${selectedNivel.tipo}] ${selectedNivel.codigo}`
                : "Selecione um item da árvore para habilitar a edição"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSalvarEdicao} className="space-y-3">
              <input
                required
                disabled={!selectedNivel || savingEdit}
                value={editTitulo}
                onChange={(event) => setEditTitulo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Título"
              />

              <textarea
                disabled={!selectedNivel || savingEdit}
                value={editDescricao}
                onChange={(event) => setEditDescricao(event.target.value)}
                className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Descrição"
              />

              <input
                disabled={!selectedNivel || savingEdit}
                value={editCodigoConarq}
                onChange={(event) => setEditCodigoConarq(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Código CONARQ"
              />

              <select
                disabled={!selectedNivel || savingEdit}
                value={editNivelSigilo}
                onChange={(event) => setEditNivelSigilo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="publico">Público</option>
                <option value="restrito">Restrito</option>
                <option value="confidencial">Confidencial</option>
                <option value="secreto">Secreto</option>
              </select>

              <select
                disabled={!selectedNivel || savingEdit}
                value={editStatus}
                onChange={(event) => setEditStatus(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="rascunho">Rascunho</option>
                <option value="ativo">Ativo</option>
                <option value="arquivado">Arquivado</option>
              </select>

              <textarea
                disabled={!selectedNivel || savingEdit}
                value={editMetadados}
                onChange={(event) => setEditMetadados(event.target.value)}
                className="min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder='Metadados JSON (ex.: {"setor": "RH"})'
              />

              <Button type="submit" className="w-full" disabled={!selectedNivel || savingEdit}>
                {savingEdit ? "Salvando..." : "Salvar alterações"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Versionamento e Aprovação</CardTitle>
            <CardDescription>
              {selectedNivel
                ? `${versoes.length} versão(ões) para o nível selecionado`
                : "Selecione um item da árvore para gerenciar versões"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleCriarVersao} className="space-y-2">
              <textarea
                required
                disabled={!selectedNivel || creatingVersao}
                value={justificativaVersao}
                onChange={(event) => setJustificativaVersao(event.target.value)}
                className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Justificativa da nova versão"
              />
              <Button type="submit" className="w-full" disabled={!selectedNivel || creatingVersao}>
                {creatingVersao ? "Versionando..." : "Criar versão"}
              </Button>
            </form>

            <div className="space-y-2">
              {loadingVersoes ? (
                <p className="text-sm text-muted-foreground">Carregando versões...</p>
              ) : versoes.length === 0 ? (
                <p className="text-sm text-muted-foreground">Sem versões registradas para o item selecionado.</p>
              ) : (
                versoes.map((versao) => (
                  <div key={versao.id} className="rounded-md border border-border p-3">
                    <p className="text-sm font-medium text-foreground">
                      v{versao.versao} · {versao.status}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(versao.created_at).toLocaleString("pt-BR")} · {versao.justificativa}
                    </p>
                    {versao.status === "pendente" ? (
                      <div className="mt-2 flex gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => handleAtualizarStatusVersao(versao.id, "aprovado")}
                          disabled={updatingVersaoId === versao.id}
                        >
                          Aprovar
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => handleAtualizarStatusVersao(versao.id, "rejeitado")}
                          disabled={updatingVersaoId === versao.id}
                        >
                          Rejeitar
                        </Button>
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Diff Visual entre Versões</CardTitle>
          <CardDescription>
            Compare snapshots de duas versões para inspecionar alterações de conteúdo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <select
              value={compararVersaoA}
              onChange={(event) => setCompararVersaoA(event.target.value)}
              disabled={versoes.length === 0}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Versão A</option>
              {versoes.map((item) => (
                <option key={item.id} value={item.id}>
                  v{item.versao} · {item.status}
                </option>
              ))}
            </select>

            <select
              value={compararVersaoB}
              onChange={(event) => setCompararVersaoB(event.target.value)}
              disabled={versoes.length === 0}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Versão B</option>
              {versoes.map((item) => (
                <option key={item.id} value={item.id}>
                  v{item.versao} · {item.status}
                </option>
              ))}
            </select>
          </div>

          {!versaoA || !versaoB ? (
            <p className="text-sm text-muted-foreground">
              Selecione duas versões para visualizar diferenças.
            </p>
          ) : diffVersoes.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Não há diferenças entre os snapshots selecionados.
            </p>
          ) : (
            <div className="space-y-2">
              {diffVersoes.map((item) => (
                <div key={item.campo} className="rounded-md border border-border p-3">
                  <p className="text-sm font-medium text-foreground">{item.campo}</p>
                  <p className="text-xs text-muted-foreground">A: {item.valorA}</p>
                  <p className="text-xs text-muted-foreground">B: {item.valorB}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>US-012 · Metadados e Controle de Acesso</CardTitle>
          <CardDescription>
            Configure metadados obrigatórios e permissões por papel para classes do PCD
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!selectedNivel ? (
            <p className="text-sm text-muted-foreground">
              Selecione um item da árvore para configurar o controle de metadados.
            </p>
          ) : !selectedNivelEhClasse ? (
            <p className="text-sm text-muted-foreground">
              O controle de metadados e permissões está disponível apenas para níveis do tipo classe.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <form onSubmit={handleSalvarControleSeguranca} className="space-y-3">
                <p className="text-sm font-medium text-foreground">Configuração da classe</p>

                <textarea
                  value={controleMetadadosObrigatorios}
                  onChange={(event) => setControleMetadadosObrigatorios(event.target.value)}
                  className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder={"Metadados obrigatórios (um por linha)\nEx.:\nsetor\ncpf_responsavel"}
                />

                <textarea
                  value={controlePermissoesJson}
                  onChange={(event) => setControlePermissoesJson(event.target.value)}
                  className="min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder='Permissões por papel em JSON (ex.: {"arquivista":["ler","editar"]})'
                />

                <textarea
                  value={controleUnidadesAutorizadas}
                  onChange={(event) => setControleUnidadesAutorizadas(event.target.value)}
                  className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder={"Unidades autorizadas (uma por linha)\nEx.:\nRJ\nSP"}
                />

                <Button type="submit" className="w-full" disabled={salvandoControle}>
                  {salvandoControle ? "Salvando controle..." : "Salvar controle da classe"}
                </Button>
              </form>

              <div className="space-y-4">
                <form onSubmit={handleValidarMetadadosClasse} className="space-y-3">
                <p className="text-sm font-medium text-foreground">Validação de metadados obrigatórios</p>

                <textarea
                  value={metadadosParaValidarJson}
                  onChange={(event) => setMetadadosParaValidarJson(event.target.value)}
                  className="min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder='Metadados do documento em JSON (ex.: {"setor":"RH"})'
                />

                <Button type="submit" className="w-full" disabled={validandoMetadados}>
                  {validandoMetadados ? "Validando..." : "Validar metadados"}
                </Button>

                {resultadoValidacao ? (
                  <div className="rounded-md border border-border p-3">
                    <p className="text-sm font-medium text-foreground">
                      Resultado: {resultadoValidacao.valido ? "Válido" : "Inválido"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Faltantes: {resultadoValidacao.faltantes.length === 0 ? "nenhum" : resultadoValidacao.faltantes.join(", ")}
                    </p>
                  </div>
                ) : null}
                </form>

                <form onSubmit={handleValidarAcessoClasse} className="space-y-3">
                  <p className="text-sm font-medium text-foreground">Validação RBAC/ABAC</p>

                  <select
                    value={acaoAcesso}
                    onChange={(event) => setAcaoAcesso(event.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="ler">Ler</option>
                    <option value="editar">Editar</option>
                    <option value="aprovar">Aprovar</option>
                  </select>

                  <Button type="submit" className="w-full" disabled={validandoAcesso}>
                    {validandoAcesso ? "Validando acesso..." : "Validar acesso atual"}
                  </Button>

                  {resultadoAcesso ? (
                    <div className="rounded-md border border-border p-3">
                      <p className="text-sm font-medium text-foreground">
                        Acesso: {resultadoAcesso.permitido ? "Permitido" : "Negado"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Papel: {resultadoAcesso.papel} · Unidade: {resultadoAcesso.unidade_usuario ?? "—"} · Sigilo: {resultadoAcesso.nivel_sigilo}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Motivos: {resultadoAcesso.motivos.length === 0 ? "nenhum" : resultadoAcesso.motivos.join(", ")}
                      </p>
                    </div>
                  ) : null}
                </form>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
