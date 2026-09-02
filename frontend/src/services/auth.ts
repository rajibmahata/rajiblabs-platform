import { api } from "./api";

export async function login(username: string, password: string) {
  return api.post<{ token: string; username: string }>("/api/admin/login", { username, password });
}
export async function logout() { return api.post("/api/admin/logout"); }
export async function me() { return api.get<{ username: string }>("/api/admin/me"); }
