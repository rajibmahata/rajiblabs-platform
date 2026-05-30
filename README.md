# Rajib Labs Platform

> AI-powered portfolio & software lab. Built with React + .NET 8. Managed by OpenClaw agents.

## Architecture

```
rajiblabs-platform/
├── frontend/          # React + TypeScript + Tailwind CSS (Vite)
│   └── src/
│       ├── components/
│       │   ├── layout/       # Header, Footer, Layout
│       │   ├── hero/         # Hero section
│       │   ├── projects/     # ProjectGrid, ProjectCard
│       │   ├── activity/     # ActivityFeed
│       │   └── common/       # Shared components
│       ├── pages/            # Home, Projects
│       ├── services/         # API client
│       └── types/            # TypeScript interfaces
├── backend/           # .NET 8 Minimal API
│   └── RajibLabs.Api/
│       ├── Models/           # Project, Activity, Profile
│       ├── Data/             # EF Core DbContext (future)
│       └── Services/         # GitHub integration (future)
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

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{id}` | Single project |
| POST | `/api/projects` | Create project (agent) |
| GET | `/api/activity` | Activity feed |
| GET | `/api/profile` | Professional profile |
| GET | `/api/health` | Health check |

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
