"use client";

import { useContext } from "react";
import { Bell, Menu, Search, User, X } from "lucide-react";
import { clearAuthCookies } from "@/lib/auth-cookies";
import { SidebarContext } from "@/lib/sidebar-context";

export function Header() {
  const sidebarContext = useContext(SidebarContext);
  const sidebarOpen = sidebarContext?.sidebarOpen ?? false;
  const setSidebarOpen = sidebarContext?.setSidebarOpen;

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    clearAuthCookies();
    window.location.href = "/login";
  }

  return (
    <header
      className="flex h-16 items-center justify-between border-b border-primary/20 bg-[linear-gradient(90deg,rgba(255,255,255,0.98),rgba(255,255,255,0.92),rgba(236,9,146,0.08))] px-4 sm:px-6"
      role="banner"
    >
      {/* Hamburger (mobile) */}
      <button
        onClick={() => setSidebarOpen?.(!sidebarOpen)}
        className="rounded-lg p-2 text-muted-foreground hover:bg-primary/10 hover:text-primary transition sm:hidden"
        aria-label="Abrir menu"
      >
        {sidebarOpen ? (
          <X className="h-5 w-5" />
        ) : (
          <Menu className="h-5 w-5" />
        )}
      </button>

      {/* Search */}
      <form
        role="search"
        aria-label="Busca no sistema"
        onSubmit={(event) => event.preventDefault()}
        className="hidden sm:flex w-96 items-center gap-2 rounded-lg border border-primary/20 bg-white/90 px-3 py-2"
      >
        <Search className="h-4 w-4 text-muted-foreground" />
        <label htmlFor="global-search" className="sr-only">
          Buscar no sistema
        </label>
        <input
          id="global-search"
          type="text"
          placeholder="Buscar roteiros, classes, regras..."
          className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
        />
        <kbd className="hidden rounded border bg-background px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline-block">
          Ctrl+K
        </kbd>
      </form>

      {/* Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
        <button
          type="button"
          aria-label="Notificações"
          className="relative rounded-lg p-2 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary"
        >
          <Bell className="h-5 w-5" aria-hidden="true" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" aria-hidden="true" />
        </button>

        <div className="h-6 w-px bg-primary/25" />

        <div className="flex items-center gap-2 rounded-lg p-2 text-foreground transition-colors hover:bg-primary/10">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
            <User className="h-4 w-4 text-primary" aria-hidden="true" />
          </div>
          <div className="hidden text-left sm:block">
            <p className="text-sm font-medium">Usuário</p>
            <p className="text-xs text-muted-foreground">Arquivista</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-md border border-input bg-background px-2 py-1 text-xs font-medium text-foreground hover:bg-muted"
          >
            Sair
          </button>
        </div>
      </div>
    </header>
  );
}
