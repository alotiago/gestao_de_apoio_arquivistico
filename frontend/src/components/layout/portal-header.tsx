"use client";

import Image from "next/image";
import { clearAuthCookies } from "@/lib/auth-cookies";

export function PortalHeader() {
  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    clearAuthCookies();
    window.location.href = "/login";
  }

  return (
    <header
      className="flex h-16 items-center justify-between border-b border-primary/20 bg-[linear-gradient(90deg,rgba(255,255,255,0.98),rgba(255,255,255,0.92),rgba(236,9,146,0.08))] px-6"
      role="banner"
    >
      <div className="flex items-center gap-3">
        <Image
          src="/branding/hw1-logo-wht.svg"
          alt="HW1"
          width={72}
          height={30}
          priority
          className="rounded bg-secondary/90 px-2 py-1"
        />
        <span className="text-sm font-semibold text-foreground">
          Portal do Cliente
        </span>
      </div>

      <button
        type="button"
        onClick={handleLogout}
        className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
      >
        Sair
      </button>
    </header>
  );
}
