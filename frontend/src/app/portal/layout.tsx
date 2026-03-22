import { PortalHeader } from "@/components/layout/portal-header";

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col" role="application" aria-label="Portal do Cliente">
      <PortalHeader />
      <main
        id="main-content"
        tabIndex={-1}
        className="flex-1 bg-background bg-[radial-gradient(circle_at_top_right,rgba(236,9,146,0.07),transparent_50%),radial-gradient(circle_at_bottom_left,rgba(0,178,168,0.10),transparent_45%)] p-6"
      >
        {children}
      </main>
      <footer className="border-t border-border px-6 py-3 text-center text-xs text-muted-foreground">
        HW1 — Gestão de Apoio Arquivístico · Portal do Cliente
      </footer>
    </div>
  );
}
