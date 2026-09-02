# RajibLabs — Implementation Plan (Portfolio CMS + GitHub AI Sync)

**Repo:** rajibmahata/rajiblabs-platform | **Prod:** https://rajiblabs.com | **Stack:** React 19 + Vite 8 + Tailwind 4 (PWA) + .NET 8 Minimal API + SQLite + EF Core | **Deploy:** GitHub Actions → FTP `win1069.site4now.net` (`frontend/dist` → `/`), backend `rajiblabs.db` via `EnsureCreated`.

## 1. Architecture Audit — Findings

**Frontend:** `frontend/src/App.tsx` renders `pages/Home.tsx` (no router) → sections: `Hero, Results, Profile, HowIWork, AppsShowcase, Products, CompletedProjects, WIP, GitHubActivity, Contact` + `layout/GlobalNav, GlobalFooter, MobileBottomBar` + `ui/FloatingContact`. Centralized `config/site.ts` (phone/wa/email/linkedin). PWA: `manifest.webmanifest, sw.js, offline.html`, `pwa/registerSW`. No auth. Types in `types/index.ts` (Project, Profile, Activity). `index.css` Midnight Engineering Design System (already premium, must preserve).

**Backend:** `Program.cs` — SQLite `UseSqlite("Data Source=rajiblabs.db")`, EF `LabDbContext` with `Projects, Activities, Profiles, Contacts, LinkedInCourses, Subscribers`, `EnsureCreated` + `SeedData` (4 projects, profile). APIs: `GET /api/projects, /api/projects/{id}, /api/activity, /api/profile, /api/learning, /api/health, POST /api/contact, /api/subscribe, /api/learning`. Writes protected by `X-Api-Key` filter (`appsettings.json:ApiKey`). No Identity/JWT, no auth, CORS `localhost:5173, rajiblabs.com`. Static files via `UseStaticFiles` (PWA).

**Content:** Professional info hard-coded in `SeedData` + `site.ts`; products/projects seeded; Page Flow not isolated — treated as product/project (spec §14). No CMS, no admin.

**Governance:** `.github/workflows/ci.yml` builds `frontend/dist` (verified PWA artifacts) + `dotnet publish`, then `deploy.sh` FTP to verified root `/` (auto-detect avoids `/rajiblabs/rajiblabs`). Needs to preserve `admin`, `api`, `.well-known` on deploy.

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

All JSON arrays as `Json` text columns, `HasIndex` on `Slug`, `Email`. `EnsureCreated` will recreate on new DB; for prod, use `dotnet ef migrations` later.

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

Auth protects admin APIs, resume CRUD, portfolio/product CRUD, Page Flow visible, GitHub sync + AI + review, public CMS data, mobile 320-1920 no scroll, PWA install, phone/WA/email from `site.ts`/profile, SEO titles, no secret leak, `npm run build` + `dotnet build` pass.
