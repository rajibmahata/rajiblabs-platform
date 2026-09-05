import { useEffect, useRef, useState } from "react";
import { analyzeScope, createChatSession, getAgentCard, getChatHistory, sendAgentChat, sendChat } from "../services/api";
import { useLang } from "../i18n/langContext";

// NOTE: rendered INSIDE <main class="rlz"> (see Home.tsx) so every
// .rlz-* class below resolves to the homepage design tokens.
const FALLBACK_STARTERS = [
  "Do you know about RajibLabs?",
  "Tell me about Rajib",
  "What projects has Rajib completed?",
  "Is there a live URL for this project?",
  "What services does RajibLabs provide?",
  "Show me Rajib's GitHub work",
  "I have a project idea",
  "Contact RajibLabs",
];
export const OPEN_CHAT_EVENT = "rlz-open-chat";
const SESSION_KEY = "rlz_chat_session";
const CHECKS = [
  { key: "name", label: "Name" },
  { key: "email", label: "Email" },
  { key: "phone", label: "Phone" },
  { key: "idea", label: "Idea" },
] as const;

import type { RagSource } from "../services/api";

type Msg =
  | { kind: "text"; role: string; text: string; sources?: RagSource[] }
  | { kind: "scope"; markdown: string }
  | { kind: "error"; text: string; retryText: string };

type ChatMode = "ask" | "plan";

export default function ChatWidget() {
  const { t, tArr, lang } = useLang();
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>(() => [
    { kind: "text", role: "assistant", text: t("chat.greeting") },
  ]);
  const [starters, setStarters] = useState<string[]>(FALLBACK_STARTERS);
  const [input, setInput] = useState("");
  const [session, setSession] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [missing, setMissing] = useState<string[]>(["name", "email", "phone", "idea"]);
  const [blueprint, setBlueprint] = useState(false);
  const [scopeBusy, setScopeBusy] = useState(false);
  const [restored, setRestored] = useState(false);
  // ask = grounded knowledge Q&A (mode=rag), plan = lead/business discovery.
  const [mode, setMode] = useState<ChatMode>("plan");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, open]);

  // Restore persisted session (history) once per mount.
  useEffect(() => {
    if (restored) return;
    setRestored(true);
    getAgentCard().then((c) => { if (c?.starters?.length) setStarters(c.starters); }).catch(() => {});
    const onOpen = () => setOpen(true);
    window.addEventListener(OPEN_CHAT_EVENT, onOpen);
    const saved = (() => { try { return localStorage.getItem(SESSION_KEY); } catch { return null; } })();
    if (!saved) return;
    getChatHistory(saved).then((h) => {
      setSession(h.session_id);
      if (h.messages.length) {
        setMsgs(h.messages.map((m) => ({ kind: "text", role: m.role, text: m.text }) as Msg));
      }
      setMissing(h.missing_fields ?? []);
      setBlueprint(!!h.show_blueprint);
      try { localStorage.setItem(SESSION_KEY, h.session_id); } catch { /* private mode */ }
    }).catch(() => {
      try { localStorage.removeItem(SESSION_KEY); } catch { /* private mode */ }
    });
    return () => window.removeEventListener(OPEN_CHAT_EVENT, onOpen);
  }, [restored]);

  const sendText = async (raw: string) => {
    const text = raw.trim();
    if (!text || busy) return;
    setInput("");
    setMsgs((m) => [...m, { kind: "text", role: "user", text }]);
    setBusy(true);
    try {
      let sid = session;
      if (!sid) {
        try {
          sid = (await createChatSession()).session_id;
        } catch { /* fall through — server creates one inline */ }
      }
      const r = mode === "ask"
        ? await sendAgentChat(text, sid, lang).then((a) => ({
            session_token: a.session_token, session_id: a.session_id,
            reply: a.reply, sources: a.sources ?? [],
            missing_fields: a.missing_fields ?? missing,
            show_blueprint: false,
          }))
        : await sendChat(text, sid, { language: lang });
      const nextSid = r.session_token || (r as { session_id?: string }).session_id || sid;
      setSession(nextSid);
      try { if (nextSid) localStorage.setItem(SESSION_KEY, nextSid); } catch { /* private mode */ }
      setMsgs((m) => [...m, { kind: "text", role: "assistant", text: r.reply, sources: r.sources ?? [] }]);
      setMissing(r.missing_fields ?? []);
      setBlueprint(!!r.show_blueprint);
    } catch {
      setMsgs((m) => [...m, { kind: "error", text: t("chat.sendError"), retryText: text }]);
    } finally {
      setBusy(false);
    }
  };

  const runBlueprint = async () => {
    if (!session || scopeBusy) return;
    setScopeBusy(true);
    try {
      const r = await analyzeScope(session);
      setMsgs((m) => [...m, { kind: "scope", markdown: r.scope_markdown }]);
    } catch (e) {
      setMsgs((m) => [...m, {
        kind: "error",
        text: e instanceof Error ? e.message : t("chat.scopeError"),
        retryText: "",
      }]);
    } finally {
      setScopeBusy(false);
    }
  };

  return (
    <div className="fixed bottom-20 md:bottom-6 right-4 z-50 flex flex-col items-end gap-3">
      {open && (
        <div className="rlz-chat-panel" role="dialog" aria-label={t("chat.title")}>
          <div className="rlz-chat-head">
            <span className="rlz-bento-icon rlz-icon-violet">
              <i className="material-symbols-outlined">smart_toy</i>
            </span>
            <div className="flex-1 min-w-0">
              <p className="rlz-chat-title">{t("chat.title")}</p>
              <span className="rlz-chat-status"><span className="rlz-live-dot" /> {t("chat.online")}</span>
            </div>
            <button className="rlz-chat-close" onClick={() => setOpen(false)} aria-label={t("chat.close")}>
              <i className="material-symbols-outlined">close</i>
            </button>
          </div>

          <div className="rlz-chat-quick" role="tablist" aria-label="Chat mode">
            {(["ask", "plan"] as ChatMode[]).map((cm) => (
              <button
                key={cm} role="tab" aria-selected={mode === cm}
                className="rlz-chip" disabled={busy}
                style={mode === cm ? { fontWeight: 700 } : undefined}
                onClick={() => setMode(cm)}
              >
                {cm === "ask" ? t("chat.ask") : t("chat.plan")}
              </button>
            ))}
          </div>

          <div className="rlz-chat-captured" aria-label="Information captured">
            {CHECKS.map((c, i) => {
              const done = !missing.includes(c.key);
              const labels = tArr("chat.checks");
              return (
                <span key={c.key} className={`rlz-chat-check${done ? " done" : ""}`}>
                  {done ? "✓ " : ""}{labels[i] || c.label}
                </span>
              );
            })}
          </div>

          <div ref={scrollRef} className="rlz-chat-log">
            {msgs.map((m, i) => (
              m.kind === "scope" ? (
                <div key={i} className="text-left">
                  <div className="rlz-chat-scope">
                    <p className="rlz-chat-scope-title">{t("chat.scopeTitle")}</p>
                    <pre className="rlz-chat-scope-body">{m.markdown}</pre>
                  </div>
                </div>
              ) : m.kind === "error" ? (
                <div key={i} className="text-left">
                  <span className="rlz-chat-msg rlz-chat-ai">{m.text}</span>
                  {m.retryText && (
                    <div className="mt-1">
                      <button className="rlz-chip" onClick={() => void sendText(m.retryText)} disabled={busy}>{t("chat.retry")}</button>
                    </div>
                  )}
                </div>
              ) : (
                <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                  <span className={`rlz-chat-msg ${m.role === "user" ? "rlz-chat-user" : "rlz-chat-ai"}`}>{m.text}</span>
                  {m.role !== "user" && m.sources && m.sources.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1" aria-label="Verified sources">
                      {m.sources.slice(0, 4).map((s, j) => (
                        s.url ? (
                          <a key={j} className="rlz-chip" href={s.url} target="_blank" rel="noreferrer">
                            {s.title || s.source_type}
                          </a>
                        ) : (
                          <span key={j} className="rlz-chip">{s.title || s.source_type}</span>
                        )
                      ))}
                    </div>
                  )}
                </div>
              )
            ))}
            {busy && (
              <div className="text-left">
                <span className="rlz-chat-msg rlz-chat-typing">typing…</span>
              </div>
            )}
          </div>

          {blueprint && (
            <div className="rlz-chat-cta">
              <p className="rlz-chat-cta-text">{t("chat.blueprintCta")}</p>
              <div className="rlz-chat-cta-row">
                <button className="rlz-chat-cta-btn" onClick={() => void runBlueprint()} disabled={scopeBusy}>
                  {scopeBusy ? t("chat.generating") : t("chat.blueprintBtn")}
                </button>
                <a className="rlz-chat-cta-link" href="mailto:rajibmahata143@gmail.com?subject=RajibLabs%20project%20enquiry">{t("chat.discuss")}</a>
              </div>
            </div>
          )}

          <div className="rlz-chat-quick">
            {starters.map((q) => (
              <button key={q} className="rlz-chip" onClick={() => void sendText(q)} disabled={busy}>
                {q}
              </button>
            ))}
          </div>

          <div className="rlz-chat-bar">
            <input
              value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void sendText(input)}
              placeholder={t("chat.placeholder")} className="rlz-chat-input" aria-label="Chat message"
            />
            <button className="rlz-chat-send" onClick={() => void sendText(input)} disabled={busy} aria-label={t("chat.send")}>
              <i className="material-symbols-outlined">send</i>
            </button>
          </div>
        </div>
      )}
      <button className="rlz-chat-launcher" onClick={() => setOpen((o) => !o)} aria-label={open ? t("chat.close") : t("chat.open")}>
        <i className="material-symbols-outlined">{open ? "close" : "forum"}</i>
      </button>
    </div>
  );
}
