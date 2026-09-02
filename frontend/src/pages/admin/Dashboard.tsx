/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function Dashboard() {
  const [data, setData] = useState<any>(null); const [err, setErr] = useState("");
  useEffect(() => { api.get<any>("/api/admin/dashboard").then(setData).catch(e => setErr(String(e))); }, []);
  if (err) return <div className="p-6 text-red-400">{err}</div>;
  if (!data) return <div className="p-6" style={{ color: "var(--c-text-secondary)" }}>Loading dashboard…</div>;
  const cards = [
    { label: "Resume", value: data.resume ? `${data.resume.fileName} v${data.resume.version}` : "No published resume", sub: data.resume ? new Date(data.resume.uploadedAt).toLocaleDateString() : "" },
    { label: "Portfolio", value: `${data.portfolio.published}/${data.portfolio.total} published`, sub: "Featured & draft" },
    { label: "GitHub Repos", value: `${data.github.total} synced`, sub: data.lastSync ? `Last sync ${new Date(data.lastSync.startedAt).toLocaleString()}` : "Never synced" },
    { label: "Products", value: `${data.products.total}`, sub: "Page Flow included" },
  ];
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1" style={{ fontFamily: "Fraunces, serif" }}>Dashboard</h1>
      <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>Overview of portfolio CMS — last content update {data.profileUpdatedAt ? new Date(data.profileUpdatedAt).toLocaleString() : "—"}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(c => (
          <div key={c.label} className="p-5 rounded-xl border" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
            <div className="text-xs mb-1" style={{ color: "var(--c-accent-gold)", fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.08em" }}>{c.label.toUpperCase()}</div>
            <div className="font-semibold" style={{ color: "var(--c-text-primary)" }}>{c.value}</div>
            <div className="text-xs mt-1" style={{ color: "var(--c-text-muted)" }}>{c.sub}</div>
          </div>
        ))}
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <a href="/admin/github" className="px-4 py-2 rounded-full text-sm text-white" style={{ background: "#1547be" }}>Sync GitHub Now →</a>
        <a href="/admin/portfolio" className="px-4 py-2 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }}>Manage Portfolio</a>
        <a href="/" target="_blank" className="px-4 py-2 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }}>View Site ↗</a>
      </div>
    </div>
  );
}
