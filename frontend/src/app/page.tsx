import Link from "next/link";
import {
  FileText,
  FolderTree,
  Clock,
  RotateCcw,
  Shield,
  BarChart3,
} from "lucide-react";

const modules = [
  {
    title: "Entrevistas",
    description: "Roteiros dinâmicos e entrevistas assistidas por IA",
    href: "/dashboard/entrevistas",
    icon: FileText,
  },
  {
    title: "Plano de Classificação",
    description: "PCD hierárquico com versionamento e CONARQ",
    href: "/dashboard/pcd",
    icon: FolderTree,
  },
  {
    title: "Tabela de Temporalidade",
    description: "Regras de retenção, legal holds e destinação",
    href: "/dashboard/ttd",
    icon: Clock,
  },
  {
    title: "Ciclo de Vida",
    description: "Workflows, jobs de retenção e automação",
    href: "/dashboard/ciclo-vida",
    icon: RotateCcw,
  },
  {
    title: "Governança",
    description: "Matriz de rastreabilidade e audit logs",
    href: "/dashboard/governanca",
    icon: Shield,
  },
  {
    title: "Painel",
    description: "Dashboard com indicadores e métricas",
    href: "/dashboard",
    icon: BarChart3,
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background bg-[url('/branding/hw1-gradient.webp')] bg-cover bg-top bg-no-repeat">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-secondary-foreground mb-4">
            Gestão de Apoio Arquivístico
          </h1>
          <p className="text-lg text-secondary-foreground/80 max-w-2xl mx-auto">
            Sistema integrado para gestão documental com suporte a entrevistas
            assistidas, classificação, temporalidade e ciclo de vida.
          </p>
        </div>

        {/* Module Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {modules.map((mod) => (
            <Link
              key={mod.href}
              href={mod.href}
              className="group block rounded-xl border border-border bg-background/95 p-6 shadow-sm backdrop-blur transition-all hover:shadow-md hover:border-primary/40"
            >
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 mb-4">
                <mod.icon className="w-6 h-6 text-primary" />
              </div>
              <h2 className="text-xl font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                {mod.title}
              </h2>
              <p className="text-sm text-muted-foreground">{mod.description}</p>
            </Link>
          ))}
        </div>

        {/* Footer */}
        <div className="text-center mt-16 text-sm text-secondary-foreground/70">
          <p>Sprint 0 — Infraestrutura & Scaffold</p>
        </div>
      </div>
    </main>
  );
}
