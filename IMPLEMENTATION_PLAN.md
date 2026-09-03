# RajibLabs — Implementation Plan (Portfolio CMS + GitHub AI Sync)

**Repo:** rajibmahata/rajiblabs-platform | **Prod:** https://rajiblabs.com | **Stack:** React 19 + Vite 8 + Tailwind 4 (PWA) + FastAPI + MongoDB | **Deploy:** GitHub Actions → FTP `win1069.site4now.net` (`frontend/dist` → `/rajiblabs`); API via Docker/VPS. (The legacy .NET 8 + SQLite API was removed; all its paths are ported into FastAPI — see `rajiblabs-ai-backend/app/routers/legacy.py`.)

## 1. Architecture Audit — Findings

**Frontend:** `frontend/src/App.tsx` renders `pages/Home.tsx` (no router) → sections: `Hero, Results, Profile, HowIWork, AppsShowcase, Products, CompletedProjects, WIP, GitHubActivity, Contact` + `layout/GlobalNav, GlobalFooter, MobileBottomBar` + `ui/FloatingContact`. Centralized `config/site.ts` (phone/wa/email/linkedin). PWA: `manifest.webmanifest, sw.js, offline.html`, `pwa/registerSW`. No auth. Types in `types/index.ts` (Project, Profile, Activity). `index.css` Midnight Engineering Design System (already premium, must preserve).

**Backend:** `Program.cs` — SQLite `UseSqlite("Data Source=rajiblabs.db")`, EF `LabDbContext` with `Projects, Activities, Profiles, Contacts, LinkedInCourses, Subscribers`, `EnsureCreated` + `SeedData` (4 projects, profile). APIs: `GET /api/projects, /api/projects/{id}, /api/activity, /api/profile, /api/learning, /api/health, POST /api/contact, /api/subscribe, /api/learning`. Writes protected by `X-Api-Key` filter (`appsettings.json:ApiKey`). No Identity/JWT, no auth, CORS `localhost:5173, rajiblabs.com`. Static files via `UseStaticFiles` (PWA).

**Content:** Professional info hard-coded in `SeedData` + `site.ts`; products/projects seeded; Page Flow not isolated — treated as product/project (spec §14). No CMS, no admin.

**Governance:** `.github/workflows/ci.yml` builds `frontend/dist` (verified PWA artifacts: lint, typecheck, build, manifest/sw/offline checks), then `deploy.sh` FTP to `/rajiblabs`. Needs to preserve `admin`, `api`, `.well-known` on deploy. No backend build in CI (FastAPI deploys via Docker).

## 2. Design Constraints

- Preserve all existing public content/seo/PWA (spec §2). CMS makes it manageable, not replaced.
- `Page Flow` stays as product — dedicated page `/products/page-flow` reusing product model.
- Mobile PWA: full-screen menu, safe-area, bottom CALL/WHATSAPP/EMAIL, no horizontal scroll 320-1920.
- Data ownership: GitHub=metadata source, AI=enrichment, Admin=authority; manual edits never overwritten.

## 3. Database / Content Model (extends SQLite, no migration break)

Existing: `Project, Activity, Profile, Contact, LinkedInCourse, Subscriber`.
Add:
- `AdminUser {Id, Username, PasswordHash, CreatedAt, LastLoginAt}` (single admin initially, role-ready)
- `Resume {Id, FileName, StoredPath, ContentType, SizeBytes, Version, Status(Published/Draft/Archived), UploadedAt, PublishedAt}` + `ResumeExtraction {Id, ResumeId, ExtractedJson, Status(review/approved/rejected), CreatedAt}`
- `PortfolioProject {Id, Title, Slug(unique), ShortDescription, Description, Problem, Solution, Role, Architecture, TechStackJson, AiCapabilitiesJson, CloudCapabilitiesJson, ScreenshotsJson, DemoUrl, GitHubUrl, ProductUrl, Status(draft/review/published/hidden), Featured, DisplayOrder, CreatedAt, UpdatedAt, PublishedAt, LastSyncedAt, IsManualEdit(bool)}`
- `GitHubRepository {Id, GitHubId, Name, FullName, Description, HtmlUrl, Language, TopicsJson, Stars, Forks, UpdatedAt, PushedAt, IsPrivate, DefaultBranch, Readme, License, Classification(professional/product/ai/saas...), AiTitle, AiSummary, AiProblem, AiTechStack, AiConfidence, SyncStatus(review/published/ignored/hidden), LastSyncedAt, IsManuallyEdited, PublishedAt}`
- `Product {Id, Name, Slug(unique), Category, Description, LogoUrl, ScreenshotsJson, FeaturesJson, TechStackJson, AiCapabilities, Architecture, ProductUrl, GitHubRepoId, Status, Featured, DisplayOrder, CreatedAt, UpdatedAt}`
- `ProjectSyncLog {Id, StartedAt, FinishedAt, Found, Added, Updated, Ignored, ErrorsJson}`
- `WebsiteContent {Id, Key(unique), Title, BodyJson, UpdatedAt}` for HOME flow ordering etc.
- Enrich `Profile` with `Headline, Location, Phone, WhatsApp, Email, LinkedIn, GitHub, Website, ProfileImageUrl` (reuse `site.ts` as fallback).

All JSON arrays as `Json` text columns, `HasIndex` on `Slug`, `Email`. (Historical SQLite design — superseded by the MongoDB collections in `rajiblabs-ai-backend/app/database.py`.)

## 4. Admin Auth Foundation (reuse existing ApiKey pattern, extend to JWT)

- `POST /api/admin/login {username,password}` → verify `BCrypt`, issue JWT (15m access + 7d refresh via HttpOnly Secure Cookie `__Host-rlabs`), return user.
- `POST /api/admin/logout` clears cookie.
- `GET /api/admin/me` requires auth.
- Middleware `RequireAdmin` validates cookie/header, protects `/api/admin/*`, `/api/resumes/*`, etc. Rate-limit login (5/min IP), CSRF via SameSite=Strict + double-submit for non-GET.
- Frontend: `/admin/login` form, `/admin` layout with guard (`services/auth.ts` + `components/admin/ProtectedRoute`), `BrowserRouter` added (preserve existing `/`).

Env: `Admin__Username, Admin__PasswordHash, Jwt__Key, Jwt__Issuer, GITHUB_TOKEN, GITHUB_OWNER=rajibmahata`.

## 5. Feature Phases (order per spec §35)

**P1 Audit** — done.
**P2 DB** — add models, update `LabDbContext`, `EnsureCreated` seed admin.
**P3 Auth** — backend JWT + frontend admin shell.
**P4 Resume** — upload/replace/view/download/publish/version, MIME/size/path-traversal guards, `wwwroot/uploads/resumes` not served static directly.
**P5 Portfolio** — CRUD, publish/feature/reorder, detail page `/portfolio/:slug` with SEO.
**P6 Products/Page Flow** — `Product` CRUD, Page Flow seeded as product, `/products/:slug`.
**P7-10 GitHub** — `GET /api/admin/github/sync` server-side `Octokit` via `GITHUB_TOKEN`, upsert `GitHubRepository`, AI enrichment via OpenAI (if `OPENAI_API_KEY` else heuristic), preserve `IsManuallyEdited`, classification, review queue `review/publish/ignore/hidden`.
**P11 Public** — HOME reorganized per §19 using CMS data (fallback to seeded), sections remain.
**P12-13 UI/PWA** — Keep Midnight premium dark, light cards, admin tables clean, mobile full-screen menu + bottom bar.
**P14 Security/tests** — file validation, SQL-inject safe (EF), XSS escape, e2e for auth/resume/portfolio.
**P15 Deploy** — verify `frontend/dist` includes `/admin`, `rajiblabs.db` migrations, secrets not in repo, `deploy.sh` preserves `uploads`.

## 6. Risks & Mitigations

- SQLite file `rajiblabs.db` lost on FTP re-deploy → store outside `wwwroot` or backup; `EnsureCreated` seeds if missing.
- Overwrite manual edits on sync → flag `IsManuallyEdited` per field.
- AI hallucination → editable, confidence low → `review` status.
- Large uploads → 10MB limit.

## 7. Verification Checklist (spec §38)

Auth protects admin APIs, resume CRUD, portfolio/product CRUD, Page Flow visible, GitHub sync + AI + review, public CMS data, mobile 320-1920 no scroll, PWA install, phone/WA/email from `site.ts`/profile, SEO titles, no secret leak, `npm run build` + `pytest -q` pass.

## 8. Backend Sync & Validation Report — 2026-09-03 (other-agent FastAPI build)

**Scope:** validated `rajiblabs-ai-backend/` (commit `4251c3c`) against `proposals/rajiblabs-ai-backend-master-prompt.md` (§§1-11) and this plan. Full detail in `CHANGELOG.md` ([Unreleased] entry).

**Outcome: PASS with known gaps (no regressions).** Coexistence confirmed at the time: .NET 8 + SQLite remained authoritative for the React admin panel while FastAPI + MongoDB served new public CMS, chat/leads, AI rewrite/versioning, daily agent, and GitHub sync. **Superseded — .NET API removed:** all legacy admin paths (`/api/admin/portfolio|products|github/repos|profile|content|resumes|dashboard`, public `/api/portfolio|products|content`) are now ported into FastAPI (`rajiblabs-ai-backend/app/routers/legacy.py` — Site API v1, 47 routes incl. the public surface, camelCase shapes, `legacy_*`/`portfolio`/`sync_logs`/`website_contents` collections); nginx routes all `/api/` to FastAPI; frontend `services/auth.ts` is FastAPI-only.

**Evidence (all re-runnable):**
- `pytest -q` in `rajiblabs-ai-backend/`: 3 passed, 1 skipped (Mongo down → graceful skip). `py_compile` all `app/` modules: OK.
- `python scripts/run_qa.py`: pytest PASS; secret scan 2 hits = false positives (empty `OPENAI_API_KEY` placeholders); no `sk-`/`ghp_` keys in code; CORS = `localhost:5173, https://rajiblabs.com`; no `.env` committed.
- Route inventory: 38 endpoints enumerated from router objects (health 1, public CMS 9, admin-auth 3, admin-CMS 9, GitHub 4, AI 4, agent 3, chat 3, resume 2).

**Accepted spec deviations (decisions, not defects):** MongoDB replaces SQLite (§1); React admin replaces Jinja2 panel (§5.2); `/api/public/*` + `/health` paths replace legacy `/api/*` (§4, bridged by nginx + frontend fallback); renamed collections (`customer_conversations/messages/leads`, `github_sync_runs`, `ai_content_versions`); OpenAI `gpt-5-nano`/`gpt-5.6-luna` replaces `gpt-4o-mini` (§6/§9).

**Requirement deltas carried to backlog (§§4-5, §11):** (1) nginx missing locations for `/api/admin/dashboard|projects`, `/api/admin/github/status|repositories|map`, `/api/admin/agent/qa` (current `/api/admin/qa` rule 404s); (2) `main.py` lifespan never wired + deprecated `on_event` double `init_db` (scheduler never starts via app); (3) dashboard returns raw `ObjectId` docs (500 risk — needs `oid_str`); (4) resume `path` vs `stored_path` field mismatch breaks public download; (5) admin CMS parity (profile/portfolio/products/content/resumes/github-repos) exists only on .NET — **CLOSED by the .NET removal: ported to FastAPI `legacy.py` (Site API v1)**; (6) test suite covers only health/validators/quality — auth/CRUD/chat/agent mocked tests per QA checklist §11 still open; (7) `.env.example` missing ~9 keys present in `config.py`.

**Update 2026-09-03 (gap-fix pass):** gaps 1–4 and 7 fixed and verified (`pytest -q`: 7 passed, 1 skipped; `tsc --noEmit`: clean; `run_qa.py`: PASS, 2 placeholder-only secret hits). Gap 5 resolved as documented decision (.NET authoritative, nginx note added). Gap 6 partially closed (auth-gate + lifespan + log-truncation tests added; mocked CRUD/chat/agent tests remain open). **Update (.NET removal):** `backend/` deleted; gap-5 ports landed in FastAPI (`legacy.py` Site API v1 — 47 routes incl. public projects/activity/profile/contact/subscribe/learning + legacy admin auth — plus seeds + indexes); single-backend Docker (ai-api :8090) and nginx; `services/auth.ts` FastAPI-only; vite proxy → `:8000`. `scripts/migrate_sqlite_to_mongo.py` migrates all 14 tables (verified live: 4 projects, 6 activities, 1 profile, 5 courses + seeds); `pytest -q`: 11 passed, 2 skipped. **New requirement added:** admin System Logs section — every backend failure recorded to `error_logs` with automatic 5-day TTL retention (`LOG_RETENTION_DAYS`), served by `GET /api/admin/logs|/stats` + `DELETE` purge, visible at `/admin/logs` (filter, details, stats, purge). See `CHANGELOG.md` for the full fix list.

**Requirement traceability:** P1 Audit done; P2 DB done (Mongo, seeded home/skills/experience/5 verified projects, `github_url=NULL` unless verified; Site-API collections `legacy_projects/activities/profiles/products/website_contents/resumes` + Page Flow/DocuFlow/profile/resume seeds; 14-table migration script verified live); P3 Auth done (dual-email JWT + rate limit; frontend FastAPI-only); P4 Resume done on FastAPI (upload/version/publish/download/extract/decision, legacy paths); P5-P6 Portfolio/Products done on FastAPI (legacy admin + public paths, camelCase parity); P7-10 GitHub/AI agents done (sync + daily agent + quality gate, `locked_fields`/`is_manually_edited` preserved, `AI_AUTO_PUBLISH=false` default; legacy repos/sync-log/PATCH paths ported); P11 Public CMS done (published-only filters, `locked_fields` stripped; legacy `/api/portfolio|products|content` ported); P14 Security/tests partial (see gaps 6-7); P15 Deploy done (single-backend Docker + nginx, secrets gitignored; CI is frontend-only FTP).
