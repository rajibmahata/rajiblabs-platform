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

## 👷 Implementation

**Mode:** ⬜ Solo (`rajiblabs-dev`) | ⬜ Squad (`rajiblabs-dev-lead` + sub-agents)  
**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked  
**Depends on:** TAD ✅, UX Handoff ✅

### Squad Mode Decision
```
Must Have feature count: __
Has external integrations: yes / no
Squad mode: SOLO / SQUAD
```

### Implementation Assignment Plan (Squad mode — filled by rajiblabs-dev-lead)
| Task | Assigned To | Depends On | Status |
|------|-------------|-----------|--------|
| | rajiblabs-dev-backend | | ⬜ |
| | rajiblabs-dev-frontend | | ⬜ |
| | rajiblabs-dev-integration | backend stubs ready | ⬜ |

### Phase 1 — Foundation
| Task | Agent | Status | Notes |
|------|-------|--------|-------|
| Data models + migrations | dev-backend | ⬜ | |
| API scaffolding (all endpoints stubbed) | dev-backend | ⬜ | |
| Auth middleware | dev-backend | ⬜ | |
| Error handling middleware | dev-backend | ⬜ | |
| Frontend project scaffold + routing | dev-frontend | ⬜ | |
| TypeScript types (all DTOs) | dev-frontend | ⬜ | |
| API service layer | dev-frontend | ⬜ | |
| Base UI components | dev-frontend | ⬜ | |
| Health endpoint `/health` | dev-backend | ⬜ | |

### Phase 2 — Core Features (Must Haves)
| Feature | Backend Agent | Backend ✓ | Frontend Agent | Frontend ✓ | Integration ✓ |
|---------|--------------|-----------|----------------|-----------|--------------|
| | dev-backend | ⬜ | dev-frontend | ⬜ | ⬜ |

### Phase 3 — Polish (Should Haves)
| Feature | Assigned To | Status |
|---------|-------------|--------|
| | | ⬜ |

### Environment Variables (consolidated by rajiblabs-dev-integration)
```yaml
# Backend (App Service / Key Vault)
ConnectionStrings__DefaultConnection: ""
Jwt__Key: ""
Jwt__Issuer: ""
Jwt__Audience: ""
AllowedOrigins: ""
KeyVaultUri: ""
# Add more as discovered

# Frontend (Vite .env)
VITE_API_BASE_URL: ""
# Add more as discovered
```

**Known limitations / tech debt:**
- _[list any]_

---

## 🧪 QA Validation

**Mode:** ⬜ Solo (`rajiblabs-qa`) | ⬜ Squad (`rajiblabs-qa-lead` + sub-agents)  
**Status:** ⬜ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked  
**Depends on:** Implementation Phase 2 ✅

### QA Squad Sub-Agent Results
| Sub-Agent | Tests Run | Passed | Failed | Open Defects | Status |
|-----------|-----------|--------|--------|-------------|--------|
| rajiblabs-qa-functional | | | | | ⬜ |
| rajiblabs-qa-security | | | | | ⬜ |
| rajiblabs-qa-accessibility | | | | | ⬜ |

### Acceptance Criteria Coverage
| Feature | Criterion | Test Case | Result |
|---------|-----------|-----------|--------|
| | | TC-001 | ⬜ |

### Consolidated Defect Log
| ID | Severity | Found By | Description | Assigned To | Status |
|----|----------|----------|-------------|-------------|--------|
| QA-001 | | qa-functional | | dev-backend | ⬜ Open |

**QA Lead Verdict:** ⬜ Pending | ✅ GO | ❌ NO-GO  
**Reason (if NO-GO):** _[fill in]_  
**Test cycle #:** 1

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
