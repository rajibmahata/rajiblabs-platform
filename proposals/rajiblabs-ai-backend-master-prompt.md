# RajibLabs AI Platform — Master Architecture & Implementation Prompt

> **Purpose:** This single document contains (A) the complete architecture specification and (B) a self-contained master prompt. Paste **Section 12** into any capable AI coding agent (OpenAI) and it has everything needed to build the entire application without further context.

---

## 1. Executive Summary & Product Concept

RajibLabs is the personal portfolio and product studio site of **Rajib Mahata** (Senior .NET & Azure Solutions Architect, Kolkata, India — https://rajiblabs.com). The goal of this project is to make the platform **fully AI-automated**:

- **Rajib logs into one admin panel** and manages everything: homepage content, skills, experience, portfolio projects, demo videos, live URLs, resume, GitHub repos, and the AI agents themselves.
- **GitHub is the source of truth for code activity.** An agentic system pulls repos via a stored Personal Access Token, and a **daily-commit validator agent** checks recent commits and updates the site automatically.
- **A background AI content agent** writes and polishes project descriptions so every project page always reads professionally. Manual edits are never silently overwritten — AI proposes, admin approves.
- **A customer-facing AI chat widget** answers visitor questions from site content (RAG-lite), guides visitors to share **name, email, phone, and a description of their need**, and stores each lead in SQLite with an admin notification on login.
- **Cost is a hard constraint:** use only a low-cost OpenAI model (`gpt-4o-mini` by default) for all content management and chat, with aggressive caching and token budgets.

### Confirmed decisions
| Decision | Choice |
|---|---|
| Stack | Python 3.12 + FastAPI + SQLite (SQLModel/SQLAlchemy) + Jinja2 admin panel |
| Scope | **Replaces** the existing .NET backend (`backend/RajibLabs.Api`) as the site API |
| Chat | AI conversation grounded on site/portfolio content + structured lead capture |
| Admin | Built-in server-rendered web admin panel, single admin user (Rajib), JWT auth |
| AI model | OpenAI low-cost mini model only |

---

## 2. System Architecture

### 2.1 Component diagram

```
                        ┌────────────────────────────────────────────────┐
                        │              FastAPI Application               │
                        │                                                │
  Public site ─────────►│  /api/*        Public JSON API (read-only)     │
  (React PWA at         │  /chat/*       Chat widget API (widget + AI)   │
   rajiblabs.com)       │  /admin/*      Admin web panel (Jinja2+JWT)    │
                        │  /uploads/*    Static media (screenshots,      │
                        │                resume — path-traversal safe)   │
                        └───────┬───────────────┬───────────────┬────────┘
                                │               │               │
                        ┌───────▼──────┐ ┌──────▼───────┐ ┌─────▼─────────┐
                        │   SQLite     │ │ Background   │ │  Scheduler    │
                        │ rajiblabs.db │ │ Agent Workers│ │ (APScheduler) │
                        └──────────────┘ └──────┬───────┘ └───────────────┘
                                                 │
                          ┌──────────────────────┼──────────────────────┐
                          │                      │                      │
                  ┌───────▼────────┐   ┌─────────▼────────┐   ┌────────▼───────┐
                  │ GitHub Sync    │   │ Commit Validator │   │ Content Writer │
                  │ Agent          │   │ Agent (daily)    │   │ Agent          │
                  │ (repos+README) │   │ validates daily  │   │ drafts/polishes│
                  └───────┬────────┘   │ commits, updates │   │ descriptions   │
                          │            │ site content     │   └───────┬────────┘
                          │            └──────────────────┘           │
                  ┌───────▼────────────────────────────────────────── ▼──────┐
                  │                OpenAI API (gpt-4o-mini)                 │
                  │   - repo classification & summarization                 │
                  │   - description drafting/polishing                      │
                  │   - chat widget conversation + lead extraction          │
                  └────────────────────────────────────────────────────────┘
```

### 2.2 Data flows

1. **Repo ingestion:** Scheduler fires GitHub Sync (default every 6h) → lists repos for configured owner via PAT → upserts `github_repos` (metadata + README) → Commit Validator Agent checks commits since last run → new/changed repos queued for AI enrichment → Content Writer Agent drafts title/summary/description → records go to `status=review` → admin approves in panel → published to portfolio.
2. **Manual-first governance:** any field the admin edits gets `is_manual_edit=true`; agents may *propose* changes (stored as proposals) but never overwrite manual edits without explicit admin approval. Admin is the authority; GitHub is metadata source; AI is enrichment.
3. **Lead capture:** visitor opens chat widget → `/chat/session` creates anonymous session → messages exchanged, AI answers from a context bundle built from profile/skills/portfolio tables → AI extracts lead fields when visitor shares them (or widget shows a compact form fallback) → `leads` row + `notifications` row created → admin sees unread badge on next login.
4. **Content publishing:** homepage sections, skills, experience all live in tables; public API serves only `status=published` rows. The React frontend consumes the same endpoint shapes it uses today (Section 4).

---

## 3. Complete Data Model (SQLite)

All timestamps ISO-8601 UTC strings. JSON array fields stored as TEXT containing JSON.

### 3.1 Identity & ops
- **admin_users** `{id, username unique, password_hash (bcrypt), created_at, last_login_at}`
- **notifications** `{id, type (lead|agent|system|error), title, body, link, is_read bool, created_at}` — index `(is_read, created_at)`
- **settings** `{key unique, value_json, updated_at}` — stores GitHub owner, default repo token ref, agent toggles, schedules, model name, token budget state
- **agent_runs** `{id, agent_name (github_sync|commit_validator|content_writer), status (running|success|failed), started_at, finished_at, summary, details_json, error}`
- **sync_logs** `{id, started_at, finished_at, repos_found, added, updated, ignored, errors_json}`

### 3.2 Site content
- **profile** `{id, full_name, headline, role, location, phone, whatsapp, email, linkedin_url, github_url, website, profile_image_path, about_json (array of paragraphs), updated_at}` — single row
- **home_content** `{id, section_key unique (hero|about|process|cta|metrics), title, subtitle, body_json, display_order, status, updated_at}`
- **skills** `{id, category, name, display_order, status}`
- **experience_items** `{id, company, role_title, date_range, description, display_order, status}`
- **resumes** `{id, file_name, stored_path, content_type, size_bytes, version, status (draft|published|archived), uploaded_at, published_at}` — one `published` at a time

### 3.3 Portfolio & GitHub
- **portfolio_projects** `{id, title, slug unique, short_description, description, problem, solution, role, architecture, tech_stack_json, ai_capabilities_json, demo_url, demo_video_url, live_url, github_url, screenshots_json, status (draft|review|published|hidden), is_featured bool, display_order, created_at, updated_at, published_at, last_synced_at, is_manual_edit bool, source_repo_id FK nullable}`
- **github_repos** `{id, github_id, name, full_name, html_url, description, primary_language, topics_json, stars, forks, default_branch, is_private, readme_text, license, last_pushed_at, last_commit_sha, last_commit_at, classification (production|ai_lab|product|tooling|ignore), sync_status (new|review|published|ignored), is_manually_edited bool, last_synced_at}`
- **ai_proposals** `{id, target_table, target_id, field, proposed_value, reason, confidence (0-1), status (pending|approved|rejected|expired), created_at, decided_at}` — how agents propose edits to manual/edited content

### 3.4 Chat & leads
- **chat_sessions** `{id, session_token unique, visitor_name, visitor_email, visitor_phone, started_at, last_message_at, ip_hash, is_converted bool}`
- **chat_messages** `{id, session_id FK, role (user|assistant|system|widget), content, created_at}`
- **leads** `{id, name, email index, phone, description, source (chat|form), chat_session_id FK nullable, status (new|contacted|closed), created_at}`
  - On insert → always create a `notifications` row (`type=lead`).

---

## 4. Public API Spec (frontend parity)

Must keep working with the existing React frontend. Same paths and response shapes as the current .NET API:

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | `{status:"ok"}` |
| GET | `/api/projects` | published portfolio projects (map to old `Project` shape) |
| GET | `/api/projects/{id}` | single project |
| GET | `/api/profile` | profile row |
| GET | `/api/activity` | recent GitHub activity (from repos/commits) |
| GET | `/api/learning` | courses/learning items |
| POST | `/api/contact` | `{name,email,phone,message}` → creates lead (source=form) + notification |
| POST | `/api/subscribe` | email capture |
| GET | `/api/skills` | new — published skills |
| GET | `/api/experience` | new — published experience |
| GET | `/api/home` | new — ordered home sections |
| GET | `/api/resume/download` | serves current published resume (auth optional; path-traversal guarded) |

### Chat widget API
| Method | Path | Body / Notes |
|---|---|---|
| POST | `/chat/session` | → `{session_token}` |
| POST | `/chat/message` | `{session_token, message}` → `{reply, lead: {name,email,phone,description} \| null, complete: bool}` — AI reply grounded on site content; extracts lead fields opportunistically |
| POST | `/chat/lead` | `{session_token, name, email, phone, description}` → final structured lead save (form fallback) |
| GET | `/chat/widget.js` | embeddable JS snippet that renders the floating chat bubble (configurable position/color via query params) |

Rate limit `/chat/*` to 20 req/min/IP.

---

## 5. Admin Panel & Admin API

### 5.1 Auth
- `POST /api/admin/login` `{username, password}` → JWT access (15 min) + refresh (7 days, HttpOnly `SameSite=Strict` cookie `rlabs_refresh`)
- `POST /api/admin/logout`, `GET /api/admin/me`
- All `/api/admin/*` and `/admin/*` pages behind `RequireAdmin` dependency; login rate-limited 5/min/IP; bcrypt password hashing; initial admin seeded from `.env` on first run.

### 5.2 Admin web panel (Jinja2 server-rendered, clean minimal dark/light UI)
Pages: **Dashboard** (leads count, unread notifications, agent status, recent sync), **Leads inbox** (list + detail + status change), **Homepage content** (edit hero/about/process/CTA/metrics), **Skills**, **Experience**, **Profile**, **Portfolio** (CRUD + publish/feature/reorder + screenshot upload + demo video/live/GitHub URLs), **GitHub repos** (list, classification, sync now, review queue), **AI proposals** (approve/reject), **Resume** (upload/version/publish), **Notifications** (bell + mark read), **Agents & Settings** (enable/disable, schedules, model, token usage, GitHub PAT management).

### 5.3 Admin API surface (all JWT-protected)
- CRUD: `/api/admin/{leads,home-content,skills,experience,profile,portfolio,resumes}`
- `/api/admin/notifications` GET / `PATCH .../{id}/read` / `POST .../read-all`
- `/api/admin/github/sync` POST — trigger sync now
- `/api/admin/agents/{name}/run` POST — trigger agent
- `/api/admin/agents` GET/PATCH — toggles + schedules
- `/api/admin/settings` GET/PATCH — GitHub owner, PAT (write-only, masked on read), model name
- `/api/admin/ai-proposals` GET / `POST .../{id}/approve|reject`

---

## 6. GitHub Integration & Agentic System

### 6.1 GitHub Sync Agent (`github_sync`)
- Uses `httpx` against `https://api.github.com` with PAT from settings (never from code). Paginate `/users/{owner}/repos?per_page=100` and `/repos/{full_name}/readme` (base64 decode).
- Upsert `github_repos` by `github_id`; never delete; new repos → `sync_status=new`.
- Records `sync_logs` + `agent_runs`.

### 6.2 Daily Commit Validator Agent (`commit_validator`) — runs once daily
- For each non-ignored repo: fetch `/repos/{full}/commits?since=last_run`.
- If new commits: refresh README + metadata; detect meaningful changes (new README sections, new topics, version tags); if the repo is published in the portfolio → queue AI refresh of its description; if classification `ignore` skipped.
- Writes a daily digest notification for the admin: "N commits across M repos — K portfolio updates proposed."

### 6.3 Content Writer Agent (`content_writer`)
- For each `sync_status=new` repo (or AI refresh queue): builds a compact context (README trimmed to ~3k tokens, languages, topics) and asks the mini model to produce: `title, short_description, description (problem → solution → outcome, 120–180 words), tech_stack[], classification, demo/live URL guesses from README links`.
- Stores AI fields as an **ai_proposal** if the project is manually edited; otherwise writes to a `review` status draft directly.
- **Polishing mode:** admin can trigger "improve this description" on any portfolio item — the agent rewrites it professionally without inventing facts not present in the source context. Confidence < 0.7 → always `review`.

### 6.4 Scheduling
- APScheduler (AsyncIOScheduler): `github_sync` every 6h, `commit_validator` daily 06:00 UTC, `content_writer` processes queue every 30 min. All toggles read from `settings`. All agent work is also manually triggerable from admin.

---

## 7. AI Chat Widget Spec

1. Floating bubble bottom-right; opens a chat card (matches site design tokens).
2. Every message → `/chat/message`; server builds a **context bundle** (profile summary, skills, top published projects, contact channels — assembled from DB, cached 10 min) and calls the mini model with a strict system prompt: *"You are the assistant for RajibLabs… answer only from the provided context… always work toward collecting the visitor's name, email, phone, and what they need. Ask for at most one missing field per reply."*
3. The model returns JSON: `{reply, extracted: {name?, email?, phone?, description?}}` (JSON mode / function calling). Extracted fields update `chat_sessions` incrementally.
4. When all four collected (or visitor ends chat), a lead is saved + notification created. Widget also offers a compact form fallback posting to `/chat/lead`.
5. Transcript stored in `chat_messages`; visible in admin lead detail.
6. Guardrails: no pricing/invention (defer to Rajib), refuse off-topic, 12-message per session soft cap, per-IP rate limit.

---

## 8. Non-Functional Requirements

- **Security:** PAT & OpenAI key only in `.env`/settings, masked everywhere in UI and logs; bcrypt; JWT expiry; CORS limited to `https://rajiblabs.com` + localhost dev; upload validation (images PNG/JPG/WebP ≤ 5 MB, resume PDF ≤ 10 MB; sanitized filenames; no path traversal); parameterized queries via SQLModel; XSS-escape in Jinja2 templates.
- **Cost control:** single model (`gpt-4o-mini` or configured equivalent); max_output_tokens caps per use case (repo enrich 700, polish 700, chat reply 300); context bundles trimmed; agent enrichment only on change (diff README hash); daily token budget counter in `settings` shown in admin, agents stop gracefully when exceeded.
- **Reliability:** all agent runs in try/except → `agent_runs.status=failed` + error notification; graceful degradation — if OpenAI key absent or budget hit, site stays fully functional, agents pause, chat falls back to form-only.
- **Observability:** structured logging (rich or loguru), `/api/health` checks DB + config presence.
- **Portability:** single SQLite file path configurable; WAL mode enabled.

---

## 9. Configuration

### `.env` template (keys added by owner; never committed)
```env
# App
APP_ENV=development
BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5173,https://rajiblabs.com

# Database
SQLITE_PATH=./data/rajiblabs.db

# Admin (seeded on first run only)
ADMIN_USERNAME=rajib
ADMIN_PASSWORD=change-me

# Auth
JWT_SECRET=generate-a-long-random-string
JWT_EXPIRE_MINUTES=15
REFRESH_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
DAILY_TOKEN_BUDGET=200000

# GitHub
GITHUB_OWNER=rajibmahata
GITHUB_TOKEN=            # optional default; can be managed in admin instead

# Uploads
UPLOAD_DIR=./data/uploads
MAX_IMAGE_MB=5
MAX_RESUME_MB=10
```

`app/config.py` loads via pydantic-settings, fails fast on missing critical vars in production, logs a warning (not fatal) in development when optional keys are absent.

---

## 10. Project Scaffold

```
rajiblabs-ai-backend/
├── app/
│   ├── main.py               # FastAPI app factory, routers, scheduler startup
│   ├── config.py             # pydantic-settings
│   ├── database.py           # SQLModel engine/session, init_db + seed
│   ├── models/               # one module per table group
│   │   ├── admin.py  content.py  portfolio.py  github.py  chat.py
│   ├── schemas/              # pydantic request/response DTOs
│   ├── auth/                 # jwt.py, dependencies.py (RequireAdmin), bcrypt
│   ├── routers/
│   │   ├── public.py  chat.py  admin_auth.py
│   │   ├── admin_content.py  admin_portfolio.py  admin_github.py
│   │   ├── admin_leads.py    admin_agents.py     admin_settings.py
│   ├── services/
│   │   ├── openai_client.py  github_client.py   context_builder.py
│   │   ├── lead_service.py   notification_service.py
│   ├── agents/
│   │   ├── base.py  github_sync.py  commit_validator.py  content_writer.py
│   ├── scheduler.py          # APScheduler wiring
│   └── templates/ + static/  # Jinja2 admin panel + widget.js
├── data/                     # rajiblabs.db + uploads (gitignored)
├── tests/                    # pytest: auth, CRUD, chat, agents (mocked OpenAI/GitHub)
├── .env.example
├── requirements.txt
└── README.md
```

**requirements.txt (indicative):** `fastapi uvicorn[standard] sqlmodel pydantic-settings python-jose[cryptography] passlib[bcrypt] httpx jinja2 python-multipart apscheduler pytest openai slowapi` (rate limiting).

**Run:** `pip install -r requirements.txt && uvicorn app.main:app --reload` — DB auto-created and seeded on startup.

---

## 11. QA Agent Validation Checklist

The implementing agent must run/verify all of the following (pytest where possible, plus manual script):

1. Fresh DB bootstraps, admin seeded, login returns JWT, protected routes reject anonymous & expired tokens, login rate limit works.
2. Public API parity: all endpoints in §4 return correct shapes; only `published` content served.
3. CRUD + publish/feature/reorder for portfolio, skills, experience, home content; screenshots upload with validation; resume versioning keeps exactly one published.
4. GitHub sync with a mocked PAT lists/upserts repos; new repo → `sync_status=new`; ignored repos skipped; sync log written.
5. Commit validator: with mocked commit fixtures, detects changes since watermark, queues refresh, writes digest notification.
6. Content writer: with mocked OpenAI responses, produces proposals; manual-edit fields are never overwritten; approve applies, reject discards; low-confidence forces `review`.
7. Chat: session created; AI reply uses context bundle (mocked model); lead fields extracted across turns; complete lead → row in `leads` + unread notification; admin sees it on login; form fallback works; rate limit enforced.
8. Notifications: badge counts only unread; mark-read works.
9. Security: PAT/keys never appear in any API response or template; path traversal on uploads rejected; CORS restricted.
10. Full test suite passes; README documents setup; `.env.example` matches §9.

---

## 12. THE MASTER PROMPT (copy everything below this line)

```
You are a senior full-stack engineer. Build a complete, production-ready backend
application called "RajibLabs AI Platform" — an AI-automated portfolio/CMS with
admin panel, GitHub agents, and an AI chat lead-capture widget.

STACK (mandatory): Python 3.12, FastAPI, SQLModel + SQLite (WAL mode), Jinja2
server-rendered admin panel, APScheduler for background jobs, httpx for GitHub,
the official `openai` SDK with ONLY a low-cost model (default "gpt-4o-mini",
configurable via env), bcrypt + JWT (python-jose) auth, pytest tests.

CONTEXT: The public site is a React PWA at https://rajiblabs.com. This app
REPLACES an existing .NET API, so the public JSON endpoints below must keep the
exact same paths and response shapes. Single admin user: "rajib".

=== 1. DATABASE (SQLite, auto-create + seed on startup) ===
Tables (SQLModel):
- admin_users{id, username unique, password_hash, created_at, last_login_at}
- notifications{id, type: lead|agent|system|error, title, body, link, is_read, created_at}
- settings{key unique, value_json, updated_at}
- agent_runs{id, agent_name, status: running|success|failed, started_at, finished_at, summary, details_json, error}
- sync_logs{id, started_at, finished_at, repos_found, added, updated, ignored, errors_json}
- profile{single row: full_name, headline, role, location, phone, whatsapp, email, linkedin_url, github_url, website, profile_image_path, about_json}
- home_content{section_key unique: hero|about|process|cta|metrics, title, subtitle, body_json, display_order, status}
- skills{id, category, name, display_order, status}
- experience_items{id, company, role_title, date_range, description, display_order, status}
- resumes{id, file_name, stored_path, content_type, size_bytes, version, status: draft|published|archived, uploaded_at, published_at}
- portfolio_projects{id, title, slug unique, short_description, description, problem, solution, role, architecture, tech_stack_json, ai_capabilities_json, demo_url, demo_video_url, live_url, github_url, screenshots_json, status: draft|review|published|hidden, is_featured, display_order, created_at, updated_at, published_at, last_synced_at, is_manual_edit, source_repo_id?}
- github_repos{id, github_id, name, full_name, html_url, description, primary_language, topics_json, stars, forks, default_branch, is_private, readme_text, license, last_pushed_at, last_commit_sha, last_commit_at, classification: production|ai_lab|product|tooling|ignore, sync_status: new|review|published|ignored, is_manually_edited, last_synced_at}
- ai_proposals{id, target_table, target_id, field, proposed_value, reason, confidence, status: pending|approved|rejected, created_at, decided_at}
- chat_sessions{id, session_token unique, visitor_name?, visitor_email?, visitor_phone?, started_at, last_message_at, ip_hash, is_converted}
- chat_messages{id, session_id FK, role: user|assistant|system|widget, content, created_at}
- leads{id, name, email, phone, description, source: chat|form, chat_session_id?, status: new|contacted|closed, created_at} — creating a lead ALWAYS also creates a notification(type="lead").
Seed on first run: admin user from env, profile for Rajib Mahata (Senior .NET & Azure Solutions Architect, Kolkata, India, phone +91 84202 49020, whatsapp wa.me/918420249020, email rajibmahata143@gmail.com, github github.com/rajibmahata), sample home sections/skills/experience.

=== 2. PUBLIC API (exact paths, published content only) ===
GET /api/health; GET /api/projects; GET /api/projects/{id}; GET /api/profile;
GET /api/activity; GET /api/learning; GET /api/skills; GET /api/experience;
GET /api/home; POST /api/contact {name,email,phone,message} -> lead(source=form)+notification;
POST /api/subscribe; GET /api/resume/download.

=== 3. CHAT WIDGET API ===
POST /chat/session -> {session_token}
POST /chat/message {session_token, message}:
  - Build a context bundle from DB (profile, skills, published projects, contact
    channels), cache 10 min.
  - Call OpenAI (JSON mode) with system prompt: "You are the assistant for
    RajibLabs. Answer ONLY from the provided context. Be concise and friendly.
    Your goal is to collect the visitor's name, email, phone number, and a short
    description of what they need. Ask for at most one missing field per reply.
    Never invent pricing, availability, or technical claims. If asked something
    off-topic, redirect politely."
  - Model returns {reply, extracted:{name?,email?,phone?,description?}} — merge
    extracted fields into chat_sessions; when all four are present, save a lead
    (source=chat) + notification, mark is_converted.
  - Respond {reply, lead:{...}|null, complete:bool}.
  - Cap 12 messages/session; rate limit 20 req/min/IP; if OPENAI key missing or
    daily budget exceeded, reply with a canned message + serve the form fallback.
POST /chat/lead {session_token, name, email, phone, description} -> form fallback save.
GET /chat/widget.js -> embeddable JS that renders a floating chat bubble +
panel, posting to the endpoints above (no build step, vanilla JS, configurable
via query params: position, color).

=== 4. ADMIN (JWT) ===
POST /api/admin/login (rate limit 5/min/IP) -> 15-min access token + 7-day
HttpOnly SameSite=Strict refresh cookie; POST /api/admin/logout; GET /api/admin/me.
Protect everything under /api/admin/* and /admin pages.
Admin web panel (Jinja2, clean modern UI, minimal CSS, mobile-friendly):
Dashboard (lead counts, unread notifications, agent run status, last sync),
Leads inbox (+ transcript view, status changes), Homepage content editor,
Skills, Experience, Profile, Portfolio manager (CRUD, publish/feature/reorder,
screenshot upload, demo video / live / GitHub URL fields), GitHub repos
(classification, sync now, review queue), AI proposals (approve/reject),
Resume manager (upload/version/publish, one published at a time),
Notifications (bell + mark read/read-all), Agents & Settings (toggles,
schedules, model name, GitHub owner + PAT — PAT write-only, masked on read,
token usage + daily budget display).
Admin API: full CRUD for the entities above plus:
POST /api/admin/github/sync; POST /api/admin/agents/{name}/run;
GET/PATCH /api/admin/agents; GET/PATCH /api/admin/settings;
GET /api/admin/ai-proposals + POST .../{id}/approve|reject;
GET /api/admin/notifications + PATCH .../{id}/read + POST .../read-all.
CRITICAL RULE: whenever an admin edits a field, set is_manual_edit=true on that
record. Agents must then only create ai_proposals for those fields — never
overwrite. Admin approval applies a proposal.

=== 5. AGENTS (APScheduler; every run recorded in agent_runs; failures create
an error notification; every agent is also manually triggerable from admin) ===
a) github_sync (every 6h): list repos for GITHUB_OWNER using PAT from settings
   (httpx, GitHub REST v3, paginate 100/page) + fetch READMEs (base64). Upsert
   github_repos by github_id, never delete; new repos -> sync_status=new.
b) commit_validator (daily 06:00 UTC): for each non-ignored repo fetch commits
   since the stored watermark; on new commits refresh README/metadata, queue AI
   refresh for published portfolio items, and write a digest notification:
   "N commits across M repos - K portfolio updates proposed."
c) content_writer (every 30 min, processes queue): for sync_status=new repos
   and queued refreshes, build a compact context (README trimmed to ~3k tokens,
   languages, topics, links found in README) and ask the model for:
   {title, short_description, description (problem -> solution -> outcome,
   120-180 words, factual, no invented metrics), tech_stack[], classification,
   confidence}. If the target is manually edited -> create ai_proposal
   (pending); else create/update a portfolio_project with status=review.
   confidence < 0.7 always forces status=review. Also expose an admin action
   "improve this description" that re-polishes any portfolio description using
   only facts present in the stored context.

=== 6. COST CONTROL (hard requirement) ===
Only the configured mini model. max_output_tokens: 700 for enrichment/polish,
300 for chat. Trim all contexts. Skip AI work when README hash unchanged.
Track daily token usage in settings; show in admin; agents stop gracefully when
the daily budget (default 200k tokens) is exceeded; chat degrades to the form
fallback. If OPENAI_API_KEY is missing the whole site still works — agents
pause, chat falls back.

=== 7. SECURITY ===
All secrets via .env (pydantic-settings, fail fast in production for missing
critical vars). bcrypt passwords. CORS only localhost:5173 + rajiblabs.com.
Uploads: images PNG/JPG/WebP <=5MB, resume PDF <=10MB, sanitized filenames,
path-traversal-proof serving from UPLOAD_DIR outside the app package.
Parameterized queries (SQLModel). Jinja2 autoescape on. PAT and API keys never
appear in any response, template, or log.

=== 8. PROJECT LAYOUT ===
app/{main.py, config.py, database.py, models/, schemas/, auth/, routers/,
services/{openai_client,github_client,context_builder,lead_service,
notification_service}, agents/{base,github_sync,commit_validator,
content_writer}, scheduler.py, templates/, static/}, data/ (gitignored),
tests/ (pytest: auth, CRUD, chat with mocked OpenAI, agents with mocked GitHub),
.env.example, requirements.txt, README.md.
requirements: fastapi uvicorn[standard] sqlmodel pydantic-settings
python-jose[cryptography] passlib[bcrypt] httpx jinja2 python-multipart
apscheduler pytest openai slowapi

=== 9. QA CHECKLIST (you MUST verify all before finishing) ===
1) Fresh DB bootstraps + seeds; login issues JWT; anonymous/expired rejected;
   login rate-limited. 2) All public endpoints return correct shapes; only
   published content served. 3) CRUD + publish/feature/reorder for portfolio/
   skills/experience/home; upload validation; exactly one published resume.
   4) Mocked GitHub sync upserts repos; new -> status new; logs written.
   5) Commit validator detects new commits via watermark, queues refresh,
   writes digest. 6) Content writer (mocked model) creates proposals; manual
   edits never overwritten; approve/reject work. 7) Chat (mocked model):
   session, context-grounded reply, incremental lead extraction, lead +
   notification on completion, form fallback, rate limit. 8) Notification badge
   counts unread only. 9) No secret leaks in responses/templates; traversal
   rejected; CORS correct. 10) Full pytest suite green; README covers setup
   from .env.example; uvicorn app.main:app starts clean on empty data dir.

Deliver complete, runnable code with no TODO placeholders. Where a design choice
is unspecified, choose the simplest option consistent with this spec and note it
in the README.
```
