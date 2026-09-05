/* Shared admin template primitives — every /admin/* page uses these. */
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function PageHead({ title, desc, actions }: { title: string; desc?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="rla-page-head">
      <div><h1>{title}</h1>{desc && <p>{desc}</p>}</div>
      {actions && <div className="rla-head-actions">{actions}</div>}
    </div>
  );
}

export function Panel({ title, sub, linkTo, linkLabel, action, children }: {
  title: string; sub?: string; linkTo?: string; linkLabel?: string;
  action?: ReactNode; children: ReactNode;
}) {
  return (
    <div className="rla-panel">
      <div className="rla-panel-head">
        <div><h3>{title}</h3>{sub && <p>{sub}</p>}</div>
        {action || (linkTo && (
          <Link to={linkTo} className="rla-panel-link">{linkLabel || "Manage"} <i className="fas fa-arrow-right" /></Link>
        ))}
      </div>
      <div className="rla-panel-body">{children}</div>
    </div>
  );
}

const OK = new Set(["published", "active", "live", "synced", "ok", "online", "ready", "healthy", "submitted", "won", "success"]);
const ERR = new Set(["failed", "error", "down", "lost", "not synced", "missing", "denied"]);
const WARN = new Set(["draft", "review", "pending", "stale", "warn", "new", "spam", "archived", "hidden", "ignored"]);
const INFO = new Set(["info", "proposal", "qualified", "contacted"]);

export function StatusPill({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  const kind = OK.has(s) ? "ok" : ERR.has(s) ? "err" : WARN.has(s) ? "warn" : INFO.has(s) ? "info" : "muted";
  return <span className={`rla-pill ${kind}`}>{(status || "—").toUpperCase()}</span>;
}

export function Chip({ active, onClick, children }: { active?: boolean; onClick: () => void; children: ReactNode }) {
  return <button onClick={onClick} className={`rla-chip${active ? " active" : ""}`}>{children}</button>;
}

export function Field({ label, children, span }: { label: string; children: ReactNode; span?: boolean }) {
  return (
    <label className="rla-field" style={span ? { gridColumn: "1 / -1" } : undefined}>
      <span className="rla-label">{label}</span>
      {children}
    </label>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rla-empty">{children}</div>;
}
