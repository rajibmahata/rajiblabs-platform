# RajibLabs Configuration Reference

Single source of truth for **every environment variable** used by the platform.
Backend reads `.env` via `rajiblabs-ai-backend/app/config.py` (Pydantic Settings).
Frontend reads `VITE_*` at build time via `import.meta.env`.

> 🔒 **Secrets rule:** `OPENAI_API_KEY`, `GITHUB_TOKEN`, `SECRET_KEY`, `JWT_SECRET`,
> `ADMIN_INITIAL_PASSWORD`, `SMTP_PASSWORD` exist **only server-side** — never in
> frontend code, logs, API responses, or Git commits. In production, set them as
> environment variables in your hosting provider (SmarterASP / VPS / Docker),
> not in a committed file. `.env` is git-ignored; `.env.example` and
> `.env.production` in this repo contain **placeholders only**.

---

## 1. App core

| Variable | Required | Dev (`.env.example`) | Prod (`.env.production`) | Where to get it / notes |
|---|---|---|---|---|
| `APP_ENV` | Yes | `development` | `production` | `production` enforces real `SECRET_KEY` + `JWT_SECRET` (app refuses to boot with `change-me` values) |
| `APP_URL` | Yes | `https://rajiblabs.com` | `https://rajiblabs.com` | Canonical public URL; used in links/sitemap |
| `BASE_URL` | No | `http://localhost:8000` | `https://rajiblabs.com` | Backend's own public base (health/docs links) |
| `CORS_ORIGINS` | Yes | `http://localhost:5173,https://rajiblabs.com` | `https://rajiblabs.com` | Comma-separated. No `*` with credentials. Add preview URLs if needed |
| `APP_TIMEZONE` | No | `Asia/Kolkata` | `Asia/Kolkata` | Daily-agent cron timezone |
| `SECRET_KEY` | **Prod yes** | _(empty)_ | `openssl rand -hex 32` | App signing. Generate: `openssl rand -hex 32` (32+ chars) |
| `VITE_API_BASE` (frontend) | No | _(empty = same origin)_ | _(empty = same origin)_ | Build-time only. Set only if API lives on another host, e.g. `https://api.rajiblabs.com` |

## 2. Database (MongoDB)

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `DATABASE_URL` | Yes | `mongodb://localhost:27017/rajiblabs` | `mongodb://mongo:27017/rajiblabs` (Docker) or Atlas URI `mongodb+srv://<user>:<pass>@<cluster>/rajiblabs` | Docker Compose overrides this to the `mongo` service automatically |
| `MONGO_DB_NAME` | No | `rajiblabs` | `rajiblabs` | Database name inside the cluster |

## 3. Admin auth (dual-email, one identity)

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `ADMIN_EMAILS` | Yes | `rajibmahata143@gmail.com,rajibmahata143@outlook.com` | same | Both log in as the **same** admin (case-insensitive). Seeded once; never overwritten |
| `ADMIN_INITIAL_PASSWORD` | **First run** | _(empty)_ | `<strong secret>` | Used **once** to create the admin, then BCrypt-hashed in DB. Generate: `openssl rand -base64 24`. Can be left empty afterwards |
| `JWT_SECRET` | **Prod yes** | _(empty)_ | `openssl rand -hex 32` | Signs access/refresh tokens. **Must differ from `SECRET_KEY`** |
| `JWT_EXPIRE_MINUTES` | No | `15` | `15` | Access-token lifetime (cookie `rlabs_access`) |
| `REFRESH_EXPIRE_DAYS` | No | `7` | `7` | Refresh-token lifetime (cookie `rlabs_refresh`) |
| `JWT_ISSUER` | No | `rajiblabs` | `rajiblabs` | Must match on every instance behind a load balancer |
| `API_KEY` | No | _(empty)_ | _(empty)_ | Optional `X-Api-Key` guard for agent write endpoints. Empty = unchecked (legacy behavior) |

## 4. OpenAI (server-only, cheapest-model setup)

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `OPENAI_API_KEY` | For AI features | _(empty)_ | `sk-proj-...` | From https://platform.openai.com/api-keys. App runs with heuristics when empty |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | `gpt-4o-mini` | Primary model — operator's choice, low-cost (see §7) |
| `OPENAI_FALLBACK_MODEL` | No | `gpt-5.6-luna` | `gpt-5.6-luna` | Higher-quality fallback for manual high-value regeneration |
| `OPENAI_ENABLED` | No | `true` | `true` | Master kill-switch. `false` = heuristics everywhere, zero spend |
| `OPENAI_MAX_RETRIES` | No | `3` | `3` | Exponential backoff; no infinite loops |
| `AI_AUTO_PUBLISH` | No | `false` | `false` | Keep `false` — AI drafts require admin approval |
| `AI_QUALITY_THRESHOLD` | No | `85` | `85` | 0–100 gate; below threshold → `review required`, never published |

## 5. GitHub sync (server-only)

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `GITHUB_OWNER` | Yes | `rajibmahata` | `rajibmahata` | Account/org to sync from |
| `GITHUB_TOKEN` | For sync | _(empty)_ | `ghp_...` / fine-grained PAT | Needs **read-only** repo metadata. Create: GitHub → Settings → Developer settings → PAT (classic `public_repo` scope, or fine-grained read-only). Least privilege — no write scopes |
| `GITHUB_SYNC_ENABLED` | No | `true` | `true` | Kill-switch for all sync activity |

## 6. Agent, chat, QA

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `DAILY_AGENT_ENABLED` | No | `true` | `true` | Daily GitHub scan → AI drafts → notifications |
| `DAILY_AGENT_HOUR` / `DAILY_AGENT_MINUTE` | No | `2` / `0` | `2` / `0` | Cron in `APP_TIMEZONE`. Manual run anytime: `POST /api/admin/agent/run` |
| `CHAT_ENABLED` | No | `true` | `true` | Public "Talk to RajibLabs" widget. `false` shows contact fallback |
| `LOG_RETENTION_DAYS` | No | `5` | `5` | Admin-visible `error_logs` auto-expire via MongoDB TTL index |

## 7. Uploads & resume

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `UPLOAD_DIR` | No | `./data/uploads` | `./data/uploads` (mounted volume in Docker) | PDF/DOCX/PNG/JPG/WEBP only; safe filenames; 10 MB resume / 5 MB image caps |
| `MAX_IMAGE_MB` | No | `5` | `5` | Project screenshot cap |
| `MAX_RESUME_MB` | No | `10` | `10` | Resume cap |
| `RESUME_PATH` | No | _(empty)_ | _(empty)_ | Optional override for the seed resume; default `data/Rajib-Mahata-Resume-2026.pdf` |

## 8. Contact (centralized — mirrors `frontend/src/config/site.ts`)

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `CONTACT_EMAIL` | Yes | `rajibmahata143@gmail.com` | same | Public contact + lead notifications |
| `CONTACT_EMAIL_SECONDARY` | No | `rajibmahata143@outlook.com` | same | Secondary |
| `PRIMARY_PHONE` | Yes | `+918420249020` | same | Call button (`tel:+918420249020`) |
| `SECONDARY_PHONE` | No | `+919100184730` | same | Backup display only |
| `WHATSAPP_PHONE` | Yes | `+918420249020` | same | `https://wa.me/918420249020` |

## 9. SMTP (optional — lead email notifications)

| Variable | Required | Dev | Prod | Notes |
|---|---|---|---|---|
| `SMTP_HOST` / `SMTP_PORT` | For email | _(empty)_ / `587` | e.g. `smtp.gmail.com` / `587` | Empty host = email notifications disabled; admin dashboard notifications always work |
| `SMTP_USER` / `SMTP_PASSWORD` | For email | _(empty)_ | App password (Gmail: 16-char app password, not login password) | |
| `SMTP_FROM` | For email | _(empty)_ | `RajibLabs <rajibmahata143@gmail.com>` | |

---

## 10. Cheapest OpenAI model for this site (verified Sept 2026 pricing)

Per current OpenAI Platform pricing, ranked by cost:

| Model | Input / 1M | Output / 1M | Verdict |
|---|---|---|---|
| `gpt-5-nano` | $0.05 | $0.40 | Absolute cheapest; switch here for minimum spend |
| `gpt-4.1-nano` | $0.10 | $0.40 | Runner-up; 1M context if needed |
| **`gpt-4o-mini`** ✅ primary | **$0.15** | **$0.60** | Operator's choice. Proven, widely supported, cheap enough |
| **`gpt-5.6-luna`** ✅ fallback | **$0.20** | **$1.20** | Current-gen cheap lane, better quality for manual high-value regen |
| `gpt-5-mini` and up | $0.25+ | $2.00+ | Not needed for this site's workloads |

The repo defaults (`OPENAI_MODEL=gpt-4o-mini`, `OPENAI_FALLBACK_MODEL=gpt-5.6-luna`) match the operator's choice. To cut spend further, set `OPENAI_MODEL=gpt-5-nano` ($0.05/$0.40) — no code change needed, it's env-only.

**What it costs on rajiblabs.com with `gpt-4o-mini`** (app caps: chat 250 output tokens, AI jobs 700):
- Chat reply (~1K in + 250 out): ≈ **$0.0003 → ~3,300 chats per $1**
- AI content job (~3K in + 700 out): ≈ **$0.00087 → ~1,150 jobs per $1**

Further savings already built in: hash dedup (unchanged content never re-runs), compact prompts (README ≤2000 chars), one summary per day (not per commit), `AI_AUTO_PUBLISH=false` (no runaway loops). A $5 credit covers thousands of interactions.

---

## 11. Production go-live checklist

1. Copy `rajiblabs-ai-backend/.env.production` → `.env` on the server (or paste values into hosting env vars). Fill **all secrets**.
2. `APP_ENV=production` (boot fails fast if `SECRET_KEY`/`JWT_SECRET` are placeholders).
3. `CORS_ORIGINS=https://rajiblabs.com` (no localhost in prod).
4. `DATABASE_URL` → production Mongo (Atlas `mongodb+srv://...` or Docker `mongo` service).
5. First boot creates the admin from `ADMIN_EMAILS` + `ADMIN_INITIAL_PASSWORD`. Log in at `/admin/login`, then you may clear the password var.
6. Verify `/health` → `{"status":"ok","database":"ok",...}`.
7. Set `GITHUB_TOKEN` (read-only PAT) → run Sync GitHub Now → review queue before publishing.
8. Set `OPENAI_API_KEY` → AI enrichment + chat go live (or leave empty for zero-spend heuristic mode).
9. `docker compose up -d` (or VPS equivalent). Frontend on SmarterASP needs no env changes (`VITE_API_BASE` empty = same origin).
