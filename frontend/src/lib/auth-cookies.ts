import { destroyCookie, setCookie } from "nookies";

export function setAuthCookies(accessToken: string, refreshToken?: string) {
  // Define o cookie do access_token (válido para todas as rotas, httpOnly false para acesso client-side)
  setCookie(null, "access_token", accessToken, {
    path: "/",
    maxAge: 60 * 60, // 1 hora
    sameSite: "lax",
    secure: true,
  });
  if (refreshToken) {
    setCookie(null, "refresh_token", refreshToken, {
      path: "/",
      maxAge: 7 * 24 * 60 * 60, // 7 dias
      sameSite: "lax",
      secure: true,
    });
  }
}

export function clearAuthCookies() {
  destroyCookie(null, "access_token", { path: "/" });
  destroyCookie(null, "refresh_token", { path: "/" });
}
