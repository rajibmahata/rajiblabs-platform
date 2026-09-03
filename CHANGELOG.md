# Changelog

All notable changes to the RajibLabs platform. Dates in UTC.

## [Unreleased] — .NET API removed, all APIs on Python (FastAPI + MongoDB)

Joint work with the parallel agent (removal, seeds, CI/run-script cutover, route test) — consolidated to a single port.

### Removed
- Deleted `backend/RajibLabs.Api/` (.NET 8 + SQLite: `Program.cs`, EF models/`LabDbContext`, Docker assets, tracked `rajiblabs.db`; resume PDF preserved via move to `rajiblabs-ai-backend/data/`). DB recoverable from git history for migration.
- Deleted orphaned `scripts/admin_server.py` (SQLite-backed mini-admin with hardcoded credentials; unreferenced).
- Removed `dotnet-api` from `docker-compose.yml` (ai-api moved to host `:8090`); nginx now routes all `/api/` to FastAPI.
- Removed .NET from CI (`setup-dotnet`, restore/build/publish, backend artifacts, backend FTP mirror), `run.bat` (rewritten: frontend-native + `docker` delegate mode), and `.gitignore` backend entries.

### Added — `app/routers/legacy.py`: Site API (v1), 47 routes, same paths + camelCase shapes
- Public: `GET /api/projects|projects/{id}|activity|profile|health|learning|portfolio|portfolio/{slug}|products|products/{slug}|content/{key}|resume/current`, `POST /api/contact|activity*|learning|subscribe|unsubscribe`, `PATCH /api/projects/{id}*` (*`X-Api-Key`, unchecked when `API_KEY` empty — new setting, mirrors .NET).
- Legacy admin auth: `POST /api/admin/login|logout`, `GET /api/admin/me` (same BCrypt admin store, dual-email; sets `rlabs_token` + `rlabs_access` cookies).
- Admin parity: dashboard (exact legacy shape), profile GET/PUT, portfolio + products CRUD, GitHub repos/sync-log/heuristic-sync/PATCH (dotnet `review`/`professional`/`ai`/`dotnet` semantics, manual edits preserved), resumes full cycle (upload/download/publish/delete, extraction + decision), content list/PUT.
- New collections: `legacy_projects`, `activities`, `profiles`, `contacts`, `courses`, `subscribers`, `portfolio`, `legacy_repos`, `sync_logs`, `website_contents`, `resume_extractions`. Reuses seeded `products`, `website_contents`, `resumes`.
- Consolidation: the parallel `legacy_admin.py` (28-route subset on conflicting collections) was removed in favor of this single router; route-param convention is `{rid}` (contract test normalizes names).

### Data — `scripts/migrate_sqlite_to_mongo.py` migrates all 14 tables
- `legacy_id` preservation, idempotent re-runs (matched by id/slug/key/url/email). Verified live against real MongoDB: test DB (4 projects, 6 activities, 1 profile, 5 courses) migrated, `init_db` seeded the rest (products 2, content 1, resume 1 from PDF). Public + admin + CRUD round-trip verified (both admin emails login, dashboard counts, portfolio publish/edit/delete, subscribe idempotency).

### Fixed along the way
- `ensure_indexes`: `db or get_db()` crashes on Motor (`__bool__` raises) — startup would have failed once lifespan was wired; now `get_db() if db is None`.
- **passlib 1.7.4 + bcrypt≥4.1 is broken** (raises on its own probe) — `app/auth/utils.py` now uses `bcrypt` directly; `requirements.txt` swaps `passlib[bcrypt]` → `bcrypt>=4.1`. Hash/verify + .NET-hash compat verified.
- `POST /api/subscribe` returns 200 for existing/reactivated (was hardcoded 201).

### Tests — `pytest -q`: 11 passed, 2 skipped
- `test_legacy_public_shapes` (paths + camelCase keys, Mongo-gated skip), `test_legacy_validation_no_db` (400/401 gates without DB), `test_legacy_routes_registered` (normalized names). `tsc --noEmit`: clean.

### Changed
- `frontend/src/services/auth.ts` is FastAPI-only (`/api/admin/auth/*`); `vite.config.ts` proxy → `localhost:8000`; `run-docker.bat` simplified to frontend :5010 / API :8090 / Mongo :27017.
- Docs updated: root `README.md`, `IMPLEMENTATION_PLAN.md`, `rajiblabs-ai-backend/README.md`.
- Supersedes the coexistence notes below: dual-backend entries (validation gaps, .NET Swagger) describe the retired setup; gap items 1–5 are closed by this port.

### ⚠️ Production note
- SmarterASP previously served `/api/*` from the .NET publish output. Until FastAPI is hosted for production, **do not wipe the live `/rajiblabs` backend files** — CI now deploys frontend `dist/` only. Point production `/api` at the FastAPI host (set `VITE_API_BASE` or proxy) before removing server-side .NET artifacts.

## [Unreleased] — 2026-09-03 — Swagger for both APIs

### Added
- **FastAPI Swagger** (`rajiblabs-ai-backend`): full OpenAPI metadata (description, contact, license, 10 tag groups), every operation tagged (41 ops, zero untagged), Bearer Authorize button via existing JWT scheme. Served at `/docs` (Swagger UI), `/redoc`, `/openapi.json` in non-production; **all three now consistently disabled in production** (previously only `/docs` was gated — `/redoc` + `/openapi.json` leaked in prod). Regression test `test_swagger_spec_tagged` added (`pytest -q`: 8 passed, 1 skipped).
- **.NET Swagger** (`backend/RajibLabs.Api`): Swashbuckle 6.6.2 (`AddEndpointsApiExplorer` + `AddSwaggerGen` with "RajibLabs API (.NET)" doc info and Bearer security definition/requirement for the `POST /api/admin/login` JWT, incl. `rlabs_token` cookie note). UI + `swagger.json` served in Development always, in Production only with `Swagger:Enabled=true`. Verified live: dev → 37 paths + UI 200 + Bearer scheme; prod → 404. `dotnet build`: 0 errors (2 pre-existing warnings untouched).

### Docs
- `rajiblabs-ai-backend/README.md`: new "API docs (Swagger)" section; root `README.md`: Swagger rows in the API tables.

## [Unreleased] — 2026-09-03 — Gap fixes + admin System Logs (5-day retention)

### Fixed (all 7 gaps from the 2026-09-03 validation report)
1. **nginx routing** (`frontend/nginx.conf`): added FastAPI locations for `/api/admin/projects`, `/api/admin/logs`, `= /api/admin/github/status`, `/api/admin/github/repositories`; removed the dead `/api/admin/qa` rule (real path `/api/admin/agent/qa` was already covered by the `/api/admin/agent/` prefix). `/api/admin/dashboard` and `/api/admin/github/repos|sync-log` intentionally stay on .NET — the React admin pages depend on the .NET response shapes.
2. **`app/main.py` startup**: `lifespan` is now passed to `FastAPI()` so `init_db` + scheduler start correctly; deprecated `@app.on_event("startup")` double-init removed (also clears the FastAPI deprecation warning in tests).
3. **Dashboard serialization** (`GET /api/admin/dashboard`): `last_sync`/`last_agent` now converted with `oid_str`, `None`-guarded — no more `ObjectId` 500 risk.
4. **Resume fields**: upload now stores canonical `stored_path`/`filename`/`size_bytes`; public `GET /api/public/resume` strips both `stored_path` and legacy `path`; `/resume/download` reads `stored_path` with legacy-`path` fallback and returns 404 (instead of `KeyError` 500) when the file is missing.
5. **Admin CMS parity**: decision confirmed — .NET stays authoritative for profile/portfolio/products/content/resumes/github-repos admin paths until FastAPI ports land; documented in nginx + `IMPLEMENTATION_PLAN.md §8`.
6. **Test coverage**: suite grew 4 → 9 tests — added lifespan-wiring, log-truncation unit, auth-gate, and Swagger-spec tests for `/api/admin/logs|stats|dashboard|projects|leads` (all Mongo-independent). `pytest -q`: **8 passed, 1 skipped**.
7. **`.env.example` drift**: added all 15 missing keys (`BASE_URL`, `CORS_ORIGINS`, `APP_TIMEZONE`, `MONGO_DB_NAME`, `JWT_EXPIRE_MINUTES`, `REFRESH_EXPIRE_DAYS`, `JWT_ISSUER`, `OPENAI_MAX_RETRIES`, `AI_QUALITY_THRESHOLD`, `DAILY_AGENT_HOUR/MINUTE`, `LOG_RETENTION_DAYS`, `UPLOAD_DIR`, `MAX_IMAGE_MB`, `MAX_RESUME_MB`). `tsc --noEmit` on frontend: clean.

### Added — admin System Logs section (failures kept 5 days)
- New `error_logs` Mongo collection: `{level: error|warning, source, message, details, created_at}`, text capped (source 120 / message 500 / details 2000 chars) so one failure can't bloat the DB.
- **5-day retention** via TTL index on `created_at` (`expireAfterSeconds = LOG_RETENTION_DAYS * 86400`, default 5, configurable); index auto-rebuilt if the setting changes; supporting indexes on `(level, created_at)`, `(source, created_at)`.
- Failure capture wired (each guarded so logging can never break the fallback path): `daily_agent` failure → `error`; `github_sync` failure → `error`; OpenAI enrichment/chat fallback → `warning`.
- Admin API (JWT, FastAPI): `GET /api/admin/logs?level=&source=&limit=` (max 500), `GET /api/admin/logs/stats` (retention window, counts by level/source, newest/oldest), `DELETE /api/admin/logs` (early purge + audit entry). Nginx routes `/api/admin/logs` → ai-api.
- Frontend: new **System Logs** page (`/admin/logs`, nav entry, level filter, expandable details, purge button with confirm, empty-healthy state).

## [Unreleased] — 2026-09-03 — Backend sync & validation (FastAPI + .NET coexistence)

### Sync with other agent
- Reviewed the FastAPI + MongoDB backend (`rajiblabs-ai-backend/`, commit `4251c3c`) built by the parallel agent against the requirement spec (`proposals/rajiblabs-ai-backend-master-prompt.md`) and `IMPLEMENTATION_PLAN.md`.
- Confirmed coexistence strategy: **both backends run side-by-side** via Docker (`dotnet-api:8090`, `ai-api:8091`) with nginx routing (`frontend/nginx.conf`) splitting `/api/*` by prefix. Legacy `.NET 8 + SQLite` API stays authoritative for the React admin panel; FastAPI + MongoDB serves new public CMS (`/api/public/*`), chat/leads, AI rewrite, and daily-agent endpoints. No data loss, no breaking change to the live admin.
- Frontend `App.tsx` detail pages (`/portfolio/:slug`, `/products/:slug`) and `services/api.ts` (`getCmsProjects`, `sendChat`, `submitLead`) already try FastAPI first with graceful fallback — parity path verified in code.

### Validation — PASS with known gaps (see below)
- `pytest -q` in `rajiblabs-ai-backend/`: **3 passed, 1 skipped** (MongoDB not running locally; `test_public_projects_published_only` skips gracefully). Health, GitHub-URL validator, and quality-gate tests green.
- `python scripts/run_qa.py`: pytest PASS; secret scan reports 2 hits, both false positives (empty `OPENAI_API_KEY` placeholders in `.env.example` and the spec doc). No hardcoded `sk-`/`ghp_` keys or passwords in `app/` or `scripts/`.
- `py_compile` over all `app/` modules: OK.
- Route inventory (38 endpoints) verified against code: health, 9 public CMS, 3 admin-auth, 9 admin-CMS (dashboard/projects/leads/notifications), 4 GitHub, 4 AI, 3 agent, 3 chat/lead/quote, 2 resume.
- Security spot-checks: JWT access (15 min) + refresh (7 d, HttpOnly `Secure; SameSite=Strict`) cookies; login rate-limit 5/min/IP; bcrypt hashing; admin seed never overwrites; `GITHUB_TOKEN`/`OPENAI_API_KEY` server-only, masked from responses/logs (`core_logging.RedactFilter`); upload validation (resume PDF/DOCX ≤10 MB, images ≤5 MB, randomized filenames, `stored_path` stripped from public responses); CORS restricted to `localhost:5173` + `https://rajiblabs.com`; no `.env` committed (gitignored).
- Spec deviations recorded as **accepted decisions** (not defects): MongoDB instead of SQLite (§1 stack), React admin instead of Jinja2 panel (§5.2), `/api/public/*` + `/health` paths instead of legacy `/api/*` paths (§4 — nginx + frontend fallback bridge the gap), renamed collections (`customer_conversations/customer_messages/customer_leads`, `github_sync_runs`, `ai_content_versions`), OpenAI model `gpt-5-nano`/`gpt-5.6-luna` instead of `gpt-4o-mini`.

### Known gaps / follow-ups (not regressions — new work for backlog)
1. **nginx routing gaps** (`frontend/nginx.conf`): `/api/admin/dashboard`, `/api/admin/projects`, `GET /api/admin/github/status|repositories`, `POST .../repositories/{rid}/map`, and `/api/admin/agent/qa` have no FastAPI location rule — they fall through to `dotnet-api` (404 on both stacks for the new paths; `/api/admin/qa` rule points at a non-existent FastAPI path, real path is `/api/admin/agent/qa`). Fix by adding explicit locations for each FastAPI prefix.
2. **`app/main.py` startup**: `lifespan` context (init_db + scheduler) is defined but never passed to `FastAPI()`; legacy `@app.on_event("startup")` (deprecated) double-runs `init_db` without starting the scheduler. Fix: `FastAPI(lifespan=lifespan)`, drop `on_event`.
3. **`GET /api/admin/dashboard` serialization**: returns raw `last_sync`/`last_agent` Mongo docs containing `ObjectId` — will 500 on JSON encode. Wrap with `oid_str` and guard `None`.
4. **Resume field mismatch**: upload stores `path`/`filename`/`size`, public `GET /api/public/resume` + `/resume/download` read `stored_path`/`filename` — download raises `KeyError`. Unify on one field name and guard missing file with 404.
5. **Admin CMS parity incomplete** (frontend admin still wired to .NET paths): `/api/admin/profile`, `/api/admin/portfolio`, `/api/admin/products`, `/api/admin/content`, `/api/admin/resumes*`, `/api/admin/github/repos`, `/api/admin/github/sync-log` exist only on .NET. Either keep .NET authoritative (current, working) or port these to FastAPI before switching nginx.
6. **Test coverage**: only 4 tests; master-prompt QA checklist §11 items (auth, CRUD, chat, agents with mocks) not yet automated. `scripts/run_qa.py` records to `agent_runs` only when Mongo is up (graceful warning otherwise — accepted).
7. **`.env.example` drift**: missing `JWT_EXPIRE_MINUTES`, `REFRESH_EXPIRE_DAYS`, `JWT_ISSUER`, `DAILY_AGENT_HOUR/MINUTE`, `MAX_IMAGE_MB`, `MAX_RESUME_MB`, `UPLOAD_DIR`, `MONGO_DB_NAME`, `APP_TIMEZONE` keys present in `config.py`. Add them so fresh setup matches code.

## 4251c3c — 2026-09-02 — feat: FastAPI + MongoDB AI portfolio CMS (replaces SQLite plan, .NET kept intact)
- New `rajiblabs-ai-backend/` (FastAPI, Motor/MongoDB, APScheduler daily agent, OpenAI content engine with hash-dedup + quality gate, GitHub sync preserving `is_manually_edited`, chat with knowledge fallback + rate limits, dual-email admin auth).
- Frontend: `ChatWidget`, `VITE_API_BASE` admin helper, CMS detail pages, `robots.txt`/`sitemap.xml`, admin layout updates.
- Dual-backend Docker + nginx split; `scripts/` for `create_admin`, `run_agent`, `run_qa`, SQLite→Mongo migration.

## ddea60c — 2026-09-01 — chore: agents/Design replaces stitch_* portfolio redesign assets
## 32bda2c — 2026-08-31 — fix: unified API deploy (`frontend/wwwroot` + backend to `/rajiblabs`)
