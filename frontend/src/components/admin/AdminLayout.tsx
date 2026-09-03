import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../../services/auth";

const nav = [
  { to: "/admin", label: "Dashboard", exact: true },
  { to: "/admin/resume", label: "Resume" },
  { to: "/admin/portfolio", label: "Portfolio" },
  { to: "/admin/github", label: "GitHub Projects" },
  { to: "/admin/products", label: "Products" },
  { to: "/admin/profile", label: "Professional Profile" },
  { to: "/admin/content", label: "Website Content" },
  { to: "/admin/settings", label: "Settings" },
];

export default function AdminLayout() {
  const nav2 = useNavigate();
  useEffect(() => {
    let meta = document.querySelector('meta[name="robots"]') as HTMLMetaElement | null;
    const prev = meta?.content ?? null;
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "robots";
      document.head.appendChild(meta);
    }
    meta.content = "noindex, nofollow";
    return () => { if (meta) meta.content = prev ?? "index, follow"; };
  }, []);
  return (
    <div className="min-h-screen flex" style={{ background: "var(--c-bg-primary)", color: "var(--c-text-primary)" }}>
      <aside className="w-64 shrink-0 border-r hidden md:flex flex-col" style={{ background: "#090e1b", borderColor: "var(--c-border)" }}>
        <div className="p-6 border-b" style={{ borderColor: "var(--c-border)" }}>
          <div className="font-bold" style={{ fontFamily: "Fraunces, serif" }}>Rajib<span style={{ color: "#eec04e", fontWeight: 400 }}>Labs</span> Admin</div>
          <div className="text-xs mt-1" style={{ color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>CMS · Secure</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(n => (
            <NavLink key={n.to} to={n.to} end={n.exact} className={({ isActive }) => `block px-3 py-2 rounded-lg text-sm ${isActive ? "bg-white/10 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"}`}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t" style={{ borderColor: "var(--c-border)" }}>
          <button onClick={async () => { await logout(); nav2("/admin/login"); }} className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-white/5" style={{ color: "var(--c-text-secondary)" }}>Logout</button>
          <a href="/" className="block px-3 py-2 text-xs mt-2" style={{ color: "var(--c-text-muted)" }}>← Back to site</a>
        </div>
      </aside>
      <div className="flex-1 min-w-0">
        <div className="md:hidden flex items-center justify-between p-4 border-b" style={{ background: "#090e1b", borderColor: "var(--c-border)" }}>
          <span style={{ fontFamily: "Fraunces, serif", fontWeight: 700 }}>RajibLabs Admin</span>
          <button onClick={async () => { await logout(); nav2("/admin/login"); }} className="text-sm px-3 py-1 rounded-full border" style={{ borderColor: "var(--c-border)" }}>Logout</button>
        </div>
        <div className="md:hidden flex gap-2 overflow-x-auto p-3 border-b no-scrollbar" style={{ borderColor: "var(--c-border)" }}>
          {nav.map(n => <NavLink key={n.to} to={n.to} end={n.exact} className={({ isActive }) => `whitespace-nowrap px-3 py-1.5 rounded-full text-xs border ${isActive ? "bg-white text-black" : "text-slate-400"}`}>{n.label}</NavLink>)}
        </div>
        <main className="p-4 md:p-8 max-w-6xl mx-auto"><Outlet /></main>
      </div>
    </div>
  );
}
