"use client";

import { useMemo, useState } from "react";
import api from "@/lib/api";
import { useUsuarios } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type UsuarioItem = {
  id: string;
  email: string;
  nome: string;
  role: string;
};

type UsuariosResponse = {
  items: UsuarioItem[];
  total: number;
  page: number;
  per_page: number;
};

type LgpdResumo = {
  user_id: string;
  email_mascarado: string;
  nome_mascarado: string;
  anonimizado: boolean;
  campos_sensiveis: string[];
  dados_mascarados: Record<string, string>;
};

type BackupSnapshot = {
  id: string;
  created_at: string;
  escopo: {
    pcd_nivel_id?: string | null;
    regra_retencao_id?: string | null;
  };
};

type SmokeCheckResult = {
  overall_status: string;
  checked_at: string;
  total_checks: number;
  failed_checks: string[];
  checks: Record<string, Record<string, string | number>>;
};

export default function AdminPage() {
  const [selectedUserId, setSelectedUserId] = useState("");
  const [cpf, setCpf] = useState("");
  const [emailSecundario, setEmailSecundario] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [resumo, setResumo] = useState<LgpdResumo | null>(null);
  const [pcdBackupId, setPcdBackupId] = useState("");
  const [regraBackupId, setRegraBackupId] = useState("");
  const [backupSnapshots, setBackupSnapshots] = useState<BackupSnapshot[]>([]);
  const [smokeResult, setSmokeResult] = useState<SmokeCheckResult | null>(null);

  const { data: usuariosRaw, isLoading } = useUsuarios();
  const usuarios = useMemo(
    () => (((usuariosRaw as UsuariosResponse | undefined)?.items ?? []) as UsuarioItem[]),
    [usuariosRaw]
  );

  const usuarioSelecionado = useMemo(
    () => usuarios.find((item) => item.id === selectedUserId) ?? null,
    [usuarios, selectedUserId]
  );

  async function handleProteger() {
    if (!selectedUserId) {
      setErrorMessage("Selecione um usuário.");
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("proteger");
    try {
      const { data } = await api.post<LgpdResumo>(`/admin/usuarios/${selectedUserId}/lgpd/proteger`, {
        cpf: cpf || null,
        email_secundario: emailSecundario || null,
      });
      setResumo(data);
      setSuccessMessage("Dados sensíveis protegidos com criptografia e masking.");
    } catch {
      setErrorMessage("Falha ao proteger dados do usuário.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleResumo() {
    if (!selectedUserId) {
      setErrorMessage("Selecione um usuário.");
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("resumo");
    try {
      const { data } = await api.get<LgpdResumo>(`/admin/usuarios/${selectedUserId}/lgpd/resumo`);
      setResumo(data);
    } catch {
      setErrorMessage("Falha ao consultar resumo LGPD.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleAnonimizar() {
    if (!selectedUserId) {
      setErrorMessage("Selecione um usuário.");
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("anonimizar");
    try {
      const { data } = await api.post<LgpdResumo>(`/admin/usuarios/${selectedUserId}/lgpd/anonimizar`);
      setResumo(data);
      setSuccessMessage("Usuário anonimizado conforme política LGPD.");
    } catch {
      setErrorMessage("Falha ao anonimizar usuário.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function loadBackups() {
    try {
      const { data } = await api.get<BackupSnapshot[]>("/backup/snapshots");
      setBackupSnapshots(data);
    } catch {
      setBackupSnapshots([]);
    }
  }

  async function handleCriarBackup() {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("backup");
    try {
      await api.post("/backup/snapshots", {
        pcd_nivel_id: pcdBackupId || null,
        regra_retencao_id: regraBackupId || null,
      });
      await loadBackups();
      setSuccessMessage("Snapshot incremental criado com sucesso.");
    } catch {
      setErrorMessage("Falha ao criar snapshot incremental.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleRestaurar(snapshotId: string) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`restore-${snapshotId}`);
    try {
      await api.post(`/backup/snapshots/${snapshotId}/restore`);
      setSuccessMessage("Restauração parcial executada com sucesso.");
    } catch {
      setErrorMessage("Falha ao restaurar snapshot.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleExecutarSmoke() {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("smoke");
    try {
      const { data } = await api.get<SmokeCheckResult>("/health/smoke");
      setSmokeResult(data);
      setSuccessMessage(
        data.overall_status === "ok"
          ? "Smoke check operacional concluído sem falhas."
          : "Smoke check concluído com alertas; revise os módulos sinalizados."
      );
    } catch {
      setErrorMessage("Falha ao executar smoke check operacional.");
    } finally {
      setLoadingAction(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Administração</h1>
        <p className="text-muted-foreground">
          EP7 (US-061): proteção LGPD, criptografia em repouso e anonimização
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
          <CardTitle>Painel LGPD</CardTitle>
          <CardDescription>
            {isLoading ? "Carregando usuários..." : `${usuarios.length} usuário(s) disponíveis`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <select
            value={selectedUserId}
            onChange={(event) => setSelectedUserId(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Selecione um usuário</option>
            {usuarios.map((usuario) => (
              <option key={usuario.id} value={usuario.id}>
                {usuario.nome} · {usuario.email} · {usuario.role}
              </option>
            ))}
          </select>

          <input
            value={cpf}
            onChange={(event) => setCpf(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="CPF sensível"
          />

          <input
            value={emailSecundario}
            onChange={(event) => setEmailSecundario(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Email secundário sensível"
          />

          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={handleProteger} disabled={loadingAction !== null}>
              {loadingAction === "proteger" ? "Protegendo..." : "Proteger dados"}
            </Button>
            <Button type="button" variant="outline" onClick={handleResumo} disabled={loadingAction !== null}>
              {loadingAction === "resumo" ? "Consultando..." : "Consultar resumo"}
            </Button>
            <Button type="button" variant="outline" onClick={handleAnonimizar} disabled={loadingAction !== null}>
              {loadingAction === "anonimizar" ? "Anonimizando..." : "Anonimizar"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resumo protegido</CardTitle>
          <CardDescription>
            {usuarioSelecionado ? `Usuário selecionado: ${usuarioSelecionado.nome}` : "Selecione um usuário para ver o resumo"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!resumo ? (
            <p className="text-sm text-muted-foreground">Nenhum resumo LGPD carregado.</p>
          ) : (
            <div className="space-y-2 rounded-md border border-border p-3">
              <p className="text-sm font-medium text-foreground">
                Nome: {resumo.nome_mascarado} · Email: {resumo.email_mascarado}
              </p>
              <p className="text-xs text-muted-foreground">
                Anonimizado: {resumo.anonimizado ? "sim" : "não"}
              </p>
              <p className="text-xs text-muted-foreground">
                Campos sensíveis: {resumo.campos_sensiveis.length === 0 ? "nenhum" : resumo.campos_sensiveis.join(", ")}
              </p>
              <div className="space-y-1">
                {Object.entries(resumo.dados_mascarados).map(([campo, valor]) => (
                  <p key={campo} className="text-xs text-muted-foreground">
                    {campo}: {valor}
                  </p>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Backup e Restauração</CardTitle>
          <CardDescription>
            US-071: snapshots incrementais e restauração parcial por classe/regra
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            value={pcdBackupId}
            onChange={(event) => setPcdBackupId(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="ID da classe PCD para backup"
          />
          <input
            value={regraBackupId}
            onChange={(event) => setRegraBackupId(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="ID da regra de retenção para backup"
          />
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={handleCriarBackup} disabled={loadingAction !== null}>
              {loadingAction === "backup" ? "Criando backup..." : "Criar snapshot"}
            </Button>
            <Button type="button" variant="outline" onClick={loadBackups} disabled={loadingAction !== null}>
              Atualizar lista
            </Button>
          </div>

          <div className="space-y-2">
            {backupSnapshots.map((snapshot) => (
              <div key={snapshot.id} className="rounded-md border border-border p-3">
                <p className="text-sm font-medium text-foreground">Snapshot {snapshot.id.slice(0, 8)}</p>
                <p className="text-xs text-muted-foreground">
                  Classe: {snapshot.escopo.pcd_nivel_id ?? "—"} · Regra: {snapshot.escopo.regra_retencao_id ?? "—"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Criado em {new Date(snapshot.created_at).toLocaleString("pt-BR")}
                </p>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="mt-2"
                  onClick={() => handleRestaurar(snapshot.id)}
                  disabled={loadingAction === `restore-${snapshot.id}`}
                >
                  {loadingAction === `restore-${snapshot.id}` ? "Restaurando..." : "Restaurar"}
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Smoke Check Operacional</CardTitle>
          <CardDescription>
            Sprint 15: validação rápida de PCD, TTD, integração, migração, conhecimento, observabilidade e backup.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={handleExecutarSmoke} disabled={loadingAction !== null}>
              {loadingAction === "smoke" ? "Executando smoke..." : "Executar smoke check"}
            </Button>
          </div>

          {!smokeResult ? (
            <p className="text-sm text-muted-foreground">Nenhum smoke check executado nesta sessão.</p>
          ) : (
            <div className="space-y-3 rounded-md border border-border p-3">
              <p className="text-sm font-medium text-foreground">
                Status geral: {smokeResult.overall_status} · Checks: {smokeResult.total_checks}
              </p>
              <p className="text-xs text-muted-foreground">
                Executado em {new Date(smokeResult.checked_at).toLocaleString("pt-BR")}
              </p>
              <p className="text-xs text-muted-foreground">
                Falhas: {smokeResult.failed_checks.length === 0 ? "nenhuma" : smokeResult.failed_checks.join(", ")}
              </p>

              <div className="space-y-2">
                {Object.entries(smokeResult.checks).map(([modulo, detalhe]) => (
                  <div key={modulo} className="rounded border border-border/60 p-2">
                    <p className="text-xs font-medium text-foreground">
                      {modulo} · {String(detalhe.status ?? "ok")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {Object.entries(detalhe)
                        .filter(([chave]) => chave !== "status")
                        .map(([chave, valor]) => `${chave}: ${String(valor)}`)
                        .join(" · ") || "sem métricas adicionais"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
