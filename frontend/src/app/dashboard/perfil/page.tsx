"use client";

import { useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function PerfilPage() {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);

  async function handleAlterarSenha() {
    if (!senhaAtual || !novaSenha) {
      setErro("Preencha senha atual e nova senha.");
      return;
    }
    if (novaSenha !== confirmacao) {
      setErro("A confirmação da nova senha não confere.");
      return;
    }

    setErro(null);
    setSucesso(null);
    setLoading(true);
    try {
      await api.patch("/auth/me/senha", {
        senha_atual: senhaAtual,
        nova_senha: novaSenha,
      });
      setSenhaAtual("");
      setNovaSenha("");
      setConfirmacao("");
      setSucesso("Senha alterada com sucesso.");
    } catch {
      setErro("Falha ao alterar senha. Verifique as regras de complexidade.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Perfil</h1>
        <p className="text-muted-foreground">Self-service de senha para usuários autenticados.</p>
      </div>

      {erro ? (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {erro}
        </div>
      ) : null}
      {sucesso ? (
        <div className="rounded-lg border border-primary/20 bg-primary/10 p-3 text-sm text-primary">
          {sucesso}
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Alterar senha</CardTitle>
          <CardDescription>
            A nova senha deve ter ao menos 8 caracteres, 1 letra maiúscula e 1 número.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            type="password"
            value={senhaAtual}
            onChange={(event) => setSenhaAtual(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Senha atual"
          />
          <input
            type="password"
            value={novaSenha}
            onChange={(event) => setNovaSenha(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Nova senha"
          />
          <input
            type="password"
            value={confirmacao}
            onChange={(event) => setConfirmacao(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Confirmar nova senha"
          />
          <Button type="button" onClick={handleAlterarSenha} disabled={loading}>
            {loading ? "Salvando..." : "Alterar senha"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
