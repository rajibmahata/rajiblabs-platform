import { api } from "./api";

// New FastAPI paths first (/api/admin/auth/*), fallback to legacy .NET paths (/api/admin/*).
async function tryPaths<T>(paths: string[], body?: unknown, method: "GET" | "POST" = "POST"): Promise<T> {
  let lastErr: unknown = null;
  for (const p of paths) {
    try {
      return method === "GET" ? await api.get<T>(p) : await api.post<T>(p, body);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error("Auth failed");
}

export async function login(email: string, password: string) {
  const r = await tryPaths<{ access_token?: string; token?: string; email?: string; username?: string }>(
    ["/api/admin/auth/login", "/api/admin/login"], { email, username: email, password });
  return { token: r.access_token ?? r.token ?? "", username: r.email ?? r.username ?? email };
}
export async function logout() {
  try { await api.post("/api/admin/auth/logout"); } catch { await api.post("/api/admin/logout"); }
}
export async function me() {
  const r = await tryPaths<{ email?: string; username?: string }>(
    ["/api/admin/auth/me", "/api/admin/me"], undefined, "GET");
  return { username: r.email ?? r.username ?? "" };
}
