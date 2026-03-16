import { create } from "zustand";
import api from "@/lib/api";

interface User {
  id: string;
  email: string;
  nome: string;
  role: string;
  departamento?: string;
  unidade?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const { data } = await api.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    localStorage.setItem("access_token", data.access_token);
    if (data.refresh_token) {
      localStorage.setItem("refresh_token", data.refresh_token);
    }

    // Buscar dados do usuário
    const userRes = await api.get("/auth/me");
    set({ user: userRes.data, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false, isLoading: false });
    window.location.href = "/login";
  },

  fetchUser: async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        set({ isLoading: false });
        return;
      }
      const { data } = await api.get("/auth/me");
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("access_token");
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
