# 🏭 RajibLabs AI Workforce — Master Workflow
**Platform:** OpenClaw AI  
**Repository:** rajibmahata/rajiblabs-platform

---

## Workforce Overview

The RajibLabs AI Workforce has two operating modes. The **Orchestrator** selects the right mode automatically based on project complexity.

### Core Agents (all projects)

| Agent | ID | Role | Schedule |
|-------|----|------|----------|
| 🎯 [rajiblabs-bidder](./rajiblabs-bidder.md) | — | Freelance Acquisition & Bid Manager | Daily 8:30 AM IST + on-demand |
| 📋 [rajiblabs-po](./rajiblabs-po.md) | 51011256 | Product Owner | Daily 8 AM IST + on-demand |
| 🧠 [rajiblabs-architect](./rajiblabs-architect.md) | e441e421 | Architect & PM | On-demand |
| 🎨 [rajiblabs-ux](./rajiblabs-ux.md) | 63c7532d | UI/UX Designer | On-demand |
| 🚀 [rajiblabs-devops](./rajiblabs-devops.md) | 16954a53 | DevOps (CI/CD, Azure) | On-demand |
| 👀 [rajiblabs-monitor](./rajiblabs-monitor.md) | eb6f6a39 | GitHub Monitor | Every 30 min |
| 📊 [rajiblabs-portfolio](./rajiblabs-portfolio.md) | 0a069639 | Portfolio Content | Daily 9 AM IST |
| 💼 [rajiblabs-bidder](./rajiblabs-bidder.md) | — | Freelance Opportunity Scout & Proposal Writer | Daily 7 AM IST + on-demand |

### Solo Mode — Simple Projects (1-3 Must Have features)

| Agent | Role |
|-------|------|
| 👷 [rajiblabs-dev](./rajiblabs-dev.md) | Full-stack developer (single agent) |
| 🧪 [rajiblabs-qa](./rajiblabs-qa.md) | QA validator (single agent) |

### Squad Mode — Complex Projects (4+ Must Haves, or external APIs, or auth)

**Dev Squad** — parallel implementation by specialisation:

| Agent | Role | Runs In Parallel With |
|-------|------|-----------------------|
| 👷‍♂️ [rajiblabs-dev-lead](./rajiblabs-dev-lead.md) | Dev squad coordinator | — |
| 🔧 [rajiblabs-dev-backend](./rajiblabs-dev-backend.md) | .NET 8 API, EF Core, DB, auth | `rajiblabs-dev-frontend` |
| 🖥️ [rajiblabs-dev-frontend](./rajiblabs-dev-frontend.md) | React, TypeScript, Vite, Tailwind | `rajiblabs-dev-backend` |
| 🔗 [rajiblabs-dev-integration](./rajiblabs-dev-integration.md) | API wiring, external services, contract verification | After backend stubs ready |

**QA Squad** — parallel validation by specialisation:

| Agent | Role | Runs In Parallel With |
|-------|------|-----------------------|
| 🧪 [rajiblabs-qa-lead](./rajiblabs-qa-lead.md) | QA squad coordinator + final verdict | — |
| ✅ [rajiblabs-qa-functional](./rajiblabs-qa-functional.md) | User flows, API contract, regression | `rajiblabs-qa-security`, `rajiblabs-qa-accessibility` |
| 🔐 [rajiblabs-qa-security](./rajiblabs-qa-security.md) | OWASP Top 10, auth bypass, injection | `rajiblabs-qa-functional`, `rajiblabs-qa-accessibility` |
| ♿ [rajiblabs-qa-accessibility](./rajiblabs-qa-accessibility.md) | WCAG 2.1 AA, keyboard, responsive | `rajiblabs-qa-functional`, `rajiblabs-qa-security` |

---

## ⚡ How to Start a New Project (3 Steps)

### Step 1 — Load the Orchestrator in OpenClaw
Open a new chat in OpenClaw and paste the **entire contents** of [`ORCHESTRATOR.md`](./ORCHESTRATOR.md) as your system prompt / persona instruction.

### Step 2 — Describe your project
Type your project description in plain English. The Orchestrator selects Solo or Squad mode automatically.

```
Example:
"Build a SaaS invoicing tool where freelancers can create invoices, 
track payments, and send automated payment reminders. 
Tech: React frontend, .NET 8 backend, Azure SQL database."
```

### Step 3 — Save the state file between sessions
At the end of each session, save the `agents/state/<project-slug>.md` output.  
Paste it back at the start of your next session and the Orchestrator resumes exactly where it left off.

---

## 🧠 Memory & State Tracking

All project progress is tracked in a **project state file**: `agents/state/<project-slug>.md`

- Created from [`project-state-template.md`](./project-state-template.md) by `rajiblabs-po` at project start.
- Every agent reads it before starting work and writes results back to it.
- Contains: squad mode decision, feature status per sub-agent, QA sub-agent results, deployment URLs, open questions.
- Acts as **persistent memory** across sessions — paste into OpenClaw to resume.

---

## Full Automated Lifecycle

### End-to-End: Acquisition → Delivery → Follow-up
```mermaid
flowchart TD
    BIDDER[🎯 rajiblabs-bidder<br/>Scan Freelancer.in → Bid → Track] -->|Awarded| PO
    USER[🧑 Rajib: Project Description] --> ORCH
    ORCH[🤖 ORCHESTRATOR] --> PO[📋 rajiblabs-po]
    PO --> ARCH[🧠 rajiblabs-architect]
    PO --> UX[🎨 rajiblabs-ux]
    ARCH --> DEVOPS[🚀 rajiblabs-devops]
    ARCH --> DEV[👷 Dev Pipeline]
    UX --> DEV
    DEV --> QA[🧪 QA Pipeline]
    QA -->|GO| PO_APPROVE[📋 rajiblabs-po<br/>Release]
    PO_APPROVE --> DEVOPS_PROD[🚀 Production Deploy]
    DEVOPS_PROD --> PORTFOLIO[📊 rajiblabs-portfolio]
    DEVOPS_PROD --> MONITOR[👀 rajiblabs-monitor]
    DEVOPS_PROD --> BIDDER_FOLLOW[🎯 rajiblabs-bidder<br/>Demo + Follow-up + Testimonial]
```

### Solo Mode Flow
```mermaid
flowchart TD
    BIDDER_SOLO[🎯 rajiblabs-bidder<br/>Finds project → bids → awarded] -->|Handoff| ORCH_SOLO
    USER_SOLO[🧑 Rajib: Project Description] --> ORCH_SOLO
    ORCH_SOLO[🤖 ORCHESTRATOR<br/>Solo mode: ≤3 Must Have features]
    ORCH --> PO[📋 rajiblabs-po]
    PO --> ARCH[🧠 rajiblabs-architect]
    PO --> UX[🎨 rajiblabs-ux]
    ARCH --> DEVOPS[🚀 rajiblabs-devops\nCI/CD + Bicep]
    ARCH --> DEV[👷 rajiblabs-dev\nFull-stack solo]
    UX --> DEV
    DEV --> QA[🧪 rajiblabs-qa\nSolo QA]
    QA -->|NO-GO| DEV
    QA -->|GO| PO_APPROVE[📋 rajiblabs-po\nRelease Approval]
    PO_APPROVE --> DEVOPS_PROD[🚀 rajiblabs-devops\nProduction Deploy]
    DEVOPS_PROD --> PORTFOLIO[📊 rajiblabs-portfolio]
    DEVOPS_PROD --> MONITOR[👀 rajiblabs-monitor]
    DEVOPS_PROD --> BIDDER_FOLLOW_SOLO[🎯 rajiblabs-bidder<br/>Client follow-up]
```

### Squad Mode Flow
```mermaid
flowchart TD
    BIDDER_SQUAD[🎯 rajiblabs-bidder<br/>Finds project → bids → awarded] -->|Handoff| ORCH_SQUAD
    USER_SQUAD[🧑 Rajib: Project Description] --> ORCH_SQUAD
    ORCH_SQUAD[🤖 ORCHESTRATOR<br/>Squad mode: 4+ Must Have features]
    ORCH --> PO[📋 rajiblabs-po]
    PO --> ARCH[🧠 rajiblabs-architect]
    PO --> UX[🎨 rajiblabs-ux]
    ARCH --> DEVOPS[🚀 rajiblabs-devops\nCI/CD + Bicep]
    ARCH --> DEVLEAD[👷‍♂️ rajiblabs-dev-lead\nAssigns swim lanes]
    UX --> DEVLEAD
    DEVLEAD --> BACKEND[🔧 rajiblabs-dev-backend]
    DEVLEAD --> FRONTEND[🖥️ rajiblabs-dev-frontend]
    BACKEND --> INTEGRATION[🔗 rajiblabs-dev-integration\nAPI wiring + contract verify]
    FRONTEND --> INTEGRATION
    INTEGRATION --> QALEAD[🧪 rajiblabs-qa-lead\nAssigns QA swim lanes]
    QALEAD --> QAFUNC[✅ rajiblabs-qa-functional]
    QALEAD --> QASEC[🔐 rajiblabs-qa-security]
    QALEAD --> QAAX[♿ rajiblabs-qa-accessibility]
    QAFUNC --> VERDICT[🧪 rajiblabs-qa-lead\nConsolidated Go/No-Go]
    QASEC --> VERDICT
    QAAX --> VERDICT
    VERDICT -->|NO-GO| DEVLEAD
    VERDICT -->|GO| PO_APPROVE[📋 rajiblabs-po\nRelease Approval]
    PO_APPROVE --> DEVOPS_PROD[🚀 rajiblabs-devops\nProduction Slot Swap]
    DEVOPS_PROD --> PORTFOLIO[📊 rajiblabs-portfolio]
    DEVOPS_PROD --> MONITOR[👀 rajiblabs-monitor]
    DEVOPS_PROD --> BIDDER_FOLLOW_SQUAD[🎯 rajiblabs-bidder<br/>Client follow-up]
```

---

## Phases Summary

| Phase | Name | Agents | Gate |
|-------|------|--------|------|
| -1 | Acquisition | bidder | Bid submitted → Award detection → Handoff to PO |
| 0 | Discovery | po, architect, ux | Project Brief + TAD + UX Brief + mode decision |
| 1 | Foundation | dev + devops | dev-lead + dev-backend + dev-frontend + devops | Scaffold compiles + CI pipelines live |
| 2 | Core Features | dev | dev-lead + dev-backend + dev-frontend + dev-integration | All Must Haves complete |
| 2 | Validation | qa | qa-lead + qa-functional + qa-security + qa-accessibility | QA GO verdict |
| 3 | Polish & Deploy | dev, qa, devops, po | dev squads, qa squads, devops, po | Release Approval + smoke test |
| 4 | Post-Launch | portfolio, monitor | portfolio, monitor | Portfolio updated + monitoring active |
| 5 | Follow-up | bidder | bidder | Demo coordination + Client follow-up + Testimonial + Warm lead registered |

---

## What Each Agent Produces (Real Files)

| Agent | Produces |
|-------|---------|
| `rajiblabs-bidder` | Daily scan reports, drafted proposals, bid state files, client follow-up messages |
| `rajiblabs-po` | Project Brief, backlog, mode decision, Release Approval |
| `rajiblabs-architect` | TAD + data models + API contract |
| `rajiblabs-ux` | UX Brief + component inventory + Design Handoff |
| `rajiblabs-dev` *(solo)* | Complete backend + frontend code |
| `rajiblabs-dev-backend` *(squad)* | .NET 8 API, EF Core entities, services, unit tests |
| `rajiblabs-dev-frontend` *(squad)* | React pages, components, hooks, service layer, component tests |
| `rajiblabs-dev-integration` *(squad)* | Contract verification report, external service wiring, env var consolidation |
| `rajiblabs-devops` | `.github/workflows/pr.yml`, `staging.yml`, `production.yml`, `infra/main.bicep` |
| `rajiblabs-qa` *(solo)* | Full test report + Go/No-Go verdict |
| `rajiblabs-qa-functional` *(squad)* | Functional + API test cases + defects |
| `rajiblabs-qa-security` *(squad)* | OWASP Top 10 audit + security defects |
| `rajiblabs-qa-accessibility` *(squad)* | WCAG 2.1 AA audit + responsive layout results |
| `rajiblabs-qa-lead` *(squad)* | Consolidated Test Report + final Go/No-Go verdict |
| `rajiblabs-portfolio` | Project Showcase Entry + `fallbackData.ts` patch |
| `rajiblabs-monitor` | 30-minute cycle reports, real-time alerts |
| `rajiblabs-bidder` | Daily lead scan, qualified proposals (ready to submit), bid tracker updates, weekly performance report |

---

## Agent Handoff Protocol

When any agent completes its output, it MUST:
1. Mark its section ✅ in the state file.
2. Announce the handoff:
```
## ✅ Handoff from rajiblabs-[agent]
Output produced: [deliverable]
Delivered to: rajiblabs-[next agent]
Next action: [specific instruction]
Open questions: [any / none]
```
3. The Orchestrator activates the next agent automatically.

---

## Escalation Path

```
Agent blocked on scope/priority     →  rajiblabs-po
Agent blocked on technical design   →  rajiblabs-architect
Contract bug (backend vs frontend)  →  rajiblabs-dev-integration → route to owner
Security finding (Critical/High)    →  rajiblabs-architect + rajiblabs-devops (IMMEDIATE)
Production incident                 →  rajiblabs-devops (IMMEDIATE)
QA NO-GO after 2 fix cycles        →  rajiblabs-po (scope/design decision needed)
Sub-agent blocker in squad          →  Lead agent (dev-lead / qa-lead)
```

---

## Quality Gates (Nothing Passes Without These)

| Gate | Enforced By | Required Before |
|------|-------------|-----------------|
| Project Brief + mode decision complete | rajiblabs-po | TAD and UX work starts |
| TAD approved | rajiblabs-architect | Any code is written |
| Foundation scaffold compiles | dev / dev-lead | Phase 2 features start |
| CI passing on PR | rajiblabs-devops | Merge to develop |
| QA GO verdict (solo or lead) | rajiblabs-qa / rajiblabs-qa-lead | Production deploy |
| Release Approval | rajiblabs-po | rajiblabs-devops triggers production |
| Production smoke test | rajiblabs-devops | Deploy declared complete |

---

## Security Non-Negotiables (All Agents, Always)

1. No secrets in code or committed files — Key Vault or environment variables only.
2. Validate all API inputs at the boundary (never trust client input).
3. Parameterised queries only — never concatenate SQL strings.
4. HTTPS enforced on all environments including staging.
5. Dependabot enabled on every repository.
6. Least-privilege service principals and managed identities.
7. Sanitise all user-generated content before rendering (prevent XSS).
8. Every API endpoint is either explicitly public or requires auth.

---

## Tech Stack Defaults

| Layer | Default |
|-------|---------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | .NET 8 ASP.NET Core Minimal API |
| ORM | Entity Framework Core (code-first) |
| Database | Azure SQL Database |
| Frontend Hosting | Azure Static Web Apps |
| Backend Hosting | Azure App Service (Linux) |
| Secrets | Azure Key Vault |
| CI/CD | GitHub Actions |
| Monitoring | Azure Application Insights |
| Auth | JWT Bearer / Azure AD B2C |

---

## File Structure

```
agents/
├── README.md                          ← This file
├── ORCHESTRATOR.md                    ← Load this in OpenClaw to start any project
├── project-state-template.md          ← Shared memory template (copied per project)
│
├── Core Agents
│   ├── rajiblabs-bidder.md            ← 🎯 Freelance acquisition & bid manager (NEW)
│   ├── rajiblabs-po.md
│   ├── rajiblabs-architect.md
│   ├── rajiblabs-ux.md
│   ├── rajiblabs-devops.md
│   ├── rajiblabs-monitor.md
│   └── rajiblabs-portfolio.md
│
├── Solo Mode
│   ├── rajiblabs-dev.md               ← Full-stack (solo projects)
│   └── rajiblabs-qa.md                ← QA validator (solo projects)
│
├── Dev Squad (complex projects)
│   ├── rajiblabs-dev-lead.md          ← Squad coordinator
│   ├── rajiblabs-dev-backend.md       ← .NET 8 API specialist
│   ├── rajiblabs-dev-frontend.md      ← React/TypeScript specialist
│   └── rajiblabs-dev-integration.md   ← API wiring + external services
│
├── QA Squad (complex projects)
│   ├── rajiblabs-qa-lead.md           ← Squad coordinator + final verdict
│   ├── rajiblabs-qa-functional.md     ← User flows + API contract tests
│   ├── rajiblabs-qa-security.md       ← OWASP Top 10 + auth tests
│   └── rajiblabs-qa-accessibility.md  ← WCAG 2.1 AA + responsive tests
│
├── bids/                              ← Bid tracking (NEW)
│   └── <project-slug>-bid.md          ← Per-bid lifecycle tracking
│
└── state/
    └── <project-slug>.md              ← Per-project memory file
```

---

## Quick Reference: Who to Ask

| Question | Solo Mode | Squad Mode |
|----------|-----------|-----------|
| Find projects & bid | `rajiblabs-bidder` | `rajiblabs-bidder` |
| What should we build? | `rajiblabs-po` | `rajiblabs-po` |
| How should we build it? | `rajiblabs-architect` | `rajiblabs-architect` |
| What should it look like? | `rajiblabs-ux` | `rajiblabs-ux` |
| Write the backend code | `rajiblabs-dev` | `rajiblabs-dev-backend` |
| Write the frontend code | `rajiblabs-dev` | `rajiblabs-dev-frontend` |
| Wire APIs / external services | `rajiblabs-dev` | `rajiblabs-dev-integration` |
| Coordinate all dev work | — | `rajiblabs-dev-lead` |
| Test user flows + API | `rajiblabs-qa` | `rajiblabs-qa-functional` |
| Security audit | `rajiblabs-qa` | `rajiblabs-qa-security` |
| Accessibility audit | `rajiblabs-qa` | `rajiblabs-qa-accessibility` |
| Final QA verdict | `rajiblabs-qa` | `rajiblabs-qa-lead` |
| Deploy it / set up CI-CD | `rajiblabs-devops` | `rajiblabs-devops` |
| What's happening in repo? | `rajiblabs-monitor` | `rajiblabs-monitor` |
| Update the portfolio | `rajiblabs-portfolio` | `rajiblabs-portfolio` |
| Follow up with client | `rajiblabs-bidder` | `rajiblabs-bidder` |
| Run the full project end-to-end | **ORCHESTRATOR** | **ORCHESTRATOR** |

---

## Workforce Overview

This is the master instruction file for the **RajibLabs AI Workforce** — a team of 9 specialised AI agents that collaborate to take a project from acquisition to production.

| Agent | ID | Role | Schedule |
|-------|----|------|----------|
| 🎯 [rajiblabs-bidder](./rajiblabs-bidder.md) | — | Freelance Acquisition & Bid Manager | Daily 8:30 AM IST + on-demand |
| 📋 [rajiblabs-po](./rajiblabs-po.md) | 51011256 | Product Owner | Daily 8 AM IST + on-demand |
| 🎨 [rajiblabs-ux](./rajiblabs-ux.md) | 63c7532d | UI/UX Designer | On-demand |
| 🧠 [rajiblabs-architect](./rajiblabs-architect.md) | e441e421 | Architect & PM | On-demand |
| 👷 [rajiblabs-dev](./rajiblabs-dev.md) | 87745ce0 | Developer (→ Copilot ACP) | On-demand |
| 🧪 [rajiblabs-qa](./rajiblabs-qa.md) | 7a4d415c | QA Validator | On-demand |
| 🚀 [rajiblabs-devops](./rajiblabs-devops.md) | 16954a53 | DevOps (CI/CD, Azure) | On-demand |
| 👀 [rajiblabs-monitor](./rajiblabs-monitor.md) | eb6f6a39 | GitHub Monitor | Every 30 minutes |
| 📊 [rajiblabs-portfolio](./rajiblabs-portfolio.md) | 0a069639 | Portfolio Content | Daily 9 AM IST |

---

## ⚡ How to Start a New Project (3 Steps)

### Step 1 — Load the Orchestrator in OpenClaw
Open a new chat in OpenClaw and paste the **entire contents** of [`ORCHESTRATOR.md`](./ORCHESTRATOR.md) as your system prompt / persona instruction.

### Step 2 — Describe your project
Type your project description in plain English. That's it.

```
Example:
"Build a SaaS invoicing tool where freelancers can create invoices, 
track payments, and send automated payment reminders. 
Tech: React frontend, .NET 8 backend, Azure SQL database."
```

### Step 3 — Save the state file between sessions
At the end of each session, save the `agents/state/<project-slug>.md` output.  
Paste it back at the start of your next session and the Orchestrator will resume exactly where it left off.

---

## 🧠 Memory & State Tracking

All project progress is tracked in a **project state file**:

```
agents/state/<project-slug>.md
```

- Created from [`project-state-template.md`](./project-state-template.md) by `rajiblabs-po` at project start.
- Every agent reads it before starting work and writes results back to it.
- Contains: feature status, agent outputs, QA results, deployment URLs, open questions.
- Acts as the **persistent memory** across sessions — paste into OpenClaw to resume.

---

## Full Automated Lifecycle

```mermaid
flowchart TD
    USER[🧑 User: Project Description] --> ORCH[🤖 ORCHESTRATOR\nLoads all agents, creates state file]
    ORCH --> PO[📋 rajiblabs-po\nProject Brief + Backlog + Acceptance Criteria]
    PO --> ARCH[🧠 rajiblabs-architect\nTechnical Architecture Document]
    PO --> UX[🎨 rajiblabs-ux\nUX Brief + Design Handoff]
    ARCH --> DEV[👷 rajiblabs-dev\nPhase 1: Scaffold + Phase 2: Features]
    UX --> DEV
    ARCH --> DEVOPS_SETUP[🚀 rajiblabs-devops\nCI/CD YAML + Azure Bicep infra]
    DEV --> QA[🧪 rajiblabs-qa\nTest Plan + Validation + Go/No-Go]
    QA -->|NO-GO ❌| DEV
    QA -->|GO ✅| PO_APPROVE[📋 rajiblabs-po\nRelease Approval]
    PO_APPROVE --> DEVOPS_DEPLOY[🚀 rajiblabs-devops\nProduction Slot Swap Deploy]
    DEVOPS_DEPLOY --> PORTFOLIO[📊 rajiblabs-portfolio\nPortfolio Showcase Entry]
    DEVOPS_DEPLOY --> MONITOR[👀 rajiblabs-monitor\n30-min repo + CI monitoring]
    PORTFOLIO --> DONE[🎉 Project Complete\nLive URL + State File Updated]
    MONITOR -.->|Alerts| DEV
    MONITOR -.->|Alerts| DEVOPS_DEPLOY
```

---

## Phases Summary

| Phase | Name | Agents Active | Gate |
|-------|------|---------------|------|
| 0 | Discovery | po, architect, ux | Project Brief + TAD + UX Brief approved |
| 1 | Foundation | dev, devops | Scaffold compiles + CI pipelines live |
| 2 | Core Features | dev, qa | All Must Haves pass QA GO verdict |
| 3 | Polish & Deploy | dev, qa, devops, po | Release Approval + Production smoke test |
| 4 | Post-Launch | portfolio, monitor | Portfolio updated + monitoring active |

---

## What Each Agent Produces (Real Files)

| Agent | Produces |
|-------|---------|
| `rajiblabs-po` | Project Brief section in state file, workforce activation instructions |
| `rajiblabs-architect` | TAD + data models + API contract in state file |
| `rajiblabs-ux` | UX Brief + component inventory + Design Handoff in state file |
| `rajiblabs-dev` | Complete backend code (`backend/`), complete frontend code (`frontend/`), `.env.example` |
| `rajiblabs-devops` | `.github/workflows/pr.yml`, `.github/workflows/staging.yml`, `.github/workflows/production.yml`, `infra/main.bicep`, `infra/parameters.prod.json` |
| `rajiblabs-qa` | Test Plan + Test Report + defect list in state file |
| `rajiblabs-portfolio` | Project Showcase Entry JSON + `fallbackData.ts` patch |
| `rajiblabs-monitor` | 30-minute cycle reports, real-time alerts |

---

## Agent Communication Protocol

When an agent completes its output, it MUST:
1. Mark its section ✅ in the state file.
2. Announce the handoff:

```
## ✅ Handoff from rajiblabs-[agent]
Output produced: [deliverable name]
Delivered to: rajiblabs-[next agent]
Next action: [specific instruction]
Open questions: [any / none]
```

3. The Orchestrator then activates the next agent automatically.

---

## Escalation Path

```
Agent blocked on scope/priority  →  rajiblabs-po
Agent blocked on technical design →  rajiblabs-architect
Security finding (any severity)   →  rajiblabs-architect + rajiblabs-devops (immediate)
Production incident               →  rajiblabs-devops (immediate, skip normal cycle)
QA NO-GO after 2 fix cycles      →  rajiblabs-po (scope/design decision needed)
```

---

## Quality Gates (Nothing Passes Without These)

| Gate | Enforced By | Required Before |
|------|-------------|-----------------|
| Project Brief complete | rajiblabs-po | TAD and UX work starts |
| TAD approved | rajiblabs-architect | Any code is written |
| CI passing on PR | rajiblabs-devops | Merge to develop |
| QA GO verdict | rajiblabs-qa | Production deploy |
| Release Approval | rajiblabs-po | rajiblabs-devops triggers production |
| Production smoke test | rajiblabs-devops | Deploy declared complete |

---

## Security Non-Negotiables (All Agents, Always)

1. No secrets in code or committed files — Key Vault or environment variables only.
2. Validate all API inputs at the boundary.
3. Parameterised queries only — never concatenate SQL strings.
4. HTTPS enforced on all environments.
5. Dependabot enabled on every repository.
6. Least-privilege service principals and managed identities.
7. Sanitise all user-generated content before rendering (no XSS).
8. Every API endpoint is either explicitly public or requires auth token.

---

## Tech Stack Defaults

| Layer | Default |
|-------|---------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | .NET 8 ASP.NET Core Minimal API |
| ORM | Entity Framework Core (code-first) |
| Database | Azure SQL Database |
| Frontend Hosting | Azure Static Web Apps |
| Backend Hosting | Azure App Service (Linux) |
| Secrets | Azure Key Vault |
| CI/CD | GitHub Actions |
| Monitoring | Azure Application Insights |
| Auth | JWT Bearer / Azure AD B2C |

---

## File Structure

```
agents/
├── README.md                      ← This file (master workflow)
├── ORCHESTRATOR.md                ← Load this in OpenClaw to start any project
├── project-state-template.md      ← Shared memory template (copied per project)
├── rajiblabs-po.md                ← Product Owner
├── rajiblabs-architect.md         ← Architect & PM
├── rajiblabs-ux.md                ← UI/UX Designer
├── rajiblabs-dev.md               ← Developer
├── rajiblabs-qa.md                ← QA Validator
├── rajiblabs-devops.md            ← DevOps (real GitHub Actions YAML + Bicep)
├── rajiblabs-monitor.md           ← GitHub Monitor (30-min)
├── rajiblabs-portfolio.md         ← Portfolio Content
└── state/
    └── <project-slug>.md          ← Per-project memory (created at project start)
```

---

## Quick Reference: Who to Ask

| Question | Ask |
|----------|-----|
| What should we build? | `rajiblabs-po` |
| How should we build it? | `rajiblabs-architect` |
| What should it look like? | `rajiblabs-ux` |
| Write the code | `rajiblabs-dev` |
| Does it work correctly? | `rajiblabs-qa` |
| Deploy it / set up CI-CD | `rajiblabs-devops` |
| What's happening in the repo right now? | `rajiblabs-monitor` |
| Update the portfolio | `rajiblabs-portfolio` |
| Run the full project end-to-end | **ORCHESTRATOR** |

---

## Workforce Overview

This is the master instruction file for the **RajibLabs AI Workforce** — a team of 8 specialised AI agents that collaborate to take a project from idea to production.

| Agent | ID | Role | Schedule |
|-------|----|------|----------|
| 📋 [rajiblabs-po](./rajiblabs-po.md) | 51011256 | Product Owner | Daily 8 AM IST + on-demand |
| 🎨 [rajiblabs-ux](./rajiblabs-ux.md) | 63c7532d | UI/UX Designer | On-demand |
| 🧠 [rajiblabs-architect](./rajiblabs-architect.md) | e441e421 | Architect & PM | On-demand |
| 👷 [rajiblabs-dev](./rajiblabs-dev.md) | 87745ce0 | Developer (→ Copilot ACP) | On-demand |
| 🧪 [rajiblabs-qa](./rajiblabs-qa.md) | 7a4d415c | QA Validator | On-demand |
| 🚀 [rajiblabs-devops](./rajiblabs-devops.md) | 16954a53 | DevOps (CI/CD, Azure) | On-demand |
| 👀 [rajiblabs-monitor](./rajiblabs-monitor.md) | eb6f6a39 | GitHub Monitor | Every 30 minutes |
| 📊 [rajiblabs-portfolio](./rajiblabs-portfolio.md) | 0a069639 | Portfolio Content | Daily 9 AM IST |

---

## How to Start a New Project

**Simply provide a project description in plain English.** The workforce will self-organise.

### Example
> "Build a SaaS invoicing tool where freelancers can create invoices, track payments, and send automated payment reminders."

The workforce will automatically:
1. `rajiblabs-po` → writes Project Brief with feature backlog and acceptance criteria
2. `rajiblabs-architect` → writes Technical Architecture Document
3. `rajiblabs-ux` → writes UX Brief and Design Handoff
4. `rajiblabs-dev` → implements the features
5. `rajiblabs-qa` → validates all features
6. `rajiblabs-devops` → deploys to Azure
7. `rajiblabs-portfolio` → updates portfolio

---

## Full Project Lifecycle

```mermaid
flowchart TD
    USER[🧑 User: Project Description] --> PO[📋 rajiblabs-po\nProject Brief + Acceptance Criteria]
    PO --> ARCH[🧠 rajiblabs-architect\nTechnical Architecture Document]
    PO --> UX[🎨 rajiblabs-ux\nUX Brief + Design Handoff]
    ARCH --> DEV[👷 rajiblabs-dev\nImplementation]
    UX --> DEV
    ARCH --> DEVOPS_SETUP[🚀 rajiblabs-devops\nCI/CD + Azure Setup]
    DEV --> QA[🧪 rajiblabs-qa\nValidation + Test Report]
    QA -->|Go ✅| DEVOPS_DEPLOY[🚀 rajiblabs-devops\nProduction Deploy]
    QA -->|No-Go ❌| DEV
    DEVOPS_DEPLOY --> PO_APPROVE[📋 rajiblabs-po\nRelease Approval]
    PO_APPROVE --> PORTFOLIO[📊 rajiblabs-portfolio\nPortfolio Update]
    MONITOR[👀 rajiblabs-monitor\nEvery 30 min] -.->|Alerts| DEV
    MONITOR -.->|Alerts| DEVOPS_DEPLOY
    MONITOR -.->|Alerts| ARCH
```

---

## Agent Communication Rules

### How Agents Hand Off Work
When an agent completes its output, it must:
1. State clearly which output it produced (e.g., "✅ Technical Architecture Document complete").
2. State which agent(s) should receive it and act next.
3. List any open questions or dependencies that must be resolved before the next agent proceeds.

### Format for Agent-to-Agent Handoff
```
## ✅ Handoff from rajiblabs-[agent]

**Output produced:** [Name of deliverable]
**Delivered to:** rajiblabs-[receiving-agent]
**Next action required:** [What the receiving agent should do]
**Open questions (if any):**
- [Question 1 — route to rajiblabs-po or rajiblabs-architect]
```

### Escalation Path
```
Any agent blocker → rajiblabs-architect
Scope / priority decision → rajiblabs-po
Security finding → rajiblabs-architect + rajiblabs-devops (immediate)
Production incident → rajiblabs-devops (immediate)
```

---

## Scheduled Agent Cadence

```
08:00 IST daily  → rajiblabs-po      Daily standup + backlog grooming
09:00 IST daily  → rajiblabs-portfolio  Portfolio update + GitHub activity digest
Every 30 min     → rajiblabs-monitor  Repository scan + CI/CD monitoring
```

---

## Project Phases

Every project follows these standard phases:

### Phase 0: Discovery (rajiblabs-po + rajiblabs-architect + rajiblabs-ux)
- Project Brief
- Technical Architecture Document
- UX Brief
- **Gate:** All three documents approved by `rajiblabs-po` before Phase 1 starts

### Phase 1: Foundation (rajiblabs-dev + rajiblabs-devops)
- Backend data layer (models, database, migrations)
- API scaffolding (endpoints stubbed)
- CI/CD pipeline live
- Azure infrastructure provisioned
- **Gate:** `rajiblabs-qa` smoke test passes

### Phase 2: Core Features (rajiblabs-dev)
- Must Have features implemented (frontend + backend)
- Integration tests written
- **Gate:** `rajiblabs-qa` full test cycle passes, no Critical/High defects

### Phase 3: Polish & Deploy (rajiblabs-dev + rajiblabs-qa + rajiblabs-devops)
- Should Have features (if time permits)
- Performance optimisation
- Accessibility audit passes
- Production deployment
- **Gate:** `rajiblabs-po` Release Approval

### Phase 4: Post-Launch (rajiblabs-portfolio + rajiblabs-monitor)
- Portfolio updated
- Monitoring active
- Post-launch bug fixes (if any)

---

## Quality Gates Summary

| Gate | Required | Approved By |
|------|----------|-------------|
| Phase 0 → Phase 1 | TAD + UX Brief complete | `rajiblabs-po` |
| Phase 1 → Phase 2 | Infrastructure live + CI passing | `rajiblabs-architect` |
| Phase 2 → Phase 3 | QA Go (no Critical/High defects) | `rajiblabs-qa` |
| Phase 3 → Production | Release Approval | `rajiblabs-po` |

---

## Tech Stack Defaults (RajibLabs Platform)

| Layer | Default |
|-------|---------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | .NET 8 ASP.NET Core Minimal API |
| ORM | Entity Framework Core (code-first) |
| Database | Azure SQL Database |
| Hosting | Azure App Service (backend) + Azure Static Web Apps (frontend) |
| Secrets | Azure Key Vault |
| CI/CD | GitHub Actions |
| Monitoring | Azure Application Insights |
| Auth | JWT Bearer / Azure AD B2C |

---

## Security Non-Negotiables (All Agents)

These apply to every project and every agent, always:

1. **No secrets in code** — all secrets via environment variables or Key Vault.
2. **Input validation** — validate all inputs at the API boundary.
3. **Parameterised queries** — never concatenate SQL strings.
4. **HTTPS only** — enforce HTTPS in all environments, including staging.
5. **Dependency scanning** — Dependabot enabled on every repository.
6. **Least privilege** — service principals and managed identities get only required permissions.
7. **No XSS** — sanitise all user-generated content before rendering.
8. **Auth on all endpoints** — every API endpoint is either explicitly public or requires auth.

---

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Azure Resource Group | `rg-<project>-<env>` | `rg-invoicer-prod` |
| Azure App Service | `app-<project>-<env>` | `app-invoicer-prod` |
| GitHub branch | `feature/<ticket>-<short-desc>` | `feature/INV-42-add-payment-reminder` |
| API endpoint | `/api/v1/<resource>` | `/api/v1/invoices` |
| TypeScript type | PascalCase | `InvoiceItem` |
| React component | PascalCase file | `InvoiceCard.tsx` |
| .NET class | PascalCase | `InvoiceService` |
| Database table | PascalCase plural | `Invoices`, `PaymentReminders` |

---

## File Structure (agents/)

```
agents/
├── README.md                  ← This file (master workflow)
├── rajiblabs-po.md            ← Product Owner
├── rajiblabs-architect.md     ← Architect & PM
├── rajiblabs-ux.md            ← UI/UX Designer
├── rajiblabs-dev.md           ← Developer
├── rajiblabs-qa.md            ← QA Validator
├── rajiblabs-devops.md        ← DevOps
├── rajiblabs-monitor.md       ← GitHub Monitor
└── rajiblabs-portfolio.md     ← Portfolio Content
```

---

## Quick Reference: Who to Ask

| Question | Ask |
|----------|-----|
| What should we build? | `rajiblabs-po` |
| How should we build it? | `rajiblabs-architect` |
| What should it look like? | `rajiblabs-ux` |
| Can you write the code? | `rajiblabs-dev` |
| Does it work correctly? | `rajiblabs-qa` |
| How do we deploy it? | `rajiblabs-devops` |
| What's happening in the repo? | `rajiblabs-monitor` |
| Update the portfolio | `rajiblabs-portfolio` |
