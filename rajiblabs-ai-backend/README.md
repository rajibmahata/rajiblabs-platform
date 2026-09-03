# RajibLabs AI Backend (FastAPI + MongoDB)

Production-ready AI-assisted portfolio CMS backend. The sole API (the legacy .NET+SQLite API was removed; all its paths live on here as Site API v1 under `app/routers/legacy.py`).

## Architecture

Browser (React, SmarterASP `/rajiblabs`) → FastAPI (`/api/public/*`, `/api/admin/*`) → MongoDB → GitHub API / OpenAI (server-only) → APScheduler daily agent → notifications.

## Setup

```bash
cp .env.example .env   # fill ADMIN_INITIAL_PASSWORD, SECRET_KEY, JWT_SECRET, GITHUB_TOKEN, OPENAI_API_KEY
docker compose up -d   # mongo + api on :8000 (root compose maps host :8090)
# or local:
pip install -r requirements.txt
python scripts/create_admin.py   # first admin only; never overwrites
uvicorn app.main:app --reload
```

Local Mongo without Docker: `DATABASE_URL=mongodb://localhost:27017/rajiblabs`.

## API docs (Swagger)

- Swagger UI: `GET /docs` · ReDoc: `GET /redoc` · spec: `GET /openapi.json` (all disabled in production; ~90 operations across 11 tag groups incl. Site API v1, JWT Authorize button).

## Database

MongoDB `rajiblabs`. Collections: `admins, site_settings, homepage_content, skills, experience, projects, project_links, github_repositories, github_commits, ai_content_versions, ai_jobs, customer_conversations, customer_messages, customer_leads, notifications, agent_runs, audit_logs, resumes`. Indexes created in `init_db`. Seed: homepage, skills, experience, 5 verified projects (PestFlow repo verified; others `github_url=NULL`), contact settings.

Migrate legacy SQLite (one-shot; `backend/` was removed — extract `rajiblabs.db` from git history first, then pass its path): `python scripts/migrate_sqlite_to_mongo.py /path/to/rajiblabs.db`.

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

## Validation (2026-09-03, synced with .NET-backend agent)

- `pytest -q`: **3 passed, 1 skipped** (Mongo-down skip is by design). `python scripts/run_qa.py`: pytest PASS, secret scan clean (2 placeholder-only hits).
- Route inventory (38): `GET /health`; public `GET /api/public/site|home|skills|experience|projects|projects/{slug}|products|resume|resume/download`; `POST /api/public/chat|leads|quote`; admin-auth `POST /api/admin/auth/login|logout`, `GET /api/admin/auth/me`; admin-CMS `GET /api/admin/dashboard`, `GET|POST /api/admin/projects`, `PUT|DELETE /api/admin/projects/{pid}`, `GET /api/admin/notifications`, `PUT .../notifications/{nid}/read`, `GET /api/admin/leads`, `PUT /api/admin/leads/{lid}`; GitHub `GET /api/admin/github/status`, `POST .../sync`, `GET .../repositories`, `POST .../repositories/{rid}/map`; AI `POST /api/admin/ai/rewrite/{pid}|review/{pid}`, `POST .../versions/{vid}/decision`, `GET .../versions/{pid}`; agent `POST /api/admin/agent/run`, `GET .../runs|qa`; resume `POST|GET /api/admin/resume`.
- Parity with master spec (`proposals/rajiblabs-ai-backend-master-prompt.md`): accepted deviations — MongoDB (not SQLite), React admin (not Jinja2), `/api/public/*` paths (not legacy `/api/*`, bridged by nginx + frontend fallback), `customer_*`/`github_sync_runs`/`ai_content_versions` collection names, `gpt-5-nano` model. See repo `CHANGELOG.md` + `IMPLEMENTATION_PLAN.md §8` for the full report.
- Known gaps before cutover (all in `CHANGELOG.md`): nginx missing locations for `/api/admin/dashboard|projects`, `/api/admin/github/status|repositories|map`, `/api/admin/agent/qa`; `main.py` lifespan not wired (scheduler never auto-starts) + deprecated `on_event`; dashboard `ObjectId` serialization; resume `path` vs `stored_path` mismatch; admin profile/portfolio/products/content/resumes endpoints still .NET-only; test suite needs auth/CRUD/chat/agent mocked tests; `.env.example` needs 9 more keys from `config.py`.

## System Logs (failures, 5-day retention)

Every backend failure is recorded to the `error_logs` collection (`level` error|warning, `source`, `message`, `details`, `created_at`; text length-capped). A MongoDB TTL index on `created_at` auto-deletes entries after `LOG_RETENTION_DAYS` (default 5). Captured today: daily-agent failure, GitHub-sync failure, OpenAI enrichment/chat fallbacks (warning). Admin: `GET /api/admin/logs?level=&source=&limit=`, `GET /api/admin/logs/stats`, `DELETE /api/admin/logs` (early purge); frontend page at `/admin/logs`.

> Status 2026-09-03: all items above fixed, including the former .NET-authoritative admin parity decision — the full .NET surface (47 routes) is now ported (`legacy.py` Site API v1) and the .NET API is removed. Tests: `pytest -q` 11 passed, 2 skipped (post-removal).
