import { createContext } from "react";

export const SidebarContext = createContext<{
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
} | null>(null);
