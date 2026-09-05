import { PageHead, Panel } from "../../components/admin/ui";

const ROWS: [string, string][] = [
  ["Admin credentials", "Set ADMIN_INITIAL_PASSWORD (and admin emails) in the backend .env. First login creates the DB user."],
  ["JWT", "SECRET_KEY / JWT_SECRET (32+ chars). Token in HttpOnly cookie rlabs_access."],
  ["GitHub", "GITHUB_TOKEN + GITHUB_OWNER=rajibmahata — server-only, never exposed to the browser."],
  ["AI", "OPENAI_API_KEY (chat model gpt-5-nano) + optional DEEPSEEK_API_KEY fallback. AI_PROVIDER selects the primary."],
  ["RAG / Qdrant", "QDRANT_URL (docker service qdrant:6333). MongoDB stays source of truth; vectors re-index automatically."],
  ["Uploads", "10MB, PDF/DOCX only, safe filenames, not directly enumerable."],
  ["Deploy", "frontend/dist via FTP; MongoDB data persists in the mongo_data volume — back up before major deploys."],
];

export default function Settings() {
  return (
    <div>
      <PageHead title="Settings" desc="Environment & platform configuration reference." />
      <Panel title="Configuration" sub="Values live in rajiblabs-ai-backend/.env (see .env.example)">
        {ROWS.map(([k, v]) => (
          <div className="rla-status-row" key={k}>
            <span className="rla-status-icon" style={{ background: "var(--rla-violet-soft)", color: "var(--rla-violet)" }}><i className="fas fa-gear" /></span>
            <div><div className="rla-st-name">{k}</div><div className="rla-st-sub">{v}</div></div>
          </div>
        ))}
      </Panel>
    </div>
  );
}
