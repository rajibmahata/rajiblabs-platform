import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/admin/Login";
import Dashboard from "./pages/admin/Dashboard";
import ResumeManage from "./pages/admin/ResumeManage";
import PortfolioManage from "./pages/admin/PortfolioManage";
import GitHubManage from "./pages/admin/GitHubManage";
import ProductsManage from "./pages/admin/ProductsManage";
import ProfileManage from "./pages/admin/ProfileManage";
import ContentManage from "./pages/admin/ContentManage";
import Settings from "./pages/admin/Settings";
import AdminLayout from "./components/admin/AdminLayout";
import ProtectedRoute from "./components/admin/ProtectedRoute";

function DetailPage({ kind }: { kind: "portfolio" | "product" }) {
  const slug = window.location.pathname.split("/").pop() || "";
  const [data, setData] = useState<unknown>(null);
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
        const tryUrls = kind === "portfolio"
          ? [`${base}/api/public/projects/${slug}`, `${base}/api/portfolio/${slug}`]
          : [`${base}/api/public/projects/${slug}`, `${base}/api/products/${slug}`];
        for (const u of tryUrls) {
          try {
            const r = await fetch(u);
            if (r.ok) {
              const j = await r.json();
              if (alive) setData(j);
              document.title = `${(j as { name?: string; title?: string }).name ?? (j as { title?: string }).title ?? slug} | RajibLabs`;
              return;
            }
          } catch { /* try next */ }
        }
      } catch { /* fallback below */ }
    })();
    return () => { alive = false; };
  }, [slug, kind]);
  const d = data as null | {
    name?: string; title?: string; short_description?: string; description?: string;
    full_description?: string; problem?: string; solution?: string; business_value?: string;
    features?: string[]; architecture?: string; technologies?: string[]; techStack?: string[];
    github_url?: string | null; GitHubUrl?: string; live_url?: string | null; LiveUrl?: string;
    demo_url?: string | null; video_url?: string | null; featured_image?: string | null;
    gallery?: string[]; status?: string;
  };
  const title = d?.name ?? d?.title ?? slug;
  const techs = d?.technologies ?? d?.techStack ?? [];
  const gh = d?.github_url ?? d?.GitHubUrl ?? null;
  const live = d?.live_url ?? d?.LiveUrl ?? d?.demo_url ?? null;
  return (
    <div className="min-h-screen p-6 md:p-12" style={{ background: "var(--c-bg-primary)", color: "var(--c-text-primary)" }}>
      <div className="max-w-3xl mx-auto">
        <a href="/" className="text-sm" style={{ color: "var(--c-text-secondary)" }}>← Home</a>
        <p className="mt-4 text-xs tracking-widest uppercase" style={{ color: "var(--c-accent-gold)", fontFamily: "JetBrains Mono, monospace" }}>{kind === "portfolio" ? "Portfolio" : "Product"}</p>
        <h1 className="text-3xl md:text-4xl font-bold mt-1" style={{ fontFamily: "Fraunces, serif" }}>{title}</h1>
        {(d?.short_description || d?.description) && <p className="mt-3" style={{ color: "var(--c-text-secondary)" }}>{d.short_description ?? d.description}</p>}
        {d?.featured_image && <img src={d.featured_image} alt={`${title} screenshot`} loading="lazy" className="mt-6 rounded-xl w-full" />}
        {d?.video_url && (
          <div className="mt-6 aspect-video">
            <iframe src={d.video_url.replace("youtu.be/", "www.youtube.com/embed/").split("?")[0]} title={`${title} demo`} className="w-full h-full rounded-xl" loading="lazy" allowFullScreen />
          </div>
        )}
        {d?.problem && (<><h2 className="text-xl font-semibold mt-8">Problem</h2><p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>{d.problem}</p></>)}
        {d?.solution && (<><h2 className="text-xl font-semibold mt-6">Solution</h2><p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>{d.solution}</p></>)}
        {!!d?.features?.length && (<><h2 className="text-xl font-semibold mt-6">Features</h2><ul className="list-disc ml-5 mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>{d.features.map((f) => <li key={f}>{f}</li>)}</ul></>)}
        {d?.architecture && (<><h2 className="text-xl font-semibold mt-6">Architecture</h2><p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>{d.architecture}</p></>)}
        {!!techs.length && (<><h2 className="text-xl font-semibold mt-6">Technology</h2><p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>{techs.join(" · ")}</p></>)}
        {d?.business_value && (<><h2 className="text-xl font-semibold mt-6">Business value</h2><p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>{d.business_value}</p></>)}
        <div className="flex flex-wrap gap-3 mt-8">
          {live ? <a href={live} target="_blank" rel="noopener noreferrer" className="px-5 py-2.5 rounded-full text-sm text-white" style={{ background: "#1547be" }}>Live Website ↗</a> : null}
          {gh ? <a href={gh} target="_blank" rel="noopener noreferrer" className="px-5 py-2.5 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }} aria-label="View GitHub repository">GitHub Repository ↗</a>
            : <span className="px-5 py-2.5 rounded-full text-sm border" style={{ borderColor: "var(--c-border)", color: "var(--c-text-muted)" }}>GitHub repository unavailable</span>}
          <a href="/#contact" className="px-5 py-2.5 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }}>Request Quote</a>
        </div>
        {!d && <p className="mt-6 text-sm" style={{ color: "var(--c-text-muted)" }}>Loading CMS content… (falls back to homepage sections if API is offline)</p>}
      </div>
    </div>
  );
}
const PortfolioDetail = () => <DetailPage kind="portfolio" />;
const ProductDetail = () => <DetailPage kind="product" />;

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/portfolio/:slug" element={<PortfolioDetail />} />
        <Route path="/products/:slug" element={<ProductDetail />} />
        <Route path="/admin/login" element={<Login />} />
        <Route
          path="/admin"
          element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}
        >
          <Route index element={<Dashboard />} />
          <Route path="resume" element={<ResumeManage />} />
          <Route path="portfolio" element={<PortfolioManage />} />
          <Route path="github" element={<GitHubManage />} />
          <Route path="products" element={<ProductsManage />} />
          <Route path="profile" element={<ProfileManage />} />
          <Route path="content" element={<ContentManage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
