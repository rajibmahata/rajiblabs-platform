import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../../styles/admin.css";
import { login } from "../../services/auth";

export default function Login() {
  const nav = useNavigate();
  const [u, setU] = useState(""); const [p, setP] = useState(""); const [err, setErr] = useState(""); const [loading, setLoading] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try { await login(u, p); nav("/admin"); } catch (e: unknown) { setErr(e instanceof Error ? e.message : "Login failed"); } finally { setLoading(false); }
  };
  return (
    <div className="rl-admin">
      <div className="rla-auth-wrap">
        <form onSubmit={submit} className="rla-auth-card">
          <div className="rla-auth-brand">
            <span className="rla-brand-mark"><i className="fas fa-microchip" /></span>
            <div>
              <div className="rla-brand-name">Rajib<em>Labs</em> Admin</div>
            </div>
            <span className="rla-brand-sub"><i className="fas fa-lock" /> SECURE</span>
          </div>
          <h1>Welcome back</h1>
          <p className="sub">Sign in for secure access to the RajibLabs CMS.</p>
          <div className="rla-field">
            <label htmlFor="rla-email">Email</label>
            <input id="rla-email" type="email" value={u} onChange={e => setU(e.target.value)} required
              autoComplete="username" placeholder="rajibmahata143@gmail.com" />
          </div>
          <div className="rla-field">
            <label htmlFor="rla-pass">Password</label>
            <input id="rla-pass" type="password" value={p} onChange={e => setP(e.target.value)} required
              autoComplete="current-password" placeholder="••••••••" />
          </div>
          {err && <div className="rla-auth-error" role="alert"><i className="fas fa-circle-exclamation" /> {err}</div>}
          <button disabled={loading} className="rla-auth-submit">
            {loading ? <><i className="fas fa-circle-notch fa-spin" /> Signing in…</> : <><i className="fas fa-right-to-bracket" /> Sign in</>}
          </button>
          <p className="rla-auth-hint">Use rajibmahata143@gmail.com or rajibmahata143@outlook.com<br />Password via <code>ADMIN_INITIAL_PASSWORD</code> env</p>
          <Link to="/" className="rla-auth-back"><i className="fas fa-arrow-left" /> Back to site</Link>
        </form>
      </div>
    </div>
  );
}
