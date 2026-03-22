import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden" role="application" aria-label="Sistema de apoio arquivístico">
      <AppSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto bg-background bg-[radial-gradient(circle_at_top_right,rgba(236,9,146,0.10),transparent_45%),radial-gradient(circle_at_bottom_left,rgba(0,178,168,0.14),transparent_40%)] p-6"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
