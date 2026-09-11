/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "./ui";
import { InlineLoader } from "./ui";
import { useAsyncActions } from "./async";
import { toast } from "./toast";
import Markdown from "../Markdown";

export interface CatalogKind {
  kind: "portfolio" | "products";
  title: string;
  nameLabel: string;
  nameKey: "title" | "name";
  statuses: string[];
  showCategory: boolean;
  showProblemSolution: boolean;
  showFeatures: boolean;
  showAiCaps: boolean;
  icon: string;
  iconBg: string;
  iconColor: string;
  publicPath: string;
}

const ORIGINS = ["", "client", "product", "engineering", "exploration"] as const;

const EMPTY_FORM: any = {
  title: "", name: "", slug: "", shortDescription: "", description: "",
  purpose: "", problem: "", solution: "", targetUsers: "", functionalDetails: "", features: "", workflow: "",
  goal: "", objectives: "", userRoles: "",
  role: "", architecture: "", techNotes: "", architectureImage: "", origin: "",
  businessValue: "", challenges: "",
  category: "", status: "draft", featured: false, displayOrder: 0,
  techStack: "", tags: "",
  aiCapabilities: "", cloudCapabilities: "",
  featuredImage: "", gallery: [] as string[],
  videoUrl: "", liveUrl: "", demoUrl: "", githubUrl: "", productUrl: "",
  docsUrl: "", ctaText: "", ctaUrl: "",
  seoTitle: "", seoDescription: "", seoImage: "",
  ragIndexed: true,
};

const toCSV = (v: any): string => Array.isArray(v) ? v.join(", ") : (v || "");
const fromCSV = (s: string): string[] =>
  String(s || "").split(",").map((x) => x.trim()).filter(Boolean);
// Objectives are one-per-line (multi-word items survive; CSV would split them).
const toLines = (v: any): string => Array.isArray(v) ? v.join("\n") : (v || "");
const fromLines = (s: string): string[] =>
  String(s || "").split("\n").map((x) => x.trim()).filter(Boolean);

export default function CatalogManager(cfg: CatalogKind) {
  const base = `/api/admin/${cfg.kind}`;
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [featured, setFeatured] = useState("");
  const [tech, setTech] = useState("");
  const [tag, setTag] = useState("");
  const [sort, setSort] = useState("");
  const [modal, setModal] = useState<"closed" | "create" | "edit" | "view" | "preview">("closed");
  const [form, setForm] = useState<any>({ ...EMPTY_FORM });
  const [editId, setEditId] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const { run, isLoading } = useAsyncActions();
  const uploading = isLoading("upload-featuredImage") ? "featuredImage" : isLoading("upload-gallery") ? "gallery" : null;
  const fileRef = useRef<HTMLInputElement | null>(null);
  const galleryRef = useRef<HTMLInputElement | null>(null);
  const pageSize = 20;

  const load = async (p = page) => {
    const params = new URLSearchParams({ page: String(p), page_size: String(pageSize) });
    if (q.trim()) params.set("q", q.trim());
    if (status) params.set("status", status);
    if (category.trim() && cfg.showCategory) params.set("category", category.trim());
    if (featured) params.set("featured", featured === "yes" ? "true" : "false");
    if (tech.trim()) params.set("tech", tech.trim());
    if (tag.trim()) params.set("tag", tag.trim());
    if (sort) params.set("sort", sort);
    try {
      const r = await api.get<any>(`${base}?${params}`);
      setItems(Array.isArray(r.items) ? r.items : []);
      setTotal(r.total || 0);
    } catch (e: any) { toast("Load failed", String(e.message || e).slice(0, 120)); }
  };
  useEffect(() => { load(1); setPage(1); }, [q, status, category, featured, tech, tag, sort]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { load(page); }, [page]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const openCreate = () => { setForm({ ...EMPTY_FORM }); setEditId(null); setErrors([]); setModal("create"); };
  const openEdit = (item: any) => {
    setForm({
      ...EMPTY_FORM, ...item,
      techStack: toCSV(item.techStack), tags: toCSV(item.tags),
      features: toCSV(item.features),
      objectives: toLines(item.objectives),
      userRoles: toCSV(item.userRoles),
      targetUsers: toCSV(item.targetUsers),
      aiCapabilities: toCSV(item.aiCapabilities), cloudCapabilities: toCSV(item.cloudCapabilities),
      gallery: item.gallery || item.screenshots || [],
      ragIndexed: item.ragIndexed !== false,
    });
    setEditId(item.id); setErrors([]); setModal("edit");
  };
  const openView = (item: any) => { openEdit(item); setModal("view"); };

  const validate = (): string[] => {
    const errs: string[] = [];
    if (!String(form[cfg.nameKey] || "").trim()) errs.push(`${cfg.nameLabel} is required.`);
    if (form.slug && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(form.slug.trim().toLowerCase()))
      errs.push("Slug may only contain lowercase letters, numbers and hyphens.");
    if (form.displayOrder !== "" && isNaN(Number(form.displayOrder))) errs.push("Display order must be a number.");
    for (const [k, label] of [["liveUrl", "Live URL"], ["githubUrl", "GitHub URL"], ["docsUrl", "Docs URL"], ["ctaUrl", "CTA link"], ["productUrl", "Product URL"], ["demoUrl", "Demo URL"], ["architectureImage", "Architecture diagram"]] as const) {
      const v = String(form[k] || "").trim();
      if (v && !/^https?:\/\/.+\..+/.test(v)) errs.push(`${label} must start with http(s)://`);
    }
    if (form.origin && !(ORIGINS as readonly string[]).includes(form.origin)) errs.push("Origin must be client, product, engineering or exploration.");
    return errs;
  };

  const payload = () => {
    const p: any = {
      [cfg.nameKey]: String(form[cfg.nameKey] || "").trim(),
      slug: form.slug.trim().toLowerCase() || undefined,
      shortDescription: form.shortDescription?.trim() || "",
      description: form.description || "",
      purpose: form.purpose?.trim() || "",
      problem: form.problem?.trim() || "",
      solution: form.solution?.trim() || "",
      targetUsers: fromCSV(form.targetUsers),
      functionalDetails: form.functionalDetails || "",
      features: fromCSV(form.features),
      workflow: form.workflow || "",
      goal: form.goal?.trim() || "",
      objectives: fromLines(form.objectives),
      userRoles: fromCSV(form.userRoles),
      role: form.role?.trim() || "",
      architecture: form.architecture || "",
      techNotes: form.techNotes || "",
      architectureImage: form.architectureImage?.trim() || null,
      origin: (ORIGINS as readonly string[]).includes(form.origin) ? form.origin : "",
      businessValue: form.businessValue || "",
      challenges: form.challenges || "",
      category: form.category?.trim() || "",
      status: form.status, featured: !!form.featured,
      displayOrder: Number(form.displayOrder) || 0,
      techStack: fromCSV(form.techStack), tags: fromCSV(form.tags),
      featuredImage: form.featuredImage || null,
      gallery: (form.gallery || []).filter(Boolean),
      videoUrl: form.videoUrl?.trim() || null,
      liveUrl: form.liveUrl?.trim() || null,
      docsUrl: form.docsUrl?.trim() || null,
      ctaText: form.ctaText?.trim() || null,
      ctaUrl: form.ctaUrl?.trim() || null,
      seoTitle: form.seoTitle?.trim() || null,
      seoDescription: form.seoDescription?.trim() || null,
      seoImage: form.seoImage || null,
      ragIndexed: form.ragIndexed !== false,
    };
    if (cfg.kind === "portfolio") {
      Object.assign(p, {
        aiCapabilities: fromCSV(form.aiCapabilities), cloudCapabilities: fromCSV(form.cloudCapabilities),
        demoUrl: form.demoUrl?.trim() || null, gitHubUrl: form.githubUrl?.trim() || null,
        productUrl: form.productUrl?.trim() || null,
      });
    } else {
      Object.assign(p, {
        aiCapabilities: form.aiCapabilities?.trim() || null,
        productUrl: form.productUrl?.trim() || null,
        gitHubUrl: form.githubUrl?.trim() || null,
      });
    }
    return p;
  };

  const save = (stayOpen: boolean) => {
    const errs = validate();
    setErrors(errs);
    if (errs.length) return;
    run("save", async () => {
      const body = payload();
      const saved = editId ? await api.put<any>(`${base}/${editId}`, body) : await api.post<any>(base, body);
      load(page);
      if (stayOpen && saved.id) { setEditId(saved.id); setForm({ ...form, ...saved, techStack: toCSV(saved.techStack), tags: toCSV(saved.tags), features: toCSV(saved.features), aiCapabilities: toCSV(saved.aiCapabilities), cloudCapabilities: toCSV(saved.cloudCapabilities) }); setModal("edit"); }
      else setModal("closed");
      return saved;
    }, { successTitle: "Saved", successMsg: `${form[cfg.nameKey] || cfg.title} saved.`, errorTitle: "Save failed" }).catch(()=>{});
  };

  const toggleStatus = (item: any) => {
    const next = item.status === "published" ? "draft" : "published";
    run(`status-${item.id}`, async () => { await api.patch(`${base}/${item.id}/status`, { status: next }); load(page); }, { successTitle: next === "published" ? "Published" : "Unpublished", successMsg: `${item[cfg.nameKey]} is now ${next}.`, errorTitle: "Update failed" });
  };
  const toggleFeatured = (item: any) => run(`featured-${item.id}`, async () => { await api.patch(`${base}/${item.id}/featured`, { featured: !item.featured }); load(page); }, { successTitle: item.featured ? "Unfeatured" : "Featured", errorTitle: "Update failed" });
  const remove = (item: any) => {
    if (!confirm(`Delete "${item[cfg.nameKey]}"? This removes it and its knowledge vectors.`)) return;
    run(`delete-${item.id}`, async () => { await api.del(`${base}/${item.id}`); load(page); }, { successTitle: "Deleted", errorTitle: "Delete failed" });
  };

  const uploadInto = (file: File | undefined, field: "featuredImage" | "gallery") => {
    if (!file) return;
    run(`upload-${field}`, async () => {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.upload<{ url: string }>(`/api/admin/uploads/image?kind=${cfg.kind}`, fd);
      if (field === "featuredImage") set("featuredImage", r.url);
      else set("gallery", [...(form.gallery || []), r.url]);
      return r;
    }, { successTitle: "Uploaded", errorTitle: "Image upload failed" }).catch(()=>{});
  };
  const removeImage = async (url: string, field: "featuredImage" | "gallery") => {
    try { await api.del(`/api/admin/uploads?path=${encodeURIComponent(url)}`); } catch { /* keep going */ }
    if (field === "featuredImage") set("featuredImage", "");
    else set("gallery", (form.gallery || []).filter((g: string) => g !== url));
  };

  const clearFilters = () => { setQ(""); setStatus(""); setCategory(""); setFeatured(""); setTech(""); setTag(""); setSort(""); setPage(1); load(1); };
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const readOnly = modal === "view";
  const img = (u?: string | null) => (u ? <img src={u} alt="" loading="lazy" style={{ width: 56, height: 42, objectFit: "cover", borderRadius: 8 }} /> : <span className="rla-doc-ic" style={{ background: "var(--rla-cyan-soft)", color: "var(--rla-cyan)" }}><i className={`fas ${cfg.icon}`} /></span>);

  return (
    <div>
      <PageHead title={cfg.title} desc={<>Full content management. Public: <span className="rla-code">{cfg.publicPath}/:slug</span>.</>}
        actions={<button onClick={openCreate} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> Add {cfg.title.slice(0, -1)}</button>} />
      <Panel title="Catalog" sub={`${total} total`}>
        <div className="rla-filter-grid">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search title, description, tags, tech…" className="rla-input" aria-label="Search" />
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="rla-select" aria-label="Status">
            <option value="">all statuses</option>{cfg.statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          {cfg.showCategory && <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Category" className="rla-input" aria-label="Category" />}
          <select value={featured} onChange={(e) => setFeatured(e.target.value)} className="rla-select" aria-label="Featured">
            <option value="">featured: all</option><option value="yes">★ featured</option><option value="no">not featured</option>
          </select>
          <input value={tech} onChange={(e) => setTech(e.target.value)} placeholder="Technology" className="rla-input" aria-label="Technology" />
          <input value={tag} onChange={(e) => setTag(e.target.value)} placeholder="Tag" className="rla-input" aria-label="Tag" />
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="rla-select" aria-label="Sort">
            <option value="">sort: display order</option><option value="title">title A–Z</option><option value="name">name A–Z</option><option value="-updated">recently updated</option><option value="order">display order</option>
          </select>
          <button onClick={clearFilters} className="rla-btn rla-btn-ghost rla-btn-sm">Clear</button>
        </div>
        <div style={{ height: 12 }} />
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Image</th><th>Title</th><th>Short</th><th>Status</th><th>Featured</th><th>Video</th><th>Live</th><th>Updated</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td>{img(p.featuredImage || p.logoUrl || (p.gallery || p.screenshots || [])[0])}</td>
                  <td><div><b>{p[cfg.nameKey]}</b><div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{p.slug}{p.category ? ` · ${p.category}` : ""} · #{p.displayOrder ?? 0}</div></div></td>
                  <td className="text-xs" style={{ maxWidth: 220 }}>{(p.shortDescription || p.description || "—").slice(0, 90)}</td>
                  <td><button onClick={() => toggleStatus(p)} title="Toggle active/inactive" style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}><StatusPill status={p.status} /></button></td>
                  <td><button onClick={() => toggleFeatured(p)} title="Toggle featured" style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem" }}>{p.featured ? "★" : "—"}</button></td>
                  <td>{p.videoEmbedUrl ? "▶" : "—"}</td>
                  <td>{p.liveUrl ? <a href={p.liveUrl} target="_blank" rel="noreferrer">↗</a> : "—"}</td>
                  <td className="text-xs">{p.updatedAt ? new Date(p.updatedAt).toLocaleDateString() : "—"}</td>
                  <td><div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                    <button onClick={() => openView(p)} className="rla-mini-btn" title="View"><i className="fas fa-eye" /></button>
                    <button onClick={() => { openEdit(p); }} className="rla-mini-btn" title="Edit"><i className="fas fa-pen" /></button>
                    <button onClick={() => remove(p)} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && <Empty>No records match. Adjust filters or add one.</Empty>}
        </div>
        <div className="rla-pager">
          <button disabled={page <= 1} onClick={() => { setPage(page - 1); load(page - 1); }} className="rla-btn rla-btn-ghost rla-btn-sm">← Prev</button>
          <span>Page {page} of {totalPages} · {total} records</span>
          <button disabled={page >= totalPages} onClick={() => { setPage(page + 1); load(page + 1); }} className="rla-btn rla-btn-ghost rla-btn-sm">Next →</button>
        </div>
      </Panel>

      {modal !== "closed" && (
        <div className="rla-modal-overlay" onClick={() => !isLoading("save") && setModal("closed")}>
          <div className="rla-modal rla-modal-wide" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={`${cfg.title} editor`}>
            <div className="rla-modal-head">
              <h3>{modal === "create" ? `Add ${cfg.title.slice(0, -1)}` : modal === "view" ? "View" : `Edit ${form[cfg.nameKey] || ""}`}</h3>
              <button onClick={() => setModal("closed")} className="rla-mini-btn" title="Close">✕</button>
            </div>
            {modal === "preview" ? (
              <div className="max-h-[70vh] overflow-y-auto pr-2">
                <p className="text-xs tracking-widest uppercase" style={{ color: "var(--rla-accent-gold, #b98a1d)" }}>{cfg.kind} — Preview</p>
                <h2 className="text-2xl font-bold mt-1">{form[cfg.nameKey] || "(untitled)"}</h2>
                {form.purpose && <p className="mt-2 text-sm font-medium" style={{ color: "var(--rla-text)" }}>{form.purpose}</p>}
                {form.shortDescription && <p className="mt-1 text-sm" style={{ color: "var(--rla-text-faint)" }}>{form.shortDescription}</p>}
                {form.featuredImage && <img src={form.featuredImage} alt="" className="mt-4 rounded-xl w-full" loading="lazy" style={{ maxHeight: 280, objectFit: "cover" }} />}
                {form.description && <div className="mt-4 text-sm"><Markdown text={form.description} /></div>}
                {form.problem && <div className="mt-4"><h4 className="font-semibold text-sm">Problem</h4><p className="text-sm mt-1">{form.problem}</p></div>}
                {form.solution && <div className="mt-4"><h4 className="font-semibold text-sm">Solution</h4><p className="text-sm mt-1">{form.solution}</p></div>}
                {form.goal && <div className="mt-4"><h4 className="font-semibold text-sm">Goal</h4><p className="text-sm mt-1">{form.goal}</p></div>}
                {!!fromLines(form.objectives).length && <div className="mt-4"><h4 className="font-semibold text-sm">Objectives</h4><ol className="list-decimal ml-5 text-sm mt-1">{fromLines(form.objectives).map((o) => <li key={o}>{o}</li>)}</ol></div>}
                {!!fromCSV(form.userRoles).length && <div className="mt-4"><h4 className="font-semibold text-sm">User Roles</h4><p className="text-sm mt-1">{fromCSV(form.userRoles).join(" · ")}</p></div>}
                {!!fromCSV(form.targetUsers).length && <div className="mt-4"><h4 className="font-semibold text-sm">Target Users</h4><p className="text-sm mt-1">{fromCSV(form.targetUsers).join(" · ")}</p></div>}
                {form.functionalDetails && <div className="mt-4"><h4 className="font-semibold text-sm">Functional Details</h4><div className="text-sm mt-1"><Markdown text={form.functionalDetails} /></div></div>}
                {!!fromCSV(form.features).length && <div className="mt-4"><h4 className="font-semibold text-sm">Key Features</h4><ul className="list-disc ml-5 text-sm mt-1">{fromCSV(form.features).map((f) => <li key={f}>{f}</li>)}</ul></div>}
                {form.workflow && <div className="mt-4"><h4 className="font-semibold text-sm">How It Works</h4><div className="text-sm mt-1"><Markdown text={form.workflow} /></div></div>}
                {!!fromCSV(form.techStack).length && <p className="mt-4 text-sm"><b>Technology:</b> {fromCSV(form.techStack).join(" · ")}</p>}
                {form.architecture && <p className="mt-2 text-sm"><b>Architecture:</b> {form.architecture}</p>}
                {form.techNotes && <p className="mt-2 text-sm"><b>Technology notes:</b> {form.techNotes}</p>}
                {form.architectureImage && <img src={form.architectureImage} alt="Architecture diagram" className="mt-2 rounded-xl w-full" loading="lazy" />}
                {form.origin && <p className="mt-2 text-xs" style={{ color: "var(--rla-text-faint)" }}>Origin: {form.origin}</p>}
                {form.role && <p className="mt-2 text-sm"><b>Rajib&apos;s Role:</b> {form.role}</p>}
                {form.businessValue && <div className="mt-4"><h4 className="font-semibold text-sm">Outcome / Value</h4><p className="text-sm mt-1">{form.businessValue}</p></div>}
                {form.challenges && <div className="mt-4"><h4 className="font-semibold text-sm">Challenges</h4><p className="text-sm mt-1">{form.challenges}</p></div>}
                {!!(form.gallery || []).length && <div className="flex gap-2 mt-4 flex-wrap">{form.gallery.map((g: string) => <img key={g} src={g} alt="" style={{ width: 120, height: 90, objectFit: "cover", borderRadius: 8 }} loading="lazy" />)}</div>}
                {form.videoUrl && <div className="mt-4"><h4 className="font-semibold text-sm">Video / Demo</h4><p className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{form.videoUrl}</p></div>}
                <div className="flex flex-wrap gap-2 mt-4">
                  {form.liveUrl && <span className="rla-btn rla-btn-primary rla-btn-sm">Live Website ↗</span>}
                  {form.githubUrl && <span className="rla-btn rla-btn-ghost rla-btn-sm">GitHub ↗</span>}
                  {form.productUrl && <span className="rla-btn rla-btn-ghost rla-btn-sm">Product ↗</span>}
                  {form.docsUrl && <span className="rla-btn rla-btn-ghost rla-btn-sm">Docs ↗</span>}
                  {form.ctaUrl && <span className="rla-btn rla-btn-ghost rla-btn-sm">{form.ctaText || "Learn more"} ↗</span>}
                </div>
                <div className="flex gap-2 mt-2 text-xs" style={{ color: "var(--rla-text-faint)" }}>
                  {form.category && <span>Category: {form.category}</span>}
                  {form.tags && <span>Tags: {form.tags}</span>}
                  {form.featured && <span>★ Featured</span>}
                  <span>Status: {form.status}</span>
                </div>
                <div className="rla-inline-actions" style={{ marginTop: 16 }}>
                  <button onClick={() => setModal(editId ? "edit" : "create")} className="rla-btn rla-btn-ghost rla-btn-sm">Back to edit</button>
                </div>
              </div>
            ) : (
              <div>
                {isLoading("save") && <div style={{marginBottom:12}}><InlineLoader text="Saving content..." /></div>}
                {errors.length > 0 && <div className="rla-alert-error">{errors.map((e, i) => <div key={i}>{e}</div>)}</div>}
                <h4 className="rla-h4">Basic Information</h4>
                <div className="rla-form-grid">
                  <Field label={cfg.nameLabel}><input value={form[cfg.nameKey]} onChange={(e) => set(cfg.nameKey, e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. PestFlow — Pest Control Platform" /></Field>
                  <Field label="Slug (auto)"><input value={form.slug} onChange={(e) => set("slug", e.target.value)} className="rla-input" disabled={readOnly} placeholder="auto from title" /></Field>
                  <Field label="Category"><input value={form.category} onChange={(e) => set("category", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. SaaS, AI, Enterprise" /></Field>
                  <Field label="Display Order"><input type="number" value={form.displayOrder} onChange={(e) => set("displayOrder", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Origin — where did this come from?"><select value={form.origin || ""} onChange={(e) => set("origin", e.target.value)} className="rla-select" disabled={readOnly}>
                    <option value="">— unset (no label shown) —</option>
                    <option value="client">Client work</option><option value="product">Own product</option>
                    <option value="engineering">Engineering R&amp;D</option><option value="exploration">Product exploration</option>
                  </select></Field>
                  <Field label="Short Description — one-line purpose" span><input value={form.shortDescription} onChange={(e) => set("shortDescription", e.target.value)} className="rla-input" disabled={readOnly} placeholder="One-line purpose visible on homepage cards" /></Field>
                </div>
                <h4 className="rla-h4">Description</h4>
                <Field label="Full description (Markdown: ## headings, **bold**, - lists, [links](url))" span>
                  <textarea value={form.description} onChange={(e) => set("description", e.target.value)} rows={8} className="rla-textarea rla-mono" disabled={readOnly} placeholder="Comprehensive project narrative. Keep concise — detail page splits into sections." />
                </Field>
                <h4 className="rla-h4">Purpose & Problem</h4>
                <Field label="Purpose — what is this project?" span><textarea value={form.purpose || ""} onChange={(e) => set("purpose", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} placeholder="An automation platform designed to reduce manual quotation and technician assignment workflows." /></Field>
                <Field label="Problem — what problem existed before?" span><textarea value={form.problem} onChange={(e) => set("problem", e.target.value)} rows={3} className="rla-textarea" disabled={readOnly} placeholder="Businesses were managing quotations, assignments and customer communication manually..." /></Field>
                <Field label="Target Users — who is it for? (comma separated)" span><input value={form.targetUsers || ""} onChange={(e) => set("targetUsers", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. Pest control operators, Field technicians, Admin, Customers" /></Field>
                <h4 className="rla-h4">Solution</h4>
                <Field label="Solution — what was built and how it solves the problem?" span><textarea value={form.solution} onChange={(e) => set("solution", e.target.value)} rows={3} className="rla-textarea" disabled={readOnly} placeholder="The platform connects customer requests, quotation generation, technician assignment and status tracking..." /></Field>
                <h4 className="rla-h4">Goal & Objectives</h4>
                <Field label="Goal — the desired high-level outcome" span><textarea value={form.goal || ""} onChange={(e) => set("goal", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} placeholder="e.g. A single platform managing the workflow from quotation through completion and payment." /></Field>
                <Field label="Objectives — one per line (only verified ones; empty hides the section)" span><textarea value={form.objectives || ""} onChange={(e) => set("objectives", e.target.value)} rows={4} className="rla-textarea rla-mono" disabled={readOnly} placeholder={"Centralize operations\nImprove workflow visibility\nReduce manual processing"} /></Field>
                <Field label="User roles — who uses it? (comma separated)" span><input value={form.userRoles || ""} onChange={(e) => set("userRoles", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. Customer, Technician, Admin, Manager" /></Field>
                <h4 className="rla-h4">Functional Details</h4>
                <Field label="Functional details — main workflows & capabilities (Markdown supported)" span><textarea value={form.functionalDetails || ""} onChange={(e) => set("functionalDetails", e.target.value)} rows={4} className="rla-textarea rla-mono" disabled={readOnly} placeholder="- Customer request management&#10;- Automated quotation&#10;- Technician assignment&#10;- Status tracking" /></Field>
                <h4 className="rla-h4">Features</h4>
                <Field label="Key features (comma separated) — shown as feature cards" span><textarea value={form.features} onChange={(e) => set("features", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} placeholder="e.g. Real-time updates, HMAC-signed APIs, Stripe payments, Visual workflow builder" /></Field>
                <h4 className="rla-h4">Workflow / How it works</h4>
                <Field label="Workflow — concise steps (one per line or markdown)" span><textarea value={form.workflow || ""} onChange={(e) => set("workflow", e.target.value)} rows={3} className="rla-textarea rla-mono" disabled={readOnly} placeholder="Discover → Design → Build → Deliver&#10;or: 1. Customer submits request → 2. System generates quotation → 3. Technician assigned" /></Field>
                <h4 className="rla-h4">Technology & Architecture</h4>
                <div className="rla-form-grid">
                  <Field label="Tech stack (comma separated)"><input value={form.techStack} onChange={(e) => set("techStack", e.target.value)} className="rla-input" disabled={readOnly} placeholder="React, FastAPI, MongoDB, AI, Docker" /></Field>
                  <Field label="Architecture summary"><input value={form.architecture} onChange={(e) => set("architecture", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. Event-driven microservices on Azure" /></Field>
                  <Field label="Technology notes — what each tech does here" span><textarea value={form.techNotes || ""} onChange={(e) => set("techNotes", e.target.value)} rows={3} className="rla-textarea" disabled={readOnly} placeholder="e.g. React renders the responsive PWA · FastAPI serves the API layer · MongoDB stores operational data. Only describe what is actually used." /></Field>
                  <Field label="Architecture diagram image URL" span><input value={form.architectureImage || ""} onChange={(e) => set("architectureImage", e.target.value)} className="rla-input" disabled={readOnly} placeholder="https://…/architecture.png (shown instead of the generated diagram)" /></Field>
                  {cfg.showAiCaps && (<>
                    <Field label="AI capabilities (comma separated)"><input value={form.aiCapabilities} onChange={(e) => set("aiCapabilities", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                    <Field label="Cloud capabilities (comma separated)"><input value={form.cloudCapabilities} onChange={(e) => set("cloudCapabilities", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  </>)}
                  {!cfg.showAiCaps && (<Field label="AI capabilities"><input value={form.aiCapabilities || ""} onChange={(e) => set("aiCapabilities", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. RAG, LLM orchestration" /></Field>)}
                </div>
                <h4 className="rla-h4">Role & Outcome</h4>
                <div className="rla-form-grid">
                  <Field label="Rajib's Role" span><input value={form.role} onChange={(e) => set("role", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. Architected data lake, designed CQRS Rule Engine, led implementation" /></Field>
                  <Field label="Business value / Outcome" span><textarea value={form.businessValue || ""} onChange={(e) => set("businessValue", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} placeholder="Measurable outcome — keep verified metrics only, otherwise describe value." /></Field>
                  <Field label="Challenges" span><textarea value={form.challenges || ""} onChange={(e) => set("challenges", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} placeholder="Key challenges faced and how they were addressed (optional)" /></Field>
                </div>
                <h4 className="rla-h4">Media</h4>
                <div className="rla-form-grid">
                  <Field label="Main image">
                    <div className="flex items-center gap-2 flex-wrap">
                      {form.featuredImage && <img src={form.featuredImage} alt="" style={{ width: 96, height: 72, objectFit: "cover", borderRadius: 8 }} />}
                      {!readOnly && (<>
                        <button onClick={() => fileRef.current?.click()} disabled={uploading !== null} className="rla-btn rla-btn-ghost rla-btn-sm">{uploading === "featuredImage" ? "Uploading…" : form.featuredImage ? "Replace" : "Upload"}</button>
                        {form.featuredImage && <button onClick={() => removeImage(form.featuredImage, "featuredImage")} className="rla-mini-btn danger" title="Remove"><i className="fas fa-trash" /></button>}
                      </>)}
                    </div>
                    <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,image/gif" style={{ display: "none" }} onChange={(e) => { uploadInto(e.target.files?.[0], "featuredImage"); e.target.value = ""; }} />
                    <input value={form.featuredImage || ""} onChange={(e) => set("featuredImage", e.target.value)} placeholder="…or paste image URL" className="rla-input mt-2" disabled={readOnly} />
                  </Field>
                  <Field label="Video embed URL (YouTube/Vimeo)">
                    <input value={form.videoUrl || ""} onChange={(e) => set("videoUrl", e.target.value)} placeholder="https://youtu.be/…" className="rla-input" disabled={readOnly} />
                  </Field>
                </div>
                <Field label="Gallery" span>
                  <div className="flex gap-2 flex-wrap items-center">
                    {(form.gallery || []).map((g: string) => (
                      <span key={g} style={{ position: "relative", display: "inline-block" }}>
                        <img src={g} alt="" style={{ width: 96, height: 72, objectFit: "cover", borderRadius: 8 }} />
                        {!readOnly && <button onClick={() => removeImage(g, "gallery")} className="rla-mini-btn danger" title="Remove" style={{ position: "absolute", top: 2, right: 2 }}>✕</button>}
                      </span>
                    ))}
                    {!readOnly && <button onClick={() => galleryRef.current?.click()} disabled={uploading !== null} className="rla-btn rla-btn-ghost rla-btn-sm">{uploading === "gallery" ? "Uploading…" : "+ Add image"}</button>}
                  </div>
                  <input ref={galleryRef} type="file" accept="image/png,image/jpeg,image/webp,image/gif" style={{ display: "none" }} onChange={(e) => { uploadInto(e.target.files?.[0], "gallery"); e.target.value = ""; }} />
                </Field>
                <h4 className="rla-h4">Tags</h4>
                <div className="rla-form-grid">
                  <Field label="Tags (comma separated) — used for filtering & SEO"><input value={form.tags} onChange={(e) => set("tags", e.target.value)} className="rla-input" disabled={readOnly} placeholder="e.g. SaaS, Automation, AI" /></Field>
                </div>
                <h4 className="rla-h4">Links</h4>
                <div className="rla-form-grid">
                  <Field label="Live website URL"><input value={form.liveUrl || ""} onChange={(e) => set("liveUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="GitHub URL"><input value={form.githubUrl || ""} onChange={(e) => set("githubUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  {cfg.kind === "portfolio" && (<>
                    <Field label="Demo URL"><input value={form.demoUrl || ""} onChange={(e) => set("demoUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                    <Field label="Product URL"><input value={form.productUrl || ""} onChange={(e) => set("productUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  </>)}
                  {cfg.kind === "products" && <Field label="Product URL"><input value={form.productUrl || ""} onChange={(e) => set("productUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>}
                  <Field label="Documentation URL"><input value={form.docsUrl || ""} onChange={(e) => set("docsUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="CTA text"><input value={form.ctaText || ""} onChange={(e) => set("ctaText", e.target.value)} placeholder="e.g. Request Quote" className="rla-input" disabled={readOnly} /></Field>
                  <Field label="CTA link"><input value={form.ctaUrl || ""} onChange={(e) => set("ctaUrl", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                </div>
                <h4 className="rla-h4">Publishing</h4>
                <div className="rla-form-grid">
                  <Field label="Status">
                    <select value={form.status} onChange={(e) => set("status", e.target.value)} className="rla-select" disabled={readOnly}>
                      <option value="draft">draft (inactive)</option><option value="published">published (active)</option>
                      {cfg.kind === "portfolio" && (<><option value="review">review</option><option value="hidden">hidden</option></>)}
                      {cfg.kind === "products" && <option value="featured">featured</option>}
                    </select>
                  </Field>
                  <Field label="Featured"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!form.featured} onChange={(e) => set("featured", e.target.checked)} disabled={readOnly} /> Featured (homepage highlight)</label></Field>
                  <Field label="RAG indexing"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.ragIndexed !== false} onChange={(e) => set("ragIndexed", e.target.checked)} disabled={readOnly} /> Index in knowledge base</label></Field>
                </div>
                <h4 className="rla-h4">SEO / Metadata</h4>
                <div className="rla-form-grid">
                  <Field label="Meta title"><input value={form.seoTitle || ""} onChange={(e) => set("seoTitle", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Social image URL"><input value={form.seoImage || form.featuredImage || ""} onChange={(e) => set("seoImage", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Meta description" span><textarea value={form.seoDescription || ""} onChange={(e) => set("seoDescription", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} /></Field>
                </div>
                {!readOnly && (
                  <div className="rla-inline-actions" style={{ marginTop: 16 }}>
                    <button onClick={() => save(false)} disabled={isLoading("save")} className="rla-btn rla-btn-primary rla-btn-sm" aria-busy={isLoading("save")}><i className={`fas ${isLoading("save") ? "fa-spinner fa-spin" : "fa-check"}`} /> {isLoading("save") ? "Saving..." : "Save"}</button>
                    <button onClick={() => save(true)} disabled={isLoading("save")} className="rla-btn rla-btn-ghost rla-btn-sm" aria-busy={isLoading("save")}>{isLoading("save") ? <InlineLoader text="Saving..." /> : "Save & Continue"}</button>
                    <button onClick={() => setModal("preview")} className="rla-btn rla-btn-ghost rla-btn-sm">Preview</button>
                    <button onClick={() => setModal("closed")} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>
                    {editId && <button onClick={() => { const it = items.find((x) => x.id === editId); if (it) remove(it); setModal("closed"); }} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /> Delete</button>}
                  </div>
                )}
                {readOnly && (
                  <div className="rla-inline-actions" style={{ marginTop: 16 }}>
                    <button onClick={() => setModal("preview")} className="rla-btn rla-btn-ghost rla-btn-sm">Preview</button>
                    <button onClick={() => setModal("closed")} className="rla-btn rla-btn-ghost rla-btn-sm">Close</button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
