# RajibLabs AI Backend (FastAPI + MongoDB)

Production-ready AI-assisted portfolio CMS backend. Replaces the legacy .NET+SQLite API (kept intact until parity).

## Architecture

Browser (React, SmarterASP `/rajiblabs`) → FastAPI (`/api/public/*`, `/api/admin/*`) → MongoDB → GitHub API / OpenAI (server-only) → APScheduler daily agent → notifications.

## Setup

```bash
cp .env.example .env   # fill ADMIN_INITIAL_PASSWORD, SECRET_KEY, JWT_SECRET, GITHUB_TOKEN, OPENAI_API_KEY
docker compose up -d   # mongo + api on :8000
# or local:
pip install -r requirements.txt
python scripts/create_admin.py   # first admin only; never overwrites
uvicorn app.main:app --reload
```

Local Mongo without Docker: `DATABASE_URL=mongodb://localhost:27017/rajiblabs`.

## Database

MongoDB `rajiblabs`. Collections: `admins, site_settings, homepage_content, skills, experience, projects, project_links, github_repositories, github_commits, ai_content_versions, ai_jobs, customer_conversations, customer_messages, customer_leads, notifications, agent_runs, audit_logs, resumes`. Indexes created in `init_db`. Seed: homepage, skills, experience, 5 verified projects (PestFlow repo verified; others `github_url=NULL`), contact settings.

Migrate legacy SQLite: `python scripts/migrate_sqlite_to_mongo.py ../backend/RajibLabs.Api/rajiblabs.db`.

## Admin setup

`ADMIN_EMAILS=rajibmahata143@gmail.com,rajibmahata143@outlook.com` (one identity, case-insensitive). `POST /api/admin/auth/login` → HttpOnly Secure SameSite cookies. No forgot-password in v1; change via authenticated settings.

## GitHub / OpenAI

`GITHUB_OWNER=rajibmahata`, `GITHUB_TOKEN` server-only. `POST /api/admin/github/sync` (manual) + daily 02:00 Asia/Kolkata. Manual edits/`locked_fields` never overwritten. `OPENAI_MODEL=gpt-5-nano`, fallback `gpt-5.6-luna`; compact prompts (README≤2000 chars), hash dedup, `AI_AUTO_PUBLISH=false` default, threshold 85.

## Scheduler / agent / QA

`POST /api/admin/agent/run` or `python scripts/run_agent.py`. QA: `pytest -q`, `python scripts/run_qa.py` (pytest + secret scan + records `agent_runs`), Playwright E2E per spec §57 (frontend suite). Admin `/admin/agent` shows runs; `/admin/qa` shows status.

## Deployment

Frontend stays on SmarterASP FTP `FTP_PATH=rajiblabs` (unchanged `deploy.sh`/`ci.yml`). FastAPI: Docker locally now, VPS later (`api.rajiblabs.com`, set `VITE_API_BASE`). Never commit `.env`; never expose tokens in responses/logs.

## Troubleshooting

Mongo down → `/health` returns `degraded`; public site uses React fallbacks; sync/AI mark failed and retry. OpenAI down → heuristic summaries, chat falls back to approved knowledge + contact links.
