import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "Gestão de Apoio Arquivístico",
  description:
    "Sistema integrado para gestão documental com suporte a entrevistas assistidas, plano de classificação (PCD), tabela de temporalidade (TTD) e ciclo de vida documental.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">
        <a
          href="#main-content"
          className="sr-only z-50 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
        >
          Pular para o conteúdo principal
        </a>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
