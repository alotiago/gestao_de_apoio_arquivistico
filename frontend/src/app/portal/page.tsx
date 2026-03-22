"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type EntrevistaCliente = {
  id: string;
  roteiro_id: string;
  roteiro_titulo: string;
  roteiro_area: string | null;
  status: string;
  respostas: Record<string, unknown>;
  motivo_devolucao: string | null;
  created_at: string;
  completed_at: string | null;
};

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  em_andamento: { label: "Em andamento", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  submetida: { label: "Submetida", color: "bg-blue-100 text-blue-800 border-blue-200" },
  devolvida: { label: "Devolvida", color: "bg-red-100 text-red-800 border-red-200" },
  concluida: { label: "Concluída", color: "bg-green-100 text-green-800 border-green-200" },
  cancelada: { label: "Cancelada", color: "bg-gray-100 text-gray-800 border-gray-200" },
};

export default function PortalPage() {
  const [entrevistas, setEntrevistas] = useState<EntrevistaCliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/portal/entrevistas")
      .then(({ data }) => setEntrevistas(data))
      .catch(() => setError("Não foi possível carregar suas entrevistas."))
      .finally(() => setLoading(false));
  }, []);

  const editaveis = (s: string) => s === "em_andamento" || s === "devolvida";

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Minhas Entrevistas</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Responda às entrevistas atribuídas a você pelos arquivistas.
        </p>
      </div>

      {loading && (
        <p className="text-sm text-muted-foreground">Carregando...</p>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && !error && entrevistas.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              Nenhuma entrevista atribuída a você no momento.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {entrevistas.map((e) => {
          const cfg = STATUS_CONFIG[e.status] || STATUS_CONFIG.em_andamento;
          return (
            <Card key={e.id} className="transition-shadow hover:shadow-md">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-lg">{e.roteiro_titulo}</CardTitle>
                    <CardDescription>
                      {e.roteiro_area && <span>{e.roteiro_area} · </span>}
                      Criada em{" "}
                      {new Date(e.created_at).toLocaleDateString("pt-BR")}
                    </CardDescription>
                  </div>
                  <span
                    className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.color}`}
                  >
                    {cfg.label}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="flex items-center justify-between gap-4">
                {e.status === "devolvida" && e.motivo_devolucao && (
                  <div className="flex-1 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    <strong>Devolução:</strong> {e.motivo_devolucao}
                  </div>
                )}
                {e.status !== "devolvida" && <div className="flex-1" />}

                <Link href={`/portal/entrevistas/${e.id}`}>
                  <Button
                    variant={editaveis(e.status) ? "default" : "outline"}
                    size="sm"
                  >
                    {editaveis(e.status) ? "Responder" : "Visualizar"}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
