/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { toast } from "../../components/admin/toast";

export default function TokenBudgetPage() {
  const [budget, setBudget] = useState<any>(null);
  const [check, setCheck] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<any>("/api/admin/ops/token-budget"),
      api.get<any>("/api/admin/ops/token-budget/check"),
    ]).then(([b, c]) => { setBudget(b); setCheck(c); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/api/admin/ops/token-budget", budget);
      toast("Saved", "Token budget updated");
      const c = await api.get<any>("/api/admin/ops/token-budget/check");
      setCheck(c);
    } catch (e) {
      toast("Save failed", String(e instanceof Error ? e.message : e).slice(0, 120));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-6 text-center" style={{ color: "var(--rla-text-dim)" }}>Loading…</div>;
  if (!budget) return <div className="p-6 text-center" style={{ color: "var(--rla-red)" }}>Failed to load budget.</div>;

  const update = (key: string, val: any) => setBudget((b: any) => ({ ...b, [key]: val }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>
        <i className="fas fa-coins" style={{ marginRight: 8, color: "var(--rla-amber)" }} />
        Token Budget & Controls
      </h2>

      {/* Current status */}
      {check && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(200px,1fr))", gap: 14 }}>
          {[
            { label: "Today Tokens", value: `${(check.today_tokens ?? 0).toLocaleString()}`, color: "var(--rla-cyan)" },
            { label: "Daily Remaining", value: check.daily_remaining === -1 ? "Unlimited" : `${(check.daily_remaining ?? 0).toLocaleString()}`, color: check.daily_remaining === 0 ? "var(--rla-red)" : "var(--rla-green)" },
            { label: "Month Tokens", value: `${(check.month_tokens ?? 0).toLocaleString()}`, color: "var(--rla-violet)" },
            { label: "Monthly Remaining", value: check.monthly_remaining === -1 ? "Unlimited" : `${(check.monthly_remaining ?? 0).toLocaleString()}`, color: check.monthly_remaining === 0 ? "var(--rla-red)" : "var(--rla-green)" },
          ].map((s) => (
            <div key={s.label} style={{ background: `${s.color}08`, border: `1px solid ${s.color}20`, borderRadius: 12, padding: "14px 16px" }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 11, color: "var(--rla-text-dim)" }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Budget config */}
      <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Budget Configuration</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label style={{ fontSize: 12, color: "var(--rla-text-dim)", display: "block", marginBottom: 4 }}>Daily Token Budget (0 = unlimited)</label>
            <input type="number" value={budget.daily_token_budget || 0} onChange={(e) => update("daily_token_budget", Number(e.target.value))}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 14 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "var(--rla-text-dim)", display: "block", marginBottom: 4 }}>Monthly Token Budget (0 = unlimited)</label>
            <input type="number" value={budget.monthly_token_budget || 0} onChange={(e) => update("monthly_token_budget", Number(e.target.value))}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 14 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "var(--rla-text-dim)", display: "block", marginBottom: 4 }}>Max Tokens Per Request</label>
            <input type="number" value={budget.max_tokens_per_request || 4000} onChange={(e) => update("max_tokens_per_request", Number(e.target.value))}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 14 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "var(--rla-text-dim)", display: "block", marginBottom: 4 }}>Fallback Model</label>
            <input type="text" value={budget.fallback_model || "gpt-4o-mini"} onChange={(e) => update("fallback_model", e.target.value)}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 14 }} />
          </div>
        </div>

        <div style={{ display: "flex", gap: 20, marginTop: 16 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer" }}>
            <input type="checkbox" checked={budget.llm_enabled !== false} onChange={(e) => update("llm_enabled", e.target.checked)} />
            LLM Enabled
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer" }}>
            <input type="checkbox" checked={budget.rag_first_enforced !== false} onChange={(e) => update("rag_first_enforced", e.target.checked)} />
            RAG-First Enforced
          </label>
        </div>

        <div style={{ marginTop: 16 }}>
          <label style={{ fontSize: 12, color: "var(--rla-text-dim)", display: "block", marginBottom: 4 }}>Allowed Models (comma-separated)</label>
          <input type="text" value={(budget.allowed_models || []).join(", ")}
            onChange={(e) => update("allowed_models", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))}
            style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 14 }} />
        </div>

        <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
          <button onClick={() => void save()} disabled={saving}
            className="rla-btn rla-btn-primary rla-btn-sm">
            {saving ? "Saving…" : "Save Budget"}
          </button>
        </div>
      </div>
    </div>
  );
}
