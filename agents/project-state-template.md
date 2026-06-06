# 📁 Project State — Memory File
> This file is the **shared memory** for the RajibLabs AI Workforce.  
> Every agent reads this file before starting work and writes its outputs back to this file when done.  
> The Orchestrator uses this file to know what has been completed and what to trigger next.

---

## 🏷️ Project Identity

```yaml
project_name: ""
project_slug: ""           # kebab-case, e.g. invoicer-pro
created_date: ""           # YYYY-MM-DD
last_updated: ""           # YYYY-MM-DD HH:MM IST
status: "Discovery"        # Discovery | Phase1 | Phase2 | Phase3 | Production | Complete
github_repo: ""            # e.g. rajibmahata/invoicer-pro
live_url: ""
staging_url: ""
```

---

## 📋 Project Brief (by rajiblabs-po)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked

**One-line description:**  
_[fill in]_

**Problem being solved:**  
_[fill in]_

**Target users:**  
_[fill in]_

**Success metrics:**  
_[fill in]_

### In-Scope Features

| # | Feature | Priority | Acceptance Criteria Written |
|---|---------|----------|-----------------------------|
| 1 | | Must Have | ⬜ |
| 2 | | Must Have | ⬜ |
| 3 | | Should Have | ⬜ |

### Out-of-Scope
- _[list items explicitly ruled out]_

### Constraints
- _[time / tech / compliance constraints]_

---

## 🧠 Technical Architecture Document (by rajiblabs-architect)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked  
**Depends on:** Project Brief ✅

**Stack confirmed:**
```yaml
frontend: ""          # e.g. React 18 + TypeScript + Vite + Tailwind
backend: ""           # e.g. .NET 8 ASP.NET Core Minimal API
database: ""          # e.g. Azure SQL Database
auth: ""              # e.g. JWT Bearer
hosting_frontend: ""  # e.g. Azure Static Web Apps
hosting_backend: ""   # e.g. Azure App Service
secrets: ""           # e.g. Azure Key Vault
monitoring: ""        # e.g. Azure Application Insights
```

**Data models defined:**
| Entity | Fields | Status |
|--------|--------|--------|
| | | ⬜ |

**API endpoints defined:**
| Method | Path | Auth | Status |
|--------|------|------|--------|
| | | | ⬜ |

**Security requirements:**
- _[list]_

**Open TAD questions:**
- _[any unresolved questions → route to rajiblabs-po]_

---

## 🎨 UX Brief & Design Handoff (by rajiblabs-ux)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked  
**Depends on:** Project Brief ✅

**Screens defined:**
| Screen | Layout Described | Components Listed | Mobile ✓ | A11y ✓ |
|--------|-----------------|-------------------|----------|---------|
| | | | ⬜ | ⬜ |

**Design tokens defined:** ⬜ Pending / ✅ Done  
**Component inventory complete:** ⬜ Pending / ✅ Done  
**Handoff to rajiblabs-dev complete:** ⬜ Pending / ✅ Done  

---

## 👷 Implementation (by rajiblabs-dev)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked  
**Depends on:** TAD ✅, UX Handoff ✅

**Phase 1 — Foundation**
| Task | Status | Notes |
|------|--------|-------|
| Data models + migrations | ⬜ | |
| API scaffolding (all endpoints stubbed) | ⬜ | |
| Auth middleware | ⬜ | |
| Frontend project scaffold | ⬜ | |
| API service layer | ⬜ | |
| Health endpoint `/health` | ⬜ | |

**Phase 2 — Core Features (Must Haves)**
| Feature | Backend ✓ | Frontend ✓ | Integrated ✓ |
|---------|-----------|-----------|--------------|
| | ⬜ | ⬜ | ⬜ |

**Phase 3 — Polish (Should Haves)**
| Feature | Status |
|---------|--------|
| | ⬜ |

**Environment variables required:**
```yaml
# List all env vars devops agent must configure
APP_DB_CONNECTION: ""
APP_JWT_SECRET: ""
APP_AZURE_KEYVAULT_URI: ""
# ...add more
```

**Known limitations / tech debt:**
- _[list any]_

---

## 🧪 QA Validation (by rajiblabs-qa)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked  
**Depends on:** Implementation Phase 2 ✅

**Test cycle results:**
| Test Case | Type | Status | Notes |
|-----------|------|--------|-------|
| | Functional | ⬜ | |
| | API | ⬜ | |
| | Security | ⬜ | |
| | Accessibility | ⬜ | |

**Defect log:**
| ID | Severity | Description | Assigned To | Status |
|----|----------|-------------|-------------|--------|
| | | | rajiblabs-dev | ⬜ Open |

**QA Verdict:** ⬜ Pending | ✅ GO | ❌ NO-GO  
**Reason (if NO-GO):** _[fill in]_

---

## 🚀 DevOps & Deployment (by rajiblabs-devops)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked

**Azure Resources Provisioned:**
| Resource | Type | Environment | Status |
|----------|------|-------------|--------|
| | Resource Group | prod | ⬜ |
| | App Service | prod | ⬜ |
| | Static Web App | prod | ⬜ |
| | SQL Database | prod | ⬜ |
| | Key Vault | prod | ⬜ |
| | App Insights | prod | ⬜ |

**GitHub Actions Pipelines:**
| Workflow File | Trigger | Status |
|---------------|---------|--------|
| `.github/workflows/pr.yml` | Pull Request | ⬜ Created |
| `.github/workflows/staging.yml` | Push to `develop` | ⬜ Created |
| `.github/workflows/production.yml` | Manual / Release tag | ⬜ Created |

**Environments:**
| Env | URL | Status |
|-----|-----|--------|
| Staging | | ⬜ Live |
| Production | | ⬜ Live |

**Smoke tests passed:** ⬜ Staging | ⬜ Production

---

## 📋 Release Approval (by rajiblabs-po)

**Status:** ⬜ Pending | ✅ Approved | ❌ Blocked

**Checklist:**
- [ ] QA Go verdict received
- [ ] No Critical/High defects open
- [ ] DevOps rollback documented
- [ ] Portfolio entry ready

**Approval decision:** _[Approved / Blocked with reason]_  
**Approved by:** rajiblabs-po  
**Date:** _[YYYY-MM-DD]_

---

## 📊 Portfolio Update (by rajiblabs-portfolio)

**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete  
**Depends on:** Release Approval ✅

- [ ] Project showcase entry written
- [ ] Skills updated
- [ ] Live URL verified
- [ ] `fallbackData.ts` update submitted to rajiblabs-dev

---

## 👀 Monitor Log (by rajiblabs-monitor)

**Last cycle:** _[YYYY-MM-DD HH:MM UTC]_  
**Active alerts:** _[list or "None"]_

---

## 🔄 Orchestration Log

Track every agent activation and handoff here:

| Timestamp | From | To | Action | Status |
|-----------|------|----|--------|--------|
| | USER | rajiblabs-po | Project description received | ✅ |
| | rajiblabs-po | rajiblabs-architect | Project Brief delivered | ⬜ |
| | rajiblabs-po | rajiblabs-ux | Project Brief delivered | ⬜ |
| | rajiblabs-architect | rajiblabs-dev | TAD delivered | ⬜ |
| | rajiblabs-ux | rajiblabs-dev | Design Handoff delivered | ⬜ |
| | rajiblabs-architect | rajiblabs-devops | TAD + infra requirements delivered | ⬜ |
| | rajiblabs-dev | rajiblabs-qa | Phase 2 complete, ready for QA | ⬜ |
| | rajiblabs-qa | rajiblabs-devops | QA GO verdict delivered | ⬜ |
| | rajiblabs-devops | rajiblabs-po | Production deploy complete | ⬜ |
| | rajiblabs-po | rajiblabs-portfolio | Release approved | ⬜ |

---

## 📌 Open Questions & Blockers

| # | Question | Raised By | Assigned To | Status |
|---|----------|-----------|-------------|--------|
| 1 | | | | ⬜ Open |

---

## 🗂️ Artifacts Index

Links to all deliverables produced:

| Artifact | File/Location | Produced By | Status |
|----------|---------------|-------------|--------|
| Project Brief | (in this file) | rajiblabs-po | ⬜ |
| Technical Architecture Document | (in this file) | rajiblabs-architect | ⬜ |
| UX Brief | (in this file) | rajiblabs-ux | ⬜ |
| Design Handoff | (in this file) | rajiblabs-ux | ⬜ |
| Backend source code | `backend/` | rajiblabs-dev | ⬜ |
| Frontend source code | `frontend/` | rajiblabs-dev | ⬜ |
| PR pipeline | `.github/workflows/pr.yml` | rajiblabs-devops | ⬜ |
| Staging pipeline | `.github/workflows/staging.yml` | rajiblabs-devops | ⬜ |
| Production pipeline | `.github/workflows/production.yml` | rajiblabs-devops | ⬜ |
| QA Test Report | (in this file) | rajiblabs-qa | ⬜ |
| Portfolio entry | `agents/portfolio/<slug>.json` | rajiblabs-portfolio | ⬜ |
