import { api } from "./api";

// FastAPI is the only backend (the legacy .NET API was removed).
export async function login(email: string, password: string) {
  const r = await api.post<{ access_token: string; email: string }>(
    "/api/admin/auth/login", { email, password });
  return { token: r.access_token, username: r.email };
}
export async function logout() {
  await api.post("/api/admin/auth/logout");
}
export async function me() {
  const r = await api.get<{ email: string }>("/api/admin/auth/me");
  return { username: r.email };
}
