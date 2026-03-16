"use client";

import { Bell, Search, User } from "lucide-react";

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-6" role="banner">
      {/* Search */}
      <form
        role="search"
        aria-label="Busca no sistema"
        onSubmit={(event) => event.preventDefault()}
        className="flex items-center gap-2 rounded-lg border bg-muted px-3 py-2 w-96"
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
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Notificações"
          className="relative rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <Bell className="h-5 w-5" aria-hidden="true" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" aria-hidden="true" />
        </button>

        <div className="h-6 w-px bg-border" />

        <button
          type="button"
          aria-label="Abrir menu de usuário"
          className="flex items-center gap-2 rounded-lg p-2 text-foreground hover:bg-muted transition-colors"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
            <User className="h-4 w-4 text-primary" aria-hidden="true" />
          </div>
          <div className="hidden text-left sm:block">
            <p className="text-sm font-medium">Usuário</p>
            <p className="text-xs text-muted-foreground">Arquivista</p>
          </div>
        </button>
      </div>
    </header>
  );
}
