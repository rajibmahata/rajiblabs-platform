import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import "../../styles/admin.css";
import { logout, me } from "../../services/auth";
import { api } from "../../services/api";

interface NavEntry { to: string; label: string; icon: string; exact?: boolean; badge?: string | number; dot?: boolean }

const NAV: { label: string; items: NavEntry[] }[] = [
  { label: "Overview", items: [
    { to: "/admin", label: "Dashboard", icon: "fas fa-gauge-high", exact: true },
    { to: "/admin/ai-workbench", label: "AI Proposal Studio", icon: "fas fa-wand-magic-sparkles" },
    { to: "/admin/logs", label: "System Logs", icon: "fas fa-wave-square" },
  ]},
  { label: "Content", items: [
    { to: "/admin/resume", label: "Resume", icon: "fas fa-file-lines" },
    { to: "/admin/portfolio", label: "Portfolio", icon: "fas fa-briefcase" },
    { to: "/admin/github", label: "GitHub Projects", icon: "fab fa-github" },
    { to: "/admin/products", label: "Products", icon: "fas fa-cube" },
  ]},
  { label: "Engagement", items: [
    { to: "/admin/leads", label: "Leads", icon: "fas fa-user-plus" },
  ]},
  { label: "Intelligence", items: [
    { to: "/admin/knowledge", label: "Knowledge Base", icon: "fas fa-brain" },
    { to: "/admin/agents", label: "AI Agents", icon: "fas fa-robot" },
  ]},
  { label: "Localization", items: [
    { to: "/admin/languages", label: "Languages", icon: "fas fa-language" },
    { to: "/admin/translations", label: "Translations", icon: "fas fa-comments" },
  ]},
  { label: "Site", items: [
    { to: "/admin/profile", label: "Professional Profile", icon: "fas fa-id-badge" },
    { to: "/admin/content", label: "Website Content", icon: "fas fa-globe" },
    { to: "/admin/settings", label: "Settings", icon: "fas fa-gear" },
  ]},
];
const FLAT = NAV.flatMap((g) => g.items);

export default function AdminLayout() {
  const nav2 = useNavigate();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [query, setQuery] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [notifs, setNotifs] = useState<{ title?: string; message?: string; created_at?: string; is_read?: boolean }[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [toastMsg, setToastMsg] = useState<{ title: string; msg: string } | null>(null);
  const toastTimer = useRef<number | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);

  const showToast = (title: string, msg: string) => {
    setToastMsg({ title, msg });
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToastMsg(null), 3500);
  };

  useEffect(() => {
    let meta = document.querySelector('meta[name="robots"]') as HTMLMetaElement | null;
    const prev = meta?.content ?? null;
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "robots";
      document.head.appendChild(meta);
    }
    meta.content = "noindex, nofollow";
    const onToast = (e: Event) => {
      const d = (e as CustomEvent).detail;
      showToast(d.title || "Done", d.msg || "");
    };
    window.addEventListener("rla-toast", onToast);
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    me().then((u) => setEmail(u.username)).catch(() => {});
    api.get<{ title?: string; message?: string; created_at?: string; is_read?: boolean }[]>("/api/admin/notifications")
      .then((n) => setNotifs(Array.isArray(n) ? n : [])).catch(() => {});
    return () => {
      if (meta) meta.content = prev ?? "index, follow";
      window.removeEventListener("rla-toast", onToast);
      document.removeEventListener("keydown", onKey);
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    };
  }, []);

  const unread = notifs.filter((n) => !n.is_read).length;
  const results = query.trim()
    ? FLAT.filter((n) => n.label.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 7)
    : [];

  const doSync = async () => {
    if (syncing) return;
    setSyncing(true);
    showToast("Sync started", "pulling latest GitHub repositories…");
    try {
      const r = await api.post<{ added?: number; updated?: number; found?: number }>("/api/admin/github/sync");
      const found = r.found ?? r.added ?? 0;
      showToast("Sync complete", `${found} repositor${found === 1 ? "y" : "ies"} found.`);
    } catch (e) {
      showToast("Sync failed", String(e instanceof Error ? e.message : e).slice(0, 120));
    } finally {
      setSyncing(false);
    }
  };
  const doLogout = async () => { await logout().catch(() => {}); nav2("/admin/login"); };
  const initials = (email || "RM").replace(/[^a-zA-Z]/g, "").slice(0, 2).toUpperCase() || "RM";

  return (
    <div className="rl-admin">
      <div className="rla-app">
        <aside className={`rla-sidebar${open ? " open" : ""}`}>
          <div className="rla-brand">
            <span className="rla-brand-mark"><i className="fas fa-microchip" /></span>
            <div className="rla-brand-name">Rajib<em>Labs</em> Admin</div>
            <span className="rla-brand-sub"><i className="fas fa-lock" /> SECURE</span>
          </div>
          <nav className="rla-nav">
            {NAV.map((g) => (
              <div key={g.label}>
                <div className="rla-nav-label">{g.label}</div>
                {g.items.map((n) => (
                  <NavLink key={n.to} to={n.to} end={n.exact}
                    onClick={() => setOpen(false)}
                    className={({ isActive }) => `rla-nav-item${isActive ? " active" : ""}`}>
                    <i className={n.icon} /> {n.label}
                    {n.badge != null && <span className="rla-nav-badge">{n.badge}</span>}
                    {n.dot && <span className="rla-nav-badge dot" />}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
          <div className="rla-sidebar-foot">
            <div className="rla-side-user">
              <span className="rla-avatar">{initials}</span>
              <div><b>{email ? email.split("@")[0] : "Admin"}</b><span>Administrator</span></div>
            </div>
            <div className="rla-side-links">
              <Link to="/" className="back"><i className="fas fa-arrow-left" /> Back to Site</Link>
              <button onClick={() => void doLogout()}><i className="fas fa-right-from-bracket" /> Logout</button>
            </div>
          </div>
        </aside>
        <div className={`rla-overlay${open ? " show" : ""}`} onClick={() => setOpen(false)} />

        <div className="rla-main">
          <header className="rla-topbar">
            <button className="rla-hamburger" onClick={() => setOpen((o) => !o)} aria-label="Toggle menu">
              <i className="fas fa-bars" />
            </button>
            <div className="rla-search">
              <i className="fas fa-magnifying-glass" />
              <input ref={searchRef} value={query} onChange={(e) => { setQuery(e.target.value); setShowResults(true); }}
                onKeyDown={(e) => { if (e.key === "Enter" && results.length) { nav2(results[0].to); setShowResults(false); setQuery(""); } }}
                onBlur={() => window.setTimeout(() => setShowResults(false), 150)}
                placeholder="Search admin sections…" aria-label="Search admin sections" />
              <kbd>⌘K</kbd>
              {showResults && results.length > 0 && (
                <div className="rla-search-results">
                  {results.map((r) => (
                    <Link key={r.to} to={r.to} onClick={() => { setShowResults(false); setQuery(""); }}>
                      <i className={r.icon} /> {r.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
            <div className="rla-topbar-right">
              <div style={{ position: "relative" }}>
                <button className="rla-icon-btn" title="Notifications" onClick={() => setShowNotifs((s) => !s)}>
                  <i className="fas fa-bell" />{unread > 0 && <span className="notif">{unread}</span>}
                </button>
                {showNotifs && (
                  <div className="rla-notif-drop">
                    {notifs.length === 0 && <div className="row"><span>No notifications.</span></div>}
                    {notifs.slice(0, 10).map((n, i) => (
                      <div className="row" key={i}>
                        <b>{n.title || "Notification"}</b>
                        <p style={{ margin: "2px 0" }}>{n.message || ""}</p>
                        <span>{n.created_at ? new Date(n.created_at).toLocaleString() : ""}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button className="rla-topbar-sync" onClick={() => void doSync()} disabled={syncing}>
                <i className={`fas fa-rotate${syncing ? " fa-spin" : ""}`} /> <span>Sync GitHub Now</span>
              </button>
            </div>
          </header>
          <main className="rla-content"><Outlet /></main>
        </div>
      </div>
      <div className={`rla-toast${toastMsg ? " show" : ""}`}>
        <i className="fas fa-circle-check" />
        <span>{toastMsg && <><b>{toastMsg.title}</b> — {toastMsg.msg}</>}</span>
      </div>
    </div>
  );
}
