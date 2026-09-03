import { useState } from "react";
import { sendChat } from "../services/api";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<{ role: string; text: string }[]>([
    { role: "assistant", text: "Hi — I'm RajibLabs assistant. Ask about projects, technologies, or starting an enquiry." },
  ]);
  const [input, setInput] = useState("");
  const [session, setSession] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);

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
    <div className="fixed bottom-20 md:bottom-6 right-4 z-50 flex flex-col items-end gap-2">
      {open && (
        <div className="w-80 max-w-[calc(100vw-2rem)] rounded-2xl border overflow-hidden" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
          <div className="px-4 py-2 text-sm font-semibold" style={{ background: "#1547be", color: "#fff" }}>Talk to RajibLabs</div>
          <div className="h-64 overflow-y-auto p-3 space-y-2 text-sm">
            {msgs.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <span className="inline-block px-3 py-1.5 rounded-xl" style={{ background: m.role === "user" ? "#1547be" : "rgba(255,255,255,0.06)", color: "#F0F4FF" }}>{m.text}</span>
              </div>
            ))}
          </div>
          <div className="flex gap-2 p-2 border-t" style={{ borderColor: "var(--c-border)" }}>
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask about projects…" className="flex-1 px-3 py-2 rounded-lg text-sm" style={{ background: "var(--c-bg-tertiary)", color: "var(--c-text-primary)" }} aria-label="Chat message" />
            <button onClick={send} disabled={busy} className="px-3 py-2 rounded-lg text-sm text-white" style={{ background: "#1547be" }} aria-label="Send">➤</button>
          </div>
        </div>
      )}
      <button onClick={() => setOpen((o) => !o)} className="w-12 h-12 rounded-full text-white shadow-lg" style={{ background: "#1547be" }} aria-label="Open chat">💬</button>
    </div>
  );
}
