# Rajib Labs Platform

> AI-powered portfolio & software lab. Built with React + .NET 8. Managed by OpenClaw agents.

## Architecture

```
rajiblabs-platform/
├── frontend/          # React + TypeScript + Tailwind CSS (Vite)
│   └── src/
│       ├── components/
│       │   ├── layout/       # GlobalNav, GlobalFooter, Layout
│       │   ├── activity/     # ActivityFeed
│       │   ├── projects/     # ProjectGrid, ProjectCard
│       │   ├── sections/     # HeroSection, ProfileSection, ProductsSection,
│       │   │                   GitHubActivitySection, ContactSection, etc.
│       │   └── ui/           # Button, StatusBadge, TechChip, CommitRow, etc.
│       ├── pages/            # Home, Projects
│       ├── services/         # api.ts, fallbackData.ts
│       └── types/            # TypeScript interfaces
├── backend/           # .NET 8 Minimal API + SQLite
│   └── RajibLabs.Api/
│       ├── Models/           # Project, Activity, Profile, DTOs
│       ├── Data/             # EF Core DbContext
│       └── Program.cs        # Minimal API endpoints
└── ARCHITECTURE.md     # Full architecture doc (in rajiblabs/)
```

## Quick Start

### Backend
```bash
cd backend/RajibLabs.Api
dotnet run
# Runs on http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/projects` | — | List all projects |
| GET | `/api/projects/{id}` | — | Single project by ID |
| PATCH | `/api/projects/{id}` | API Key | Update project (agent) |
| GET | `/api/activity?limit=` | — | Activity feed (optional limit) |
| POST | `/api/activity` | API Key | Log new activity (agent) |
| GET | `/api/profile` | — | Professional profile |
| GET | `/api/health` | — | Health check |

### Authentication

Write endpoints (`POST`, `PATCH`) require an API key passed via the `X-Api-Key` header. Configure in `appsettings.json`:

```json
{
  "ApiKey": "rajiblabs-agent-key-change-me"
}
```

Read endpoints (`GET`) are public and require no authentication.

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
