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
import LeadsManage from "./pages/admin/LeadsManage";
import KnowledgeManage from "./pages/admin/KnowledgeManage";
import LanguagesManage from "./pages/admin/LanguagesManage";
import TranslationsManage from "./pages/admin/TranslationsManage";
import AgentsManage from "./pages/admin/AgentsManage";
import Workbench from "./pages/admin/Workbench";
import LogsManage from "./pages/admin/LogsManage";
import Settings from "./pages/admin/Settings";
import AdminLayout from "./components/admin/AdminLayout";
import Markdown from "./components/Markdown";
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
    name?: string; title?: string; short_description?: string; shortDescription?: string; description?: string;
    full_description?: string; problem?: string; solution?: string; business_value?: string;
    features?: string[]; architecture?: string; technologies?: string[]; techStack?: string[];
    tags?: string[];
    github_url?: string | null; GitHubUrl?: string; live_url?: string | null; LiveUrl?: string;
    liveUrl?: string | null; demo_url?: string | null; docsUrl?: string | null; docs_url?: string | null;
    ctaText?: string | null; cta_text?: string | null; ctaUrl?: string | null; cta_url?: string | null;
    video_url?: string | null; videoEmbedUrl?: string | null;
    featured_image?: string | null; featuredImage?: string | null;
    logoUrl?: string | null; screenshots?: string[]; gallery?: string[];
    seoTitle?: string | null; seo_title?: string | null;
    status?: string;
  };
  const title = d?.name ?? d?.title ?? slug;
  const techs = d?.technologies ?? d?.techStack ?? [];
  const tags = d?.tags ?? [];
  const gh = d?.github_url ?? d?.GitHubUrl ?? null;
  const live = d?.liveUrl ?? d?.live_url ?? d?.LiveUrl ?? d?.demo_url ?? null;
  const docs = d?.docsUrl ?? d?.docs_url ?? null;
  const ctaUrl = d?.ctaUrl ?? d?.cta_url ?? null;
  const ctaText = d?.ctaText ?? d?.cta_text ?? null;
  const heroImg = d?.featuredImage ?? d?.featured_image ?? d?.logoUrl ?? null;
  const gallery = d?.gallery ?? d?.screenshots ?? [];
  const embed = d?.videoEmbedUrl ?? (d?.video_url ? d.video_url.replace("youtu.be/", "www.youtube.com/embed/").split("?")[0] : null);
  const seoTitle = d?.seoTitle ?? d?.seo_title ?? null;
  useEffect(() => { if (seoTitle) document.title = seoTitle; }, [seoTitle]);
  return (
    <div className="min-h-screen p-6 md:p-12" style={{ background: "var(--c-bg-primary)", color: "var(--c-text-primary)" }}>
      <div className="max-w-3xl mx-auto">
        <a href="/" className="text-sm" style={{ color: "var(--c-text-secondary)" }}>← Home</a>
        <p className="mt-4 text-xs tracking-widest uppercase" style={{ color: "var(--c-accent-gold)", fontFamily: "JetBrains Mono, monospace" }}>{kind === "portfolio" ? "Portfolio" : "Product"}</p>
        <h1 className="text-3xl md:text-4xl font-bold mt-1" style={{ fontFamily: "Fraunces, serif" }}>{title}</h1>
        {(d?.short_description || d?.shortDescription || d?.description) && <p className="mt-3" style={{ color: "var(--c-text-secondary)" }}>{d.short_description ?? d.shortDescription ?? ""}</p>}
        {!!tags.length && <p className="mt-2 text-xs" style={{ color: "var(--c-text-muted)" }}>{tags.map((t) => `#${t}`).join("  ")}</p>}
        {heroImg && <img src={heroImg} alt={`${title} screenshot`} loading="lazy" className="mt-6 rounded-xl w-full" />}
        {!!gallery.length && (
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
            {gallery.filter((g) => g !== heroImg).map((g) => <img key={g} src={g} alt={`${title} gallery`} loading="lazy" style={{ width: 160, height: 110, objectFit: "cover", borderRadius: 10, flexShrink: 0 }} />)}
          </div>
        )}
        {embed && (
          <div className="mt-6 aspect-video">
            <iframe src={embed} title={`${title} demo`} className="w-full h-full rounded-xl" loading="lazy" allowFullScreen />
          </div>
        )}
        {(d?.description || d?.full_description) && <div className="mt-4 text-sm" style={{ color: "var(--c-text-secondary)" }}><Markdown text={d.description ?? d.full_description ?? ""} /></div>}
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
          {docs ? <a href={docs} target="_blank" rel="noopener noreferrer" className="px-5 py-2.5 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }}>Documentation ↗</a> : null}
          {ctaUrl ? <a href={ctaUrl} target="_blank" rel="noopener noreferrer" className="px-5 py-2.5 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }}>{ctaText || "Learn more"} ↗</a>
            : <a href="/#contact" className="px-5 py-2.5 rounded-full text-sm border" style={{ borderColor: "var(--c-border)" }}>Request Quote</a>}
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
          <Route path="leads" element={<LeadsManage />} />
          <Route path="knowledge" element={<KnowledgeManage />} />
          <Route path="agents" element={<AgentsManage />} />
          <Route path="ai-workbench" element={<Workbench />} />
          <Route path="ai-workbench/history" element={<Workbench initialView="history" />} />
          <Route path="languages" element={<LanguagesManage />} />
          <Route path="translations" element={<TranslationsManage />} />
          <Route path="logs" element={<LogsManage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
