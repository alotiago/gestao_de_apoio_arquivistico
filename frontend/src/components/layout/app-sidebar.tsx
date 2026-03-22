"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Database,
  FileText,
  FolderTree,
  Clock,
  RotateCcw,
  Shield,
  Settings,
  BookOpen,
  PlugZap,
  User,
  FileBarChart,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
  { name: "Entrevistas", href: "/dashboard/entrevistas", icon: FileText },
  { name: "PCD", href: "/dashboard/pcd", icon: FolderTree },
  { name: "TTD", href: "/dashboard/ttd", icon: Clock },
  { name: "Ciclo de Vida", href: "/dashboard/ciclo-vida", icon: RotateCcw },
  { name: "Governança", href: "/dashboard/governanca", icon: Shield },
  { name: "Integração", href: "/dashboard/integracao", icon: PlugZap },
  { name: "Dados & Migração", href: "/dashboard/dados-migracao", icon: Database },
  { name: "Relatórios", href: "/dashboard/relatorios", icon: FileBarChart },
];

const secondaryNav = [
  { name: "Base de Conhecimento", href: "/dashboard/conhecimento", icon: BookOpen },
  { name: "Perfil", href: "/dashboard/perfil", icon: User },
  { name: "Administração", href: "/dashboard/admin", icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 flex-col border-r border-secondary/20 bg-secondary text-secondary-foreground" aria-label="Navegação lateral">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-secondary-foreground/15 bg-secondary px-5">
        <Image
          src="/branding/hw1-logo-wht.svg"
          alt="HW1"
          width={72}
          height={30}
          priority
        />
        <span className="text-xs font-semibold text-secondary-foreground/80">
          Apoio Arquivístico
        </span>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Menu principal">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-secondary-foreground/65">
          Módulos
        </p>
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-secondary-foreground/80 hover:bg-secondary-foreground/10 hover:text-secondary-foreground"
              )}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.name}
            </Link>
          );
        })}

        <div className="my-4 border-t border-secondary-foreground/15" />

        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-secondary-foreground/65">
          Sistema
        </p>
        {secondaryNav.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-secondary-foreground/80 hover:bg-secondary-foreground/10 hover:text-secondary-foreground"
              )}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-secondary-foreground/15 p-4">
        <p className="text-xs text-secondary-foreground/65 text-center">v0.1.0 — Sprint 0</p>
      </div>
    </aside>
  );
}
