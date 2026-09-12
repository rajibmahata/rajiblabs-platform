import { useEffect, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../services/api";

interface Msg { id: string; conversation_id: string; session_token: string; sender: string; message: string; intent?: string; tools_called?: string[]; agent_slug?: string; ai_provider?: string; ai_model?: string; duration_ms?: number; created_at?: string }
interface DetailMsg { id: string; sender: string; message: string; intent?: string; tools_called?: string[]; sources_used?: Record<string, unknown>[]; ai_provider?: string; ai_model?: string; duration_ms?: number; created_at?: string }

function relativeTime(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = Date.now();
  const diff = (now - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}

export default function AgentOpsConversationsPage() {
  const { conversationId } = useParams();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [agent, setAgent] = useState("");
  const [hasLlm, setHasLlm] = useState<boolean | null>(null);
  const [detail, setDetail] = useState<{ conversation_id: string; messages: DetailMsg[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const limit = 30;

  const load = useCallback(() => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
    if (agent) params.set("agent", agent);
    if (hasLlm !== null) params.set("has_llm", String(hasLlm));
    let active = true;
    api.get<{ messages: Msg[]; total: number }>(`/api/admin/ops/conversations?${params}`)
      .then((r) => { if (active) { setMessages(r.messages || []); setTotal(r.total); } })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [page, agent, hasLlm]);

  useEffect(() => { return load(); }, [load]);

  useEffect(() => {
    if (!conversationId) return;
    let active = true;
    api.get<{ conversation_id: string; messages: DetailMsg[] }>(`/api/admin/ops/conversations/${conversationId}`)
      .then((d) => { if (active) setDetail(d); })
      .catch(() => { if (active) setDetail(null); });
    return () => { active = false; };
  }, [conversationId]);

  // Conversation detail drawer
  if (conversationId) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
            <i className="fas fa-comments" style={{ marginRight: 8, color: "var(--rla-cyan)" }} />
            Conversation Detail
          </h2>
          <Link to="/admin/ops/conversations" style={{ fontSize: 13, color: "var(--rla-violet)" }}>
            <i className="fas fa-arrow-left" style={{ marginRight: 4 }} /> Back
          </Link>
        </div>
        {!detail && <div style={{ padding: 20, color: "var(--rla-text-dim)" }}>Loading…</div>}
        {detail && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {detail.messages.map((m) => (
              <div key={m.id} style={{
                background: m.sender === "user" ? "var(--rla-violet-soft)" : "var(--rla-surface)",
                border: "1px solid var(--rla-border)", borderRadius: 10, padding: 14,
                maxWidth: m.sender === "user" ? "75%" : "100%",
                alignSelf: m.sender === "user" ? "flex-end" : "flex-start",
              }}>
                <div style={{ fontSize: 10, color: "var(--rla-text-faint)", marginBottom: 4 }}>
                  {m.sender === "user" ? "Visitor" : "Agent"} · {m.intent || "—"} · {relativeTime(m.created_at)}
                  {m.duration_ms ? <span> · {m.duration_ms}ms</span> : null}
                </div>
                <div style={{ fontSize: 13.5, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{m.message}</div>
                {m.tools_called && m.tools_called.length > 0 && (
                  <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {m.tools_called.map((t) => (
                      <span key={t} style={{ fontSize: 10, padding: "1px 6px", borderRadius: 6, background: "var(--rla-cyan-soft)", color: "var(--rla-cyan)" }}>{t}</span>
                    ))}
                  </div>
                )}
                {m.ai_provider && (
                  <div style={{ marginTop: 4, fontSize: 11, color: "var(--rla-text-faint)" }}>
                    LLM: {m.ai_provider}/{m.ai_model || "?"}
                  </div>
                )}
              </div>
            ))}
            {detail.messages.length === 0 && <div style={{ color: "var(--rla-text-faint)", padding: 20 }}>No messages in this conversation.</div>}
          </div>
        )}
      </div>
    );
  }

  // Conversations list
  const pages = Math.ceil(total / limit);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
          <i className="fas fa-comments" style={{ marginRight: 8, color: "var(--rla-cyan)" }} />
          Agent Conversations
        </h2>
        <div style={{ fontSize: 13, color: "var(--rla-text-dim)" }}>{total} messages total</div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <select value={agent} onChange={(e) => { setAgent(e.target.value); setPage(0); }}
          style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 13, background: "var(--rla-surface)" }}>
          <option value="">All agents</option>
          <option value="rajiblabs-concierge">Concierge</option>
          <option value="rajiblabs-career">Career</option>
          <option value="rajiblabs-profile">Profile</option>
          <option value="rajiblabs-learning">Learning</option>
        </select>
        <select value={hasLlm === null ? "" : String(hasLlm)} onChange={(e) => { setHasLlm(e.target.value === "" ? null : e.target.value === "true"); setPage(0); }}
          style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 13, background: "var(--rla-surface)" }}>
          <option value="">All messages</option>
          <option value="true">Used LLM</option>
          <option value="false">Tool-only (no LLM)</option>
        </select>
      </div>

      {loading && <div style={{ padding: 16, color: "var(--rla-text-dim)" }}>Loading…</div>}

      {!loading && messages.length === 0 && <div style={{ padding: 20, color: "var(--rla-text-faint)" }}>No conversations found.</div>}

      {!loading && messages.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {messages.map((m) => (
            <Link key={m.id} to={`/admin/ops/conversations/${m.conversation_id}`}
              style={{
                display: "grid", gridTemplateColumns: "70px 80px 1fr 120px 60px 70px",
                alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 8,
                background: "var(--rla-surface)", border: "1px solid var(--rla-border)",
                textDecoration: "none", color: "inherit", fontSize: 13,
                transition: "border-color 0.15s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--rla-violet)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--rla-border)"; }}
            >
              <span style={{ fontFamily: "monospace", fontSize: 11, color: "var(--rla-text-faint)" }}>
                {m.session_token.slice(0, 8)}…
              </span>
              <span style={{
                fontSize: 10, fontWeight: 600, padding: "2px 6px", borderRadius: 6,
                background: m.sender === "user" ? "var(--rla-violet-soft)" : "var(--rla-green-soft)",
                color: m.sender === "user" ? "var(--rla-violet)" : "var(--rla-green)",
                textAlign: "center",
              }}>{m.sender === "user" ? "USR" : "AGT"}</span>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--rla-text-dim)" }}>
                {m.message}
              </span>
              <span style={{ fontFamily: "monospace", fontSize: 11, color: "var(--rla-text-faint)" }}>
                {m.intent || "—"}
              </span>
              <span style={{ fontSize: 12, color: m.ai_provider ? "var(--rla-green)" : "var(--rla-text-faint)" }}>
                {m.ai_provider ? "LLM" : "tool"}
              </span>
              <span style={{ fontSize: 11, color: "var(--rla-text-faint)" }}>
                {relativeTime(m.created_at)}
              </span>
            </Link>
          ))}
        </div>
      )}

      {pages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 8 }}>
          <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
            style={{ padding: "6px 14px", borderRadius: 8, border: "1px solid var(--rla-border)", background: "var(--rla-surface)", cursor: page === 0 ? "default" : "pointer", opacity: page === 0 ? 0.5 : 1, fontSize: 13 }}>
            ← Prev
          </button>
          <span style={{ padding: "6px 12px", fontSize: 13, color: "var(--rla-text-dim)" }}>
            {page + 1} / {pages}
          </span>
          <button onClick={() => setPage((p) => Math.min(pages - 1, p + 1))} disabled={page >= pages - 1}
            style={{ padding: "6px 14px", borderRadius: 8, border: "1px solid var(--rla-border)", background: "var(--rla-surface)", cursor: page >= pages - 1 ? "default" : "pointer", opacity: page >= pages - 1 ? 0.5 : 1, fontSize: 13 }}>
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
