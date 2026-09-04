import { useEffect, useRef, useState } from "react";
import { sendChat } from "../services/api";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<{ role: string; text: string }[]>([
    { role: "assistant", text: "Hi — I'm RajibLabs assistant. Ask about projects, technologies, or starting an enquiry." },
  ]);
  const [input, setInput] = useState("");
  const [session, setSession] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, open]);

  const send = async () => {
    if (!input.trim() || busy) return;
    const text = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const r = await sendChat(text, session);
      setSession(r.session_token);
      setMsgs((m) => [...m, { role: "assistant", text: r.reply }]);
    } catch {
      setMsgs((m) => [...m, { role: "assistant", text: "I'm temporarily unable to answer. Please contact Rajib: rajibmahata143@gmail.com / +91 84202 49020." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed bottom-20 md:bottom-6 right-4 z-50 flex flex-col items-end gap-3">
      {open && (
        <div
          className="w-80 max-w-[calc(100vw-2rem)] overflow-hidden"
          style={{
            background: "rgba(255, 255, 255, 0.88)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            border: "1px solid rgba(15, 18, 34, 0.08)",
            borderRadius: 20,
            boxShadow: "0 20px 60px rgba(15, 18, 34, 0.12), 0 0 40px rgba(124, 58, 237, 0.08)",
            animation: "rlzChatUp 0.4s cubic-bezier(0.22, 1, 0.36, 1)",
          }}
          role="dialog"
          aria-label="Talk to RajibLabs"
        >
          <div
            className="px-4 py-3 flex items-center gap-3"
            style={{ borderBottom: "1px solid rgba(15, 18, 34, 0.08)", background: "rgba(255,255,255,0.5)" }}
          >
            <span
              className="w-9 h-9 grid place-items-center flex-shrink-0"
              style={{
                borderRadius: 12,
                background: "linear-gradient(135deg, #7c3aed, #06b6d4)",
                boxShadow: "0 8px 20px rgba(124, 58, 237, 0.35)",
                color: "#fff",
              }}
            >
              <i className="material-symbols-outlined" style={{ fontSize: "1.15rem" }}>smart_toy</i>
            </span>
            <div className="flex-1 min-w-0">
              <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: 700, fontSize: 14, color: "#0f1222", lineHeight: 1.2 }}>
                Talk to RajibLabs
              </div>
              <div className="flex items-center gap-1.5" style={{ fontSize: 11, color: "#059669", fontWeight: 500 }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
                Online — replies instantly
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="w-7 h-7 rounded-full grid place-items-center flex-shrink-0"
              style={{ color: "#8a8fa8", background: "#eef0f9" }}
              aria-label="Close chat"
            >
              <i className="material-symbols-outlined" style={{ fontSize: 16 }}>close</i>
            </button>
          </div>

          <div ref={scrollRef} className="h-64 overflow-y-auto p-3 space-y-2 text-sm">
            {msgs.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <span
                  className="inline-block px-3 py-2"
                  style={{
                    borderRadius: 14,
                    maxWidth: "85%",
                    wordBreak: "break-word",
                    fontFamily: "'Inter', sans-serif",
                    fontSize: 13,
                    lineHeight: 1.5,
                    background: m.role === "user"
                      ? "linear-gradient(135deg, #7c3aed, #06b6d4)"
                      : "#eef0f9",
                    color: m.role === "user" ? "#fff" : "#0f1222",
                    boxShadow: m.role === "user" ? "0 4px 14px rgba(124, 58, 237, 0.3)" : "none",
                  }}
                >
                  {m.text}
                </span>
              </div>
            ))}
            {busy && (
              <div className="text-left">
                <span
                  className="inline-block px-3 py-2"
                  style={{ borderRadius: 14, background: "#eef0f9", color: "#8a8fa8", fontSize: 13 }}
                >
                  typing…
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-2 p-3" style={{ borderTop: "1px solid rgba(15, 18, 34, 0.08)" }}>
            <input
              value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask about projects…"
              className="flex-1 px-3 py-2.5 text-sm"
              style={{
                borderRadius: 12,
                background: "#f7f8fc",
                border: "1px solid rgba(15, 18, 34, 0.08)",
                color: "#0f1222",
                fontFamily: "'Inter', sans-serif",
                outline: "none",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(124, 58, 237, 0.45)"; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(15, 18, 34, 0.08)"; }}
              aria-label="Chat message"
            />
            <button
              onClick={send} disabled={busy}
              className="w-11 grid place-items-center flex-shrink-0 transition-all disabled:opacity-50"
              style={{
                borderRadius: 12,
                background: "linear-gradient(135deg, #7c3aed, #06b6d4)",
                boxShadow: "0 8px 20px rgba(124, 58, 237, 0.35)",
                color: "#fff",
              }}
              aria-label="Send"
            >
              <i className="material-symbols-outlined" style={{ fontSize: 20 }}>send</i>
            </button>
          </div>
          <style>{`@keyframes rlzChatUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }`}</style>
        </div>
      )}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-14 h-14 grid place-items-center transition-all"
        style={{
          borderRadius: "50%",
          background: "linear-gradient(135deg, #7c3aed, #06b6d4)",
          boxShadow: "0 12px 40px rgba(124, 58, 237, 0.4)",
          color: "#fff",
        }}
        onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-3px)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}
        aria-label={open ? "Close chat" : "Talk to RajibLabs"}
      >
        <i className="material-symbols-outlined" style={{ fontSize: 26 }}>{open ? "close" : "forum"}</i>
      </button>
    </div>
  );
}
