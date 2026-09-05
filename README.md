# Rajib Labs Platform

> AI-powered portfolio & software lab. Built with React + FastAPI + MongoDB.

## Architecture

```
rajiblabs-platform/
├── frontend/                # React + TypeScript + Tailwind CSS (Vite)
│   └── src/
│       ├── components/
│       │   ├── layout/       # GlobalNav, GlobalFooter, Layout
│       │   ├── activity/     # ActivityFeed
│       │   ├── projects/     # ProjectGrid, ProjectCard
│       │   ├── sections/     # HeroSection, ProfileSection, ProductsSection,
│       │   │                   GitHubActivitySection, ContactSection, etc.
│       │   └── ui/           # Button, StatusBadge, TechChip, CommitRow, etc.
│       ├── pages/            # Home, Projects, admin/*
│       ├── services/         # api.ts, fallbackData.ts
│       └── types/            # TypeScript interfaces
├── rajiblabs-ai-backend/    # FastAPI + MongoDB (the API)
│   ├── app/routers/         # public, admin_auth, admin_projects, github,
│   │                          ai, agent, chat, resume, legacy, health
│   │                          (legacy = Site API v1, same paths/shapes
│   │                           as the retired .NET backend)
│   ├── app/services/        # github_service, openai_service, quality, notify
│   └── scripts/             # create_admin.py, migrate_sqlite_to_mongo.py
└── ARCHITECTURE.md     # Full architecture doc (in rajiblabs/)
```

## Quick Start

### Full stack (recommended)
```cmd
run-docker.bat
:: Frontend http://localhost:5010, API http://localhost:8090, Mongo :27017
```

### API only
```bash
cd rajiblabs-ai-backend
cp .env.example .env   # fill ADMIN_INITIAL_PASSWORD + secrets
docker compose up -d   # mongo + api (api on :8000 natively, :8090 via root compose)
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173 (/api proxied to FastAPI, see vite.config.ts)
```

## API Endpoints (FastAPI + MongoDB)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | — | Health check (db/github/openai status) |
| GET | `/api/public/projects` | — | Published projects |
| GET | `/api/public/projects/{slug}` | — | Single project |
| POST | `/api/public/chat` | rate-limit | AI chat widget |
| POST | `/api/public/leads` | rate-limit | Lead / quote capture |
| GET | `/api/projects` | — | Projects (site format) |
| GET | `/api/activity?limit=` | — | Activity feed |
| GET | `/api/profile` | — | Professional profile |
| POST | `/api/contact` | — | Contact form → lead + notification |
| POST | `/api/subscribe` | — | Newsletter subscribe |
| GET | `/api/learning` | — | Learning/courses |
| GET | `/api/portfolio` | — | Published portfolio |
| GET | `/api/products` | — | Published products |
| POST | `/api/admin/auth/login` | rate-limit | Dual-email admin login (JWT cookies) |

### API Docs (Swagger)

- FastAPI (Mongo CMS/AI/admin): `/docs` (Swagger UI), `/redoc`, `/openapi.json` — non-production only. JWT via Authorize button (`POST /api/admin/auth/login`).

### Authentication

Admin endpoints require the dual-email admin login (`ADMIN_EMAILS` + `ADMIN_INITIAL_PASSWORD` from env, `ADMIN_INITIAL_PASSWORD` never committed). Login issues HttpOnly Secure SameSite cookies (`rlabs_access` 15m, `rlabs_refresh` 7d); login is rate-limited (5/min/IP). Public `GET /api/public/*` endpoints require no authentication; chat/lead POSTs are rate-limited.

Read endpoints (`GET /api/public/*`) are public and require no authentication.

## Deployment

Frontend `dist/` deploys via FTP (`deploy.sh`, SmarterASP). The API runs on the
VPS (169.58.165.10, shared with PestFlow — our edge is host `:8080`, PestFlow keeps
`:80/:443`; see POCs in `CHANGELOG.md`) via `docker-compose.production.yml`
(private network, Mongo + Qdrant internal, state in `/opt/rajiblabs`):
- One-command deploy on the VPS: `sh deploy/deploy-vps.sh`; setup + secrets in the
  compose header and `deploy/dotenv.production.example`.
- Auto-deploy from GitHub: `.github/workflows/deploy-vps.yml` runs on every merge to
  `main` (manual dispatch also available). Repo secrets: `VPS_HOST`, `VPS_USER`,
  `VPS_SSH_KEY` (SSH), plus `OPENAI_API_KEY`, `GITHUB_TOKEN`,
  `ADMIN_INITIAL_PASSWORD`, `SECRET_KEY`, `JWT_SECRET` — non-empty values sync into
  `/opt/rajiblabs/config/.env` each deploy (server file stays fallback).

Run from the repo root:

```bash
./deploy.sh
./deploy.sh --build
```

What it does:
- reads FTP credentials from your local environment or `.env`
- uploads the frontend `dist/` files to the SmarterASP FTP host
- keeps OpenClaw configuration untouched

Required local env vars:
- `FTP_HOST`
- `FTP_USER`
- `FTP_PASS`
- `FTP_PATH`
- `SITE_URL` (optional, used for verification)

## AI Workforce (OpenClaw Agents)

- **📊 Portfolio Agent** — Manages portfolio content
- **👀 Monitor Agent** — Tracks GitHub commits, updates activity feed
- **👷 Dev Agent** — Builds new projects
- **🧪 QA Agent** — Tests and validates
- **🚀 Delivery Agent** — Handles deployment
- **📋 HR Agent** — Receives and routes new project requests

## Owner

Rajib Mahata — Independent Software Architect
- GitHub: [rajibmahata](https://github.com/rajibmahata)
- Domain: [rajiblabs.com](https://rajiblabs.com)
