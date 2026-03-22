"use client";

import Link from "next/link";
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
  ativo?: boolean;
  departamento?: string | null;
  unidade?: string | null;
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

type ResetSenhaResponse = {
  user_id: string;
  senha_temporaria: string;
  force_password_change: boolean;
};

const crudLinks = [
  { href: "/dashboard/pcd", label: "PCD", description: "Plano de classificação" },
  { href: "/dashboard/ttd", label: "TTD", description: "Regras, hold e destinação" },
  { href: "/dashboard/governanca", label: "Governança", description: "Matriz e auditoria" },
  { href: "/dashboard/dados-migracao", label: "Dados/Migração", description: "Inventário, cleansing e ondas" },
  { href: "/dashboard/conhecimento", label: "Conhecimento", description: "Templates e trilhas" },
  { href: "/dashboard/ciclo-vida", label: "Ciclo de Vida", description: "Jobs e selos" },
  { href: "/dashboard/integracao", label: "Integração", description: "Importações e reprocessamento" },
  { href: "/dashboard/perfil", label: "Perfil", description: "Troca de senha própria" },
];

export default function AdminPage() {
  const [selectedUserId, setSelectedUserId] = useState("");
  const [novoNome, setNovoNome] = useState("");
  const [novoEmail, setNovoEmail] = useState("");
  const [novoRole, setNovoRole] = useState("viewer");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [novoDepartamento, setNovoDepartamento] = useState("");
  const [novaUnidade, setNovaUnidade] = useState("");
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
  const [senhaTemporaria, setSenhaTemporaria] = useState<string | null>(null);
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [editNome, setEditNome] = useState("");
  const [editRole, setEditRole] = useState("viewer");
  const [editDepartamento, setEditDepartamento] = useState("");
  const [editUnidade, setEditUnidade] = useState("");

  const { data: usuariosRaw, isLoading, mutate: mutateUsuarios } = useUsuarios();
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

  async function handleResetSenha() {
    if (!selectedUserId) {
      setErrorMessage("Selecione um usuário.");
      return;
    }
    if (!confirm("Deseja resetar a senha deste usuário?")) {
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setSenhaTemporaria(null);
    setLoadingAction("reset-senha");
    try {
      const { data } = await api.post<ResetSenhaResponse>(`/admin/usuarios/${selectedUserId}/reset-senha`);
      setSenhaTemporaria(data.senha_temporaria);
      setSuccessMessage("Senha resetada com sucesso.");
    } catch {
      setErrorMessage("Falha ao resetar senha do usuário.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleCriarUsuario() {
    if (!novoNome.trim() || !novoEmail.trim() || !novaSenha.trim()) {
      setErrorMessage("Preencha nome, email e senha para criar o usuário.");
      return;
    }
    if (novaSenha !== confirmarSenha) {
      setErrorMessage("A confirmação de senha não confere.");
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction("create-user");
    try {
      const { data } = await api.post<UsuarioItem>("/admin/usuarios", {
        email: novoEmail.trim().toLowerCase(),
        nome: novoNome.trim(),
        senha: novaSenha,
        role: novoRole,
        departamento: novoDepartamento.trim() || null,
        unidade: novaUnidade.trim() || null,
        atributos: {},
      });

      await mutateUsuarios();
      setSelectedUserId(data.id);
      setNovoNome("");
      setNovoEmail("");
      setNovaSenha("");
      setConfirmarSenha("");
      setNovoRole("viewer");
      setNovoDepartamento("");
      setNovaUnidade("");
      setSuccessMessage("Usuário criado com sucesso e disponível no Painel LGPD.");
    } catch {
      setErrorMessage("Falha ao criar usuário. Verifique permissões e se o email já existe.");
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

  function handleIniciarEdicaoUsuario(usuario: UsuarioItem) {
    setEditingUserId(usuario.id);
    setEditNome(usuario.nome || "");
    setEditRole(usuario.role || "viewer");
    setEditDepartamento(usuario.departamento || "");
    setEditUnidade(usuario.unidade || "");
  }

  function handleCancelarEdicaoUsuario() {
    setEditingUserId(null);
    setEditNome("");
    setEditRole("viewer");
    setEditDepartamento("");
    setEditUnidade("");
  }

  async function handleSalvarUsuario(userId: string) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`save-user-${userId}`);
    try {
      await api.patch(`/admin/usuarios/${userId}`, {
        nome: editNome,
        role: editRole,
        departamento: editDepartamento || null,
        unidade: editUnidade || null,
      });
      await mutateUsuarios();
      setSuccessMessage("Usuário atualizado com sucesso.");
      handleCancelarEdicaoUsuario();
    } catch {
      setErrorMessage("Falha ao atualizar usuário.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleDesativarUsuario(userId: string) {
    if (!confirm("Deseja desativar este usuário?")) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoadingAction(`disable-user-${userId}`);
    try {
      await api.delete(`/admin/usuarios/${userId}`);
      await mutateUsuarios();
      setSuccessMessage("Usuário desativado com sucesso.");
      if (selectedUserId === userId) {
        setSelectedUserId("");
      }
    } catch {
      setErrorMessage("Falha ao desativar usuário.");
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
          <CardTitle>Acessos rápidos</CardTitle>
          <CardDescription>
            Atalhos para os CRUDs e fluxos administrativos disponíveis no dashboard.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {crudLinks.map((item) => (
              <div key={item.href} className="rounded-lg border border-border p-4">
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="mt-1 text-xs text-muted-foreground">{item.description}</p>
                <Button asChild className="mt-3" variant="outline">
                  <Link href={item.href}>Abrir</Link>
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Criar usuário</CardTitle>
          <CardDescription>
            Cadastro rápido para disponibilizar usuários no Painel LGPD.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            value={novoNome}
            onChange={(event) => setNovoNome(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Nome completo"
          />
          <input
            type="email"
            value={novoEmail}
            onChange={(event) => setNovoEmail(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Email"
          />
          <select
            value={novoRole}
            onChange={(event) => setNovoRole(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="viewer">viewer</option>
            <option value="analista">analista</option>
            <option value="arquivista">arquivista</option>
            <option value="classificador">classificador</option>
            <option value="auditor">auditor</option>
            <option value="gestor">gestor</option>
            <option value="admin">admin</option>
            <option value="cliente">cliente</option>
          </select>
          <input
            value={novoDepartamento}
            onChange={(event) => setNovoDepartamento(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Departamento (opcional)"
          />
          <input
            value={novaUnidade}
            onChange={(event) => setNovaUnidade(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Unidade (opcional)"
          />
          <input
            type="password"
            value={novaSenha}
            onChange={(event) => setNovaSenha(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Senha inicial"
          />
          <input
            type="password"
            value={confirmarSenha}
            onChange={(event) => setConfirmarSenha(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Confirmar senha"
          />
          <Button type="button" onClick={handleCriarUsuario} disabled={loadingAction !== null}>
            {loadingAction === "create-user" ? "Criando usuário..." : "Criar usuário"}
          </Button>
        </CardContent>
      </Card>

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
            <Button type="button" variant="outline" onClick={handleResetSenha} disabled={loadingAction !== null}>
              {loadingAction === "reset-senha" ? "Resetando..." : "Reset senha"}
            </Button>
          </div>
          {senhaTemporaria ? (
            <p className="text-xs text-muted-foreground">
              Senha temporária: <strong>{senhaTemporaria}</strong>
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Gestão de usuários</CardTitle>
          <CardDescription>
            Edição rápida de perfil/permissão e desativação de usuários.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {usuarios.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhum usuário disponível.</p>
          ) : (
            usuarios.map((usuario) => (
              <div key={usuario.id} className="rounded-md border border-border p-3">
                {editingUserId === usuario.id ? (
                  <div className="space-y-2">
                    <input
                      value={editNome}
                      onChange={(event) => setEditNome(event.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      placeholder="Nome"
                    />
                    <select
                      value={editRole}
                      onChange={(event) => setEditRole(event.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="viewer">viewer</option>
                      <option value="analista">analista</option>
                      <option value="arquivista">arquivista</option>
                      <option value="classificador">classificador</option>
                      <option value="auditor">auditor</option>
                      <option value="gestor">gestor</option>
                      <option value="admin">admin</option>
                      <option value="cliente">cliente</option>
                    </select>
                    <input
                      value={editDepartamento}
                      onChange={(event) => setEditDepartamento(event.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      placeholder="Departamento"
                    />
                    <input
                      value={editUnidade}
                      onChange={(event) => setEditUnidade(event.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      placeholder="Unidade"
                    />
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => handleSalvarUsuario(usuario.id)}
                        disabled={loadingAction === `save-user-${usuario.id}`}
                      >
                        {loadingAction === `save-user-${usuario.id}` ? "Salvando..." : "Salvar"}
                      </Button>
                      <Button type="button" size="sm" variant="outline" onClick={handleCancelarEdicaoUsuario}>
                        Cancelar
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-sm font-medium text-foreground">{usuario.nome}</p>
                    <p className="text-xs text-muted-foreground">{usuario.email} · {usuario.role}</p>
                    <div className="mt-2 flex gap-2">
                      <Button type="button" size="sm" variant="outline" onClick={() => handleIniciarEdicaoUsuario(usuario)}>
                        Editar
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => handleDesativarUsuario(usuario.id)}
                        disabled={loadingAction === `disable-user-${usuario.id}`}
                      >
                        {loadingAction === `disable-user-${usuario.id}` ? "Desativando..." : "Desativar"}
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
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
