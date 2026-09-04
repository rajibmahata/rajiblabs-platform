import { useEffect, useRef, useState } from "react";
import { sendChat } from "../services/api";

// NOTE: rendered INSIDE <main class="rlz"> (see Home.tsx) so every
// .rlz-* class below resolves to the homepage design tokens.
const QUICK_REPLIES = ["What do you build?", "Show projects", "Contact details"];

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
  }, [msgs, open ]);

  const sendText = async (raw: string) => {
    const text = raw.trim();
    if (!text || busy) return;
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
        <div className="rlz-chat-panel" role="dialog" aria-label="Talk to RajibLabs">
          <div className="rlz-chat-head">
            <span className="rlz-bento-icon rlz-icon-violet">
              <i className="material-symbols-outlined">smart_toy</i>
            </span>
            <div className="flex-1 min-w-0">
              <p className="rlz-chat-title">Talk to RajibLabs</p>
              <span className="rlz-chat-status"><span className="rlz-live-dot" /> Online — replies instantly</span>
            </div>
            <button className="rlz-chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              <i className="material-symbols-outlined">close</i>
            </button>
          </div>

          <div ref={scrollRef} className="rlz-chat-log">
            {msgs.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <span className={`rlz-chat-msg ${m.role === "user" ? "rlz-chat-user" : "rlz-chat-ai"}`}>{m.text}</span>
              </div>
            ))}
            {busy && (
              <div className="text-left">
                <span className="rlz-chat-msg rlz-chat-typing">typing…</span>
              </div>
            )}
          </div>

          <div className="rlz-chat-quick">
            {QUICK_REPLIES.map((q) => (
              <button key={q} className="rlz-chip" onClick={() => void sendText(q)} disabled={busy}>
                {q}
              </button>
            ))}
          </div>

          <div className="rlz-chat-bar">
            <input
              value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void sendText(input)}
              placeholder="Ask about projects…" className="rlz-chat-input" aria-label="Chat message"
            />
            <button className="rlz-chat-send" onClick={() => void sendText(input)} disabled={busy} aria-label="Send">
              <i className="material-symbols-outlined">send</i>
            </button>
          </div>
        </div>
      )}
      <button className="rlz-chat-launcher" onClick={() => setOpen((o) => !o)} aria-label={open ? "Close chat" : "Talk to RajibLabs"}>
        <i className="material-symbols-outlined">{open ? "close" : "forum"}</i>
      </button>
    </div>
  );
}
