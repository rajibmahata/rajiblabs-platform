/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "./ui";
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

const EMPTY_FORM: any = {
  title: "", name: "", slug: "", shortDescription: "", description: "",
  problem: "", solution: "", role: "", architecture: "",
  category: "", status: "draft", featured: false, displayOrder: 0,
  techStack: "", tags: "", features: "",
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
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState<string | null>(null);
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
    for (const [k, label] of [["liveUrl", "Live URL"], ["githubUrl", "GitHub URL"], ["docsUrl", "Docs URL"], ["ctaUrl", "CTA link"], ["productUrl", "Product URL"], ["demoUrl", "Demo URL"]] as const) {
      const v = String(form[k] || "").trim();
      if (v && !/^https?:\/\/.+\..+/.test(v)) errs.push(`${label} must start with http(s)://`);
    }
    return errs;
  };

  const payload = () => {
    const p: any = {
      [cfg.nameKey]: String(form[cfg.nameKey] || "").trim(),
      slug: form.slug.trim().toLowerCase() || undefined,
      shortDescription: form.shortDescription?.trim() || "",
      description: form.description || "",
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
        problem: form.problem || "", solution: form.solution || "", role: form.role || "",
        architecture: form.architecture || "",
        aiCapabilities: fromCSV(form.aiCapabilities), cloudCapabilities: fromCSV(form.cloudCapabilities),
        demoUrl: form.demoUrl?.trim() || null, gitHubUrl: form.githubUrl?.trim() || null,
        productUrl: form.productUrl?.trim() || null,
      });
    } else {
      Object.assign(p, {
        category: form.category?.trim() || "",
        features: fromCSV(form.features),
        aiCapabilities: form.aiCapabilities?.trim() || null,
        architecture: form.architecture?.trim() || "",
        productUrl: form.productUrl?.trim() || null,
        gitHubUrl: form.githubUrl?.trim() || null,
      });
    }
    return p;
  };

  const save = async (stayOpen: boolean) => {
    const errs = validate();
    setErrors(errs);
    if (errs.length) return;
    setBusy(true);
    try {
      const body = payload();
      const saved = editId
        ? await api.put<any>(`${base}/${editId}`, body)
        : await api.post<any>(base, body);
      toast("Saved", `${saved[cfg.nameKey] || cfg.title} saved.`);
      load(page);
      if (stayOpen && saved.id) { setEditId(saved.id); setForm({ ...form, ...saved, techStack: toCSV(saved.techStack), tags: toCSV(saved.tags), features: toCSV(saved.features), aiCapabilities: toCSV(saved.aiCapabilities), cloudCapabilities: toCSV(saved.cloudCapabilities) }); setModal("edit"); }
      else setModal("closed");
    } catch (e: any) { setErrors([String(e.message || e).slice(0, 300)]); } finally { setBusy(false); }
  };

  const toggleStatus = async (item: any) => {
    const next = item.status === "published" ? "draft" : "published";
    try {
      await api.patch(`${base}/${item.id}/status`, { status: next });
      toast(next === "published" ? "Published" : "Unpublished", `${item[cfg.nameKey]} is now ${next}.`);
      load(page);
    } catch (e: any) { toast("Update failed", String(e.message || e).slice(0, 120)); }
  };
  const toggleFeatured = async (item: any) => {
    try {
      await api.patch(`${base}/${item.id}/featured`, { featured: !item.featured });
      load(page);
    } catch (e: any) { toast("Update failed", String(e.message || e).slice(0, 120)); }
  };
  const remove = async (item: any) => {
    if (!confirm(`Delete "${item[cfg.nameKey]}"? This removes it and its knowledge vectors.`)) return;
    try { await api.del(`${base}/${item.id}`); toast("Deleted", ""); load(page); }
    catch (e: any) { toast("Delete failed", String(e.message || e).slice(0, 120)); }
  };

  const uploadInto = async (file: File | undefined, field: "featuredImage" | "gallery") => {
    if (!file) return;
    setUploading(field);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.upload<{ url: string }>(`/api/admin/uploads/image?kind=${cfg.kind}`, fd);
      if (field === "featuredImage") set("featuredImage", r.url);
      else set("gallery", [...(form.gallery || []), r.url]);
      toast("Uploaded", r.url);
    } catch (e: any) { setErrors([`Image upload failed: ${String(e.message || e).slice(0, 200)}`]); }
    finally { setUploading(null); }
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
        <div className="rla-modal-overlay" onClick={() => !busy && setModal("closed")}>
          <div className="rla-modal rla-modal-wide" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={`${cfg.title} editor`}>
            <div className="rla-modal-head">
              <h3>{modal === "create" ? `Add ${cfg.title.slice(0, -1)}` : modal === "view" ? "View" : `Edit ${form[cfg.nameKey] || ""}`}</h3>
              <button onClick={() => setModal("closed")} className="rla-mini-btn" title="Close">✕</button>
            </div>
            {modal === "preview" ? (
              <div>
                <p className="text-xs tracking-widest uppercase" style={{ color: "var(--rla-accent-gold, #b98a1d)" }}>{cfg.kind}</p>
                <h2 className="text-2xl font-bold mt-1">{form[cfg.nameKey] || "(untitled)"}</h2>
                {form.shortDescription && <p className="mt-2 text-sm">{form.shortDescription}</p>}
                {form.featuredImage && <img src={form.featuredImage} alt="" className="mt-4 rounded-xl w-full" />}
                {form.description && <div className="mt-4 text-sm"><Markdown text={form.description} /></div>}
                {!!(form.gallery || []).length && <div className="flex gap-2 mt-4 flex-wrap">{form.gallery.map((g: string) => <img key={g} src={g} alt="" style={{ width: 120, height: 90, objectFit: "cover", borderRadius: 8 }} />)}</div>}
                {!!fromCSV(form.techStack).length && <p className="mt-4 text-sm"><b>Technology:</b> {fromCSV(form.techStack).join(" · ")}</p>}
                <div className="flex flex-wrap gap-2 mt-4">
                  {form.liveUrl && <span className="rla-btn rla-btn-primary rla-btn-sm">Live Website ↗</span>}
                  {form.githubUrl && <span className="rla-btn rla-btn-ghost rla-btn-sm">GitHub ↗</span>}
                  {form.ctaUrl && <span className="rla-btn rla-btn-ghost rla-btn-sm">{form.ctaText || "Learn more"} ↗</span>}
                </div>
                <div className="rla-inline-actions" style={{ marginTop: 16 }}>
                  <button onClick={() => setModal(editId ? "edit" : "create")} className="rla-btn rla-btn-ghost rla-btn-sm">Back to edit</button>
                </div>
              </div>
            ) : (
              <div>
                {errors.length > 0 && <div className="rla-alert-error">{errors.map((e, i) => <div key={i}>{e}</div>)}</div>}
                <h4 className="rla-h4">Basic Information</h4>
                <div className="rla-form-grid">
                  <Field label={cfg.nameLabel}><input value={form[cfg.nameKey]} onChange={(e) => set(cfg.nameKey, e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Slug (auto)"><input value={form.slug} onChange={(e) => set("slug", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  {cfg.showCategory && <Field label="Category"><input value={form.category} onChange={(e) => set("category", e.target.value)} className="rla-input" disabled={readOnly} /></Field>}
                  <Field label="Display Order"><input type="number" value={form.displayOrder} onChange={(e) => set("displayOrder", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Short Description" span><input value={form.shortDescription} onChange={(e) => set("shortDescription", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                </div>
                <h4 className="rla-h4">Description</h4>
                <Field label="Full description (Markdown: ## headings, **bold**, - lists, [links](url))" span>
                  <textarea value={form.description} onChange={(e) => set("description", e.target.value)} rows={8} className="rla-textarea rla-mono" disabled={readOnly} />
                </Field>
                {cfg.showProblemSolution && (<div className="rla-form-grid">
                  <Field label="Problem" span><textarea value={form.problem} onChange={(e) => set("problem", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} /></Field>
                  <Field label="Solution" span><textarea value={form.solution} onChange={(e) => set("solution", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} /></Field>
                  <Field label="Role"><input value={form.role} onChange={(e) => set("role", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Architecture"><input value={form.architecture} onChange={(e) => set("architecture", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                </div>)}
                {cfg.showFeatures && (<Field label="Features (comma separated)" span><textarea value={form.features} onChange={(e) => set("features", e.target.value)} rows={2} className="rla-textarea" disabled={readOnly} /></Field>)}
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
                <h4 className="rla-h4">Technology & Tags</h4>
                <div className="rla-form-grid">
                  <Field label="Tech stack (comma separated)"><input value={form.techStack} onChange={(e) => set("techStack", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  <Field label="Tags (comma separated)"><input value={form.tags} onChange={(e) => set("tags", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  {cfg.showAiCaps && (<>
                    <Field label="AI capabilities (comma separated)"><input value={form.aiCapabilities} onChange={(e) => set("aiCapabilities", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                    <Field label="Cloud capabilities (comma separated)"><input value={form.cloudCapabilities} onChange={(e) => set("cloudCapabilities", e.target.value)} className="rla-input" disabled={readOnly} /></Field>
                  </>)}
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
                    <button onClick={() => save(false)} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">{busy ? "Saving…" : "Save"}</button>
                    <button onClick={() => save(true)} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Save & Continue</button>
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
