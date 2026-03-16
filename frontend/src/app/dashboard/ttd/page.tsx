"use client";

import { FormEvent, useMemo, useState } from "react";
import api from "@/lib/api";
import {
  useLegalHolds,
  useOrdensDestinacao,
  usePcdArvore,
  useRegrasRetencao,
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

type RegraRetencao = {
  id: string;
  pcd_nivel_id: string;
  evento_inicio: string;
  prazo_dias: number;
  destinacao_final: string;
  base_legal: string | null;
  legislacao_ref: string | null;
};

type LegalHold = {
  id: string;
  pcd_nivel_id: string;
  motivo: string;
  tipo: string;
  status: string;
  data_inicio: string;
};

type OrdemDestinacao = {
  id: string;
  tipo: string;
  status: string;
  aprovador_1_id: string | null;
  aprovador_2_id: string | null;
  hash_termo: string | null;
  assinatura_digital: string | null;
  carimbo_tempo: string | null;
  items: Record<string, unknown>[];
  created_at: string;
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

export default function TtdPage() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [creatingRegra, setCreatingRegra] = useState(false);
  const [creatingHold, setCreatingHold] = useState(false);
  const [revogandoId, setRevogandoId] = useState<string | null>(null);
  const [creatingOrdem, setCreatingOrdem] = useState(false);
  const [aprovarOrdemId, setAprovarOrdemId] = useState<string | null>(null);
  const [assinarOrdemId, setAssinarOrdemId] = useState<string | null>(null);

  const [regraPcdNivelId, setRegraPcdNivelId] = useState("");
  const [eventoInicio, setEventoInicio] = useState("fim_contrato");
  const [prazoDias, setPrazoDias] = useState(365);
  const [destinacaoFinal, setDestinacaoFinal] = useState("eliminacao");
  const [baseLegal, setBaseLegal] = useState("");
  const [legislacaoRef, setLegislacaoRef] = useState("");

  const [holdPcdNivelId, setHoldPcdNivelId] = useState("");
  const [holdMotivo, setHoldMotivo] = useState("");
  const [holdTipo, setHoldTipo] = useState("auditoria");

  const [ordemTipo, setOrdemTipo] = useState("eliminacao");
  const [ordemItemsJson, setOrdemItemsJson] = useState("[]");
  const [assinaturaDigital, setAssinaturaDigital] = useState("");

  const { data: pcdRaw } = usePcdArvore();
  const niveisFlat = useMemo(
    () => flattenPcdTree((pcdRaw as PcdNivel[] | undefined) ?? []),
    [pcdRaw]
  );

  const {
    data: regrasRaw,
    mutate: mutateRegras,
    isLoading: loadingRegras,
  } = useRegrasRetencao();
  const regras = (regrasRaw as RegraRetencao[] | undefined) ?? [];

  const {
    data: holdsRaw,
    mutate: mutateHolds,
    isLoading: loadingHolds,
  } = useLegalHolds();
  const holds = (holdsRaw as LegalHold[] | undefined) ?? [];

  const {
    data: ordensRaw,
    mutate: mutateOrdens,
    isLoading: loadingOrdens,
  } = useOrdensDestinacao();
  const ordens = (ordensRaw as OrdemDestinacao[] | undefined) ?? [];

  async function handleCriarRegra(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!regraPcdNivelId) {
      setErrorMessage("Selecione um nível do PCD para criar a regra.");
      return;
    }

    setErrorMessage(null);
    setCreatingRegra(true);
    try {
      await api.post("/ttd/regras", {
        pcd_nivel_id: regraPcdNivelId,
        evento_inicio: eventoInicio,
        prazo_dias: prazoDias,
        fase_corrente: 0,
        fase_intermediaria: 0,
        destinacao_final: destinacaoFinal,
        base_legal: baseLegal || null,
        legislacao_ref: legislacaoRef || null,
        observacoes: null,
      });

      setRegraPcdNivelId("");
      setEventoInicio("fim_contrato");
      setPrazoDias(365);
      setDestinacaoFinal("eliminacao");
      setBaseLegal("");
      setLegislacaoRef("");
      await mutateRegras();
    } catch {
      setErrorMessage("Falha ao criar regra de retenção.");
    } finally {
      setCreatingRegra(false);
    }
  }

  async function handleAplicarHold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!holdPcdNivelId) {
      setErrorMessage("Selecione um nível do PCD para aplicar hold.");
      return;
    }

    setErrorMessage(null);
    setCreatingHold(true);
    try {
      await api.post("/ttd/holds", {
        pcd_nivel_id: holdPcdNivelId,
        motivo: holdMotivo,
        tipo: holdTipo,
        data_expiracao: null,
        evidencia: null,
      });

      setHoldPcdNivelId("");
      setHoldMotivo("");
      setHoldTipo("auditoria");
      await mutateHolds();
    } catch {
      setErrorMessage("Falha ao aplicar legal hold.");
    } finally {
      setCreatingHold(false);
    }
  }

  async function handleRevogarHold(holdId: string) {
    setErrorMessage(null);
    setRevogandoId(holdId);
    try {
      await api.patch(`/ttd/holds/${holdId}/revogar`);
      await mutateHolds();
    } catch {
      setErrorMessage("Falha ao revogar hold.");
    } finally {
      setRevogandoId(null);
    }
  }

  async function handleCriarOrdem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    let parsedItems: Record<string, unknown>[] = [];
    try {
      parsedItems = JSON.parse(ordemItemsJson) as Record<string, unknown>[];
      if (!Array.isArray(parsedItems)) {
        setErrorMessage("Itens da ordem devem ser uma lista JSON.");
        return;
      }
    } catch {
      setErrorMessage("Itens da ordem inválidos: informe JSON válido.");
      return;
    }

    setErrorMessage(null);
    setCreatingOrdem(true);
    try {
      await api.post("/ttd/ordens", {
        tipo: ordemTipo,
        items: parsedItems,
      });

      setOrdemTipo("eliminacao");
      setOrdemItemsJson("[]");
      await mutateOrdens();
    } catch {
      setErrorMessage("Falha ao criar ordem de destinação.");
    } finally {
      setCreatingOrdem(false);
    }
  }

  async function handleAprovarOrdem(ordemId: string) {
    setErrorMessage(null);
    setAprovarOrdemId(ordemId);
    try {
      await api.patch(`/ttd/ordens/${ordemId}/aprovar`);
      await mutateOrdens();
    } catch {
      setErrorMessage("Falha ao aprovar ordem.");
    } finally {
      setAprovarOrdemId(null);
    }
  }

  async function handleAssinarOrdem(ordemId: string) {
    setErrorMessage(null);
    setAssinarOrdemId(ordemId);
    try {
      await api.patch(`/ttd/ordens/${ordemId}/assinar`, {
        assinatura_digital: assinaturaDigital || null,
      });
      setAssinaturaDigital("");
      await mutateOrdens();
    } catch {
      setErrorMessage("Falha ao assinar ordem.");
    } finally {
      setAssinarOrdemId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Tabela de Temporalidade (TTD)</h1>
        <p className="text-muted-foreground">
          Sprint 5 (US-020/US-021): regras de retenção e legal holds
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
            <CardTitle>Nova Regra de Retenção</CardTitle>
            <CardDescription>Defina evento de início, prazo e destinação final</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCriarRegra} className="space-y-3">
              <select
                required
                value={regraPcdNivelId}
                onChange={(event) => setRegraPcdNivelId(event.target.value)}
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
                value={eventoInicio}
                onChange={(event) => setEventoInicio(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Evento de início"
              />

              <input
                type="number"
                min={1}
                value={prazoDias}
                onChange={(event) => setPrazoDias(Number(event.target.value))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Prazo (dias)"
              />

              <select
                value={destinacaoFinal}
                onChange={(event) => setDestinacaoFinal(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="eliminacao">Eliminação</option>
                <option value="guarda_permanente">Guarda Permanente</option>
                <option value="microfilmagem">Microfilmagem</option>
              </select>

              <input
                value={baseLegal}
                onChange={(event) => setBaseLegal(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Base legal (opcional)"
              />

              <input
                value={legislacaoRef}
                onChange={(event) => setLegislacaoRef(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Referência legal (opcional)"
              />

              <Button type="submit" className="w-full" disabled={creatingRegra}>
                {creatingRegra ? "Salvando..." : "Criar regra"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Novo Legal Hold</CardTitle>
            <CardDescription>Suspender temporariamente destinação de documentos</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAplicarHold} className="space-y-3">
              <select
                required
                value={holdPcdNivelId}
                onChange={(event) => setHoldPcdNivelId(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Nível do PCD</option>
                {niveisFlat.map((nivel) => (
                  <option key={nivel.id} value={nivel.id}>
                    [{nivel.tipo}] {nivel.codigo} - {nivel.titulo}
                  </option>
                ))}
              </select>

              <select
                value={holdTipo}
                onChange={(event) => setHoldTipo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="auditoria">Auditoria</option>
                <option value="litigio">Litígio</option>
                <option value="investigacao">Investigação</option>
                <option value="regulatorio">Regulatório</option>
              </select>

              <textarea
                required
                value={holdMotivo}
                onChange={(event) => setHoldMotivo(event.target.value)}
                className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Motivo do hold"
              />

              <Button type="submit" className="w-full" disabled={creatingHold}>
                {creatingHold ? "Aplicando..." : "Aplicar hold"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Regras de Retenção</CardTitle>
            <CardDescription>
              {loadingRegras ? "Carregando regras..." : `${regras.length} regra(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {regras.map((regra) => (
              <div key={regra.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">
                  {regra.evento_inicio} · {regra.prazo_dias} dia(s)
                </p>
                <p className="text-xs text-muted-foreground">
                  Destinação: {regra.destinacao_final} · PCD: {regra.pcd_nivel_id}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Legal Holds</CardTitle>
            <CardDescription>
              {loadingHolds ? "Carregando holds..." : `${holds.length} hold(s)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {holds.map((hold) => (
              <div key={hold.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">
                  [{hold.tipo}] {hold.motivo}
                </p>
                <p className="text-xs text-muted-foreground">
                  Status: {hold.status} · {new Date(hold.data_inicio).toLocaleString("pt-BR")}
                </p>
                {hold.status === "ativo" ? (
                  <div className="mt-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => handleRevogarHold(hold.id)}
                      disabled={revogandoId === hold.id}
                    >
                      {revogandoId === hold.id ? "Revogando..." : "Revogar"}
                    </Button>
                  </div>
                ) : null}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Nova Ordem de Destinação</CardTitle>
            <CardDescription>
              US-022: geração de ordem com itens para aprovação e assinatura
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCriarOrdem} className="space-y-3">
              <select
                value={ordemTipo}
                onChange={(event) => setOrdemTipo(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="eliminacao">Eliminação</option>
                <option value="transferencia">Transferência</option>
                <option value="recolhimento">Recolhimento</option>
              </select>

              <textarea
                value={ordemItemsJson}
                onChange={(event) => setOrdemItemsJson(event.target.value)}
                className="min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder='Itens da ordem em JSON (ex.: [{"pcd_nivel_id":"...","quantidade":12}])'
              />

              <Button type="submit" className="w-full" disabled={creatingOrdem}>
                {creatingOrdem ? "Gerando ordem..." : "Criar ordem"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ordens de Destinação</CardTitle>
            <CardDescription>
              {loadingOrdens ? "Carregando ordens..." : `${ordens.length} ordem(ns)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <input
              value={assinaturaDigital}
              onChange={(event) => setAssinaturaDigital(event.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Assinatura digital opcional (para assinatura do termo)"
            />

            {ordens.map((ordem) => (
              <div key={ordem.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">
                  [{ordem.tipo}] {ordem.status}
                </p>
                <p className="text-xs text-muted-foreground">
                  Itens: {ordem.items.length} · {new Date(ordem.created_at).toLocaleString("pt-BR")}
                </p>
                {ordem.hash_termo ? (
                  <p className="text-xs text-muted-foreground">Hash termo: {ordem.hash_termo.slice(0, 16)}...</p>
                ) : null}

                <div className="mt-2 flex gap-2">
                  {(ordem.status === "pendente" || ordem.status === "em_aprovacao") ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => handleAprovarOrdem(ordem.id)}
                      disabled={aprovarOrdemId === ordem.id}
                    >
                      {aprovarOrdemId === ordem.id ? "Aprovando..." : "Aprovar etapa"}
                    </Button>
                  ) : null}

                  {ordem.status === "aprovado" ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => handleAssinarOrdem(ordem.id)}
                      disabled={assinarOrdemId === ordem.id}
                    >
                      {assinarOrdemId === ordem.id ? "Assinando..." : "Assinar termo"}
                    </Button>
                  ) : null}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
