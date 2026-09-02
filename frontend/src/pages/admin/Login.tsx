import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../../services/auth";

export default function Login() {
  const nav = useNavigate();
  const [u, setU] = useState(""); const [p, setP] = useState(""); const [err, setErr] = useState(""); const [loading, setLoading] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try { await login(u, p); nav("/admin"); } catch (e: unknown) { setErr(e instanceof Error ? e.message : "Login failed"); } finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: "var(--c-bg-primary)" }}>
      <form onSubmit={submit} className="w-full max-w-md p-8 rounded-2xl border" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
        <h1 className="text-2xl font-bold mb-1" style={{ fontFamily: "Fraunces, serif" }}>Admin Login</h1>
        <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>Secure access to RajibLabs CMS. Credentials never leave the server.</p>
        <label className="block text-xs mb-1" style={{ color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>EMAIL</label>
        <input type="email" value={u} onChange={e => setU(e.target.value)} required className="w-full px-3 py-2 rounded-lg border mb-4" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)", color: "var(--c-text-primary)" }} placeholder="rajibmahata143@gmail.com" />
        <label className="block text-xs mb-1" style={{ color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>PASSWORD</label>
        <input type="password" value={p} onChange={e => setP(e.target.value)} required className="w-full px-3 py-2 rounded-lg border mb-4" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)", color: "var(--c-text-primary)" }} placeholder="••••••••" />
        {err && <div className="text-sm mb-3 p-2 rounded" style={{ background: "rgba(239,68,68,0.12)", color: "#f87171" }}>{err}</div>}
        <button disabled={loading} className="w-full py-2.5 rounded-full font-medium text-white" style={{ background: "#1547be" }}>{loading ? "Signing in…" : "Sign in"}</button>
        <p className="text-xs mt-4 text-center" style={{ color: "var(--c-text-muted)" }}>Use rajibmahata143@gmail.com or rajibmahata143@outlook.com · Password via ADMIN_INITIAL_PASSWORD env</p>
      </form>
    </div>
  );
}
