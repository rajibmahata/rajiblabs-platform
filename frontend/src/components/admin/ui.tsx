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

const OK = new Set(["published", "active", "live", "synced", "ok", "online", "ready", "healthy", "submitted", "won", "success", "sent", "delivered", "subscribed", "customer", "converted", "hot"]);
const ERR = new Set(["failed", "error", "down", "lost", "not synced", "missing", "denied", "unsubscribed", "cancelled", "bounced"]);
const WARN = new Set(["draft", "review", "pending", "stale", "warn", "new", "spam", "archived", "hidden", "ignored", "scheduled", "sending", "paused", "queued", "skipped", "warm", "cold", "follow_up"]);
const INFO = new Set(["info", "proposal", "qualified", "contacted", "opened", "clicked"]);

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

export function InlineLoader({ text = "Loading..." }: { text?: string }) {
  return (
    <span className="rla-inline-loader" aria-live="polite" aria-busy="true">
      <i className="fas fa-spinner fa-spin" aria-hidden="true" />
      <span>{text}</span>
    </span>
  );
}

export function BlockLoader({ text = "Loading...", sub }: { text?: string; sub?: string }) {
  return (
    <div className="rla-block-loader" role="status" aria-live="polite" aria-busy="true">
      <span className="rla-loader-ring" aria-hidden="true"><i className="fas fa-spinner fa-spin" /></span>
      <div>
        <b>{text}</b>
        {sub && <span>{sub}</span>}
      </div>
    </div>
  );
}

export function StepProgress({
  steps,
  current,
  status = "processing",
}: {
  steps: string[];
  current: number;
  status?: "processing" | "done" | "error";
}) {
  return (
    <div className="rla-step-progress" role="status" aria-live="polite" aria-busy={status === "processing"}>
      {steps.map((label, i) => {
        const isDone = i < current;
        const isCurrent = i === current && status === "processing";
        const isError = i === current && status === "error";
        return (
          <div key={label} className={`rla-step ${isDone ? "done" : ""} ${isCurrent ? "current" : ""} ${isError ? "error" : ""}`}>
            <span className="rla-step-dot" aria-hidden="true">
              {isDone ? <i className="fas fa-check" /> : isCurrent ? <i className="fas fa-spinner fa-spin" /> : isError ? <i className="fas fa-exclamation" /> : <span>{i + 1}</span>}
            </span>
            <span className="rla-step-label">{label}</span>
            {isCurrent && <span className="rla-step-pulse" aria-hidden="true" />}
          </div>
        );
      })}
    </div>
  );
}

export function AsyncButton({
  loading,
  loadingText,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean; loadingText?: string }) {
  return (
    <button {...props} disabled={loading || props.disabled} aria-busy={loading ? "true" : undefined} className={`${props.className || ""} ${loading ? "is-loading" : ""}`.trim()}>
      {loading ? <InlineLoader text={loadingText || "Working..."} /> : children}
    </button>
  );
}
