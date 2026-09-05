# RajibLabs Platform — Project Memory

Durable context for future work. Read this before implementing any new page or feature.
Stack is locked: React + TypeScript + Vite + Tailwind (`frontend/`), FastAPI + Python
(`rajiblabs-ai-backend/`), MongoDB. No .NET / SQL Server / microservices.

## Repo layout

- `frontend/src/pages/admin/` — 15 pages: AgentsManage, ContentManage, Dashboard,
  GitHubManage, KnowledgeManage, LanguagesManage, LeadsManage, LogsManage,
  PortfolioManage, ProductsManage, ProfileManage, ResumeManage, Settings,
  TranslationsManage, Workbench (AI Proposal Studio), + Login.
- `frontend/src/components/admin/` — `AdminLayout.tsx` (shell + NAV groups), `ui.tsx`
  (template primitives), `toast.ts` (toast bus), `ProtectedRoute.tsx`.
- `frontend/src/styles/admin.css` — entire admin design system, scoped under `.rl-admin`.
- `frontend/src/services/api.ts` — `api.{get,post,put,patch,del,upload}` (cookies included),
  plus `sendChat/sendAgentChat/getAgentCard` for the homepage widget.
- `frontend/src/components/ChatWidget.tsx` — homepage concierge chat (ask→agent
  endpoint, plan→pipeline; starters from `/api/public/agent/config`).
- `rajiblabs-ai-backend/app/routers/` — `admin_*` (JWT: auth, projects, logs, rag,
  workbench, languages, agents), `public.py`, `chat.py`, `lead_chat.py`,
  `rag.py` (public RAG), `legacy.py` (v1 compat), `github.py` (token config +
  knowledge-sync lifecycle), `concierge.py` (public agent chat).
- `rajiblabs-ai-backend/app/services/` — `lead_ai.AIService` (THE orchestrator),
  `rag_query.retrieve` (THE retrieval entry), `agent_tools.py` (THE public tool
  registry), `concierge.py` (intent→tools→reply loop), `agent_config.py`
  (`ai_agents` store), `workbench.py`, `github_service.py`, `translation_*`.
- `rajiblabs-ai-backend/tests/` — `test_api.py`, `test_lead_chat.py`, `test_rag.py`,
  `test_workbench.py`, `test_concierge.py`, `test_github_knowledge.py`, `test_kb_policy.py`,
  `test_i18n.py` (~199 collected). HTTP mocks via `respx` (in requirements; install if missing).

## Adding a new admin page (copy this recipe)

1. Create `frontend/src/pages/admin/XxxManage.tsx` using ONLY template primitives:
   `PageHead({title, desc, actions})`, `Panel({title, sub, action})`, `StatusPill`,
   `Chip`, `Field`, `Empty` from `../../components/admin/ui`, plus CSS classes
   `rla-form-grid`, `rla-input`, `rla-textarea`, `rla-select`, `rla-chip-row`,
   `rla-list-card`, `rla-table`, `rla-btn rla-btn-primary|ghost rla-btn-sm`,
   `rla-mini-btn`, `rla-code`, `rla-search-input`, `rla-section-title`.
   Never invent new colors — use `var(--rla-*)` tokens.
2. Guard every list fetch: `.then((l) => setX(Array.isArray(l) ? l : []))`.
3. Feedback via `toast(title, msg)` from `components/admin/toast` (no bare `alert` in new code).
4. Route in `frontend/src/App.tsx` inside the admin layout block; nav entry in
   `AdminLayout.tsx` NAV groups (pick icon from Font Awesome free set, already bundled).
5. `npx tsc --noEmit && npx eslint src/pages/admin/ && npm run build`.
6. Grid pages: copy `LogsManage.tsx` (search/filter/pagination/sort + details modal
   + `rla-table`/`rla-pager`/`rla-modal` CSS); test consoles: copy `AgentsManage.tsx`.

## Adding a backend admin endpoint (copy this recipe)

1. Schema in `rajiblabs-ai-backend/app/schemas/__init__.py` (Pydantic, validated).
2. Router file with `prefix="/api/admin/..."`; EVERY route takes
   `email: str = Depends(require_admin)`; audit writes via `services.notify.audit`
   with explicit `event_type=`; serialize with `models.oid_str`.
3. AI calls go through `lead_ai.AIService()._complete(...)` ONLY — never call
   OpenAI/DeepSeek from routers. RAG reads go through `rag_query.retrieve(...)` ONLY.
4. New collections need indexes in `app/database.py::ensure_indexes`.
5. Register router in `app/main.py` router list + `openapi_tags`. Add tests in `tests/`
   following the fake-at-boundary pattern (monkeypatch `AIService` / `rag_query.retrieve`;
   `respx` for GitHub HTTP; live-Mongo tests must skip gracefully when DB is down).
6. `python3 -m pytest tests/ -q` (~199 tests, must stay green).

## Secrets (non-negotiable)

- `.env.example`, `.env.production`, `deploy/dotenv.production.example` contain
  placeholders ONLY (empty values). Never commit real `SECRET_KEY`/`JWT_SECRET`/
  `API_KEY`/`ADMIN_INITIAL_PASSWORD`/tokens — a committed value must be treated as
  burned: rotate it in `/opt/rajiblabs/config/.env` + GitHub Secrets immediately
  (rotation just forces admin re-login, nothing else breaks).
- Production reads secrets from `/opt/rajiblabs/config/.env` (0600, never committed);
  CI syncs non-empty GitHub Secrets over it each VPS deploy.

## RAG rules (do not break)

- One shared knowledge base (`knowledge_documents` + `knowledge_chunks` + Qdrant).
  Never create a second index. Public chat and workbench only differ in prompting.
- Only public/approved content is indexed; GitHub sync skips secrets/binaries
  (`SKIP_FILENAMES` / `SKIP_EXTENSIONS` in `github_service.py`).
- Chunk hydration is via `payload.mongo_chunk_id` (Qdrant point IDs are UUIDv5).
- `EmbeddingService.descriptor()` keys: `embedding_provider/model/version/dim`.
- Vector store health is `get_vector_store().health_check()` (no `collection_info`).
- `qdrant-client==1.12.1` is pinned in requirements (dashboard goes DOWN without it);
  dev compose runs `qdrant/qdrant:v1.11.3`, prod compose its own internal instance
  (`QDRANT_URL=http://qdrant:6333`, persistent `/opt/rajiblabs/data/qdrant`).
- `github_rag_repos` config is a comma-separated STRING; empty = all tracked public repos.
- `/api/admin/logs/stats` returns `by_level` as an OBJECT `{level: count}`.

## Concierge / agents rules (do not break)

- Flow is intent → sanitized tools → ONE small LLM reply (`concierge.py`).
  Pure lookups (greeting/contact/verified live URL/lead follow-ups) never call the LLM;
  provider failure falls back to the deterministic tool-only composer.
- Public tools live ONLY in `agent_tools.PUBLIC_TOOL_NAMES`; `run_public_tool`
  rejects admin-only/unknown names server-side — the LLM never decides authorization.
  Tool outputs are allowlisted + secret-scrubbed; reply URLs are validated against
  tool-returned URLs (others stripped); unknown info → fallback message, never invented.
- KB policy is central (`kb_policy.py`) and enforced server-side, never by prompt:
  `rag_query.retrieve(consumer=)` drops disallowed/orphan chunks (fail-closed);
  `upsert_document` normalizes + stores per-doc `guardrails`/`hallucination_control`;
  concierge validates LLM replies deterministically (no-evidence/low-confidence/
  unsupported-claims → fallback or clarify question). Admin edits policies in the
  KB form (`GET /api/admin/rag/guardrail-schema` drives the widgets); policy-only
  saves skip re-indexing.
- Knowledge guardrails: per-agent `knowledge_policy` in `ai_agents`
  (`{source: {public_allowed, priority}}`, unknown types denied); RAG hits filtered
  server-side in the concierge (shared index, never a second one).
- Lead capture is gradual (one field/turn) and stored ONLY via
  `lead_pipeline.find_or_create_lead` / `upsert_idea`; marketing consent never implied.
- Agent runtime config: `ai_agents` collection (seeded `rajiblabs-concierge`);
  edit via `/api/admin/agents/*`, never via prompt edits.
- Chat turns persist intent/tools/sources/lead/latency/model on `customer_messages`
  (+ `agent_slug`); admin stats aggregate from there.

## AI orchestrator failure behavior (do not break)

- `AIService._complete` classifies every failure: `HTTP_{status}`, `NonJsonBody`,
  `EmptyContent` (+finish_reason), `Refusal`, `BadJson`, network errors — recorded as
  `provider: Cause` strings plus a scrubbed raw snippet in `error_logs`
  (source `ai_provider`). Never collapse back to bare exception type names.
- Prose-wrapped JSON is repaired via `_extract_json_object` (balanced-brace scan);
  Pydantic validation downstream still rejects garbage. Unit-tested in
  `test_lead_chat.py` 23–27 with attempt counts (refusal/401 = 1 attempt, not 3).
- Retry rule: deterministic (refusal, 400/401/403/404) breaks early; transient
  (429/5xx/network/empty/bad-JSON) uses backoff. Final contract stays
  `AIError("All AI providers failed")`; visitor fallback unchanged.
- Diagnosing "All AI providers failed": `HTTP_401` = wrong key; `HTTP_404` = model
  name the key can't access (auto-retries once with `openai_fallback_model`,
  default `gpt-4o-mini`; details list `models tried:`); `Refusal` = that exact
  visitor message refused (reproducible); `EmptyContent` = model returned nothing
  (check model support for `response_format`/`temperature`); `JSONDecodeError` in OLD
  logs = any of the above (pre-classification era).
- `openai_fallback_model` (default `gpt-5.6-luna` — REAL, GPT-5.6 cheap tier; verified
  2026-09-05 after a false alarm claiming otherwise) is auto-tried once on HTTP_404;
  test_28 guards the path with the fallback read from settings, never hardcoded.

## Multilingual framework (do not break)

- One shared RAG index for ALL languages — retrieval stays English, only the final
  response is localized (`lang_service.response_instruction`). Never build per-language indexes.
- Cost rule: approved record → `translation_cache` → valid generated → English source
  (+ `fill_background` fire-and-forget) → LLM only when explicitly asked. Prove with
  `TranslationAgent.calls` in tests.
- `translations` key format: `{collection}.{ref}.{field}` (`body` dicts flatten to
  dotted leaves); technical leaves (slug/URL/email/github/...) are never translated
  (`SKIP_LEAF_KEYS`, `_leaf_ok`). Translatable fields registry: `TRANSLATABLE` in
  `translation_service.py`.
- Language master: `languages` collection, `en` default (never disable/delete),
  delete only when zero records reference the code. `enabled_languages()` has a 60s
  process cache — admin writes call `invalidate_cache()`.
- Public content endpoints take `?lang=` (absent/English = passthrough, no extra cost).
- Frontend L1 bundles live in `src/i18n/*.json` (flat keys, arrays for lists) with
  key-parity across all 12; `useLang()` from `i18n/langContext` (`t`/`tArr` fall back
  to English per key); persistence key `rlabs_lang` (localStorage + cookie); browser
  detection ONLY with no saved preference; `<html lang/dir>` synced (ar = RTL).
- Chat language flows as `language` field (lead chat, RAG query, concierge agent,
  workbench generate/chat) and is echoed back in responses.
- Test fakes need `_id` on fake Mongo docs (`{**d, "_id": ...}` in service code).

## Gotchas (learned the hard way)

- Motor/pymongo `Database`/`Collection` objects raise on truthiness: NEVER write
  `db = db or get_db()` — always `db = get_db() if db is None else db`. This has
  bitten `ensure_indexes`, `purge_old_logs`, and `agent_config.ensure_seed`.
- `respx` is a test dependency (requirements.txt) but may not be installed in the
  environment — `pip install --break-system-packages respx` if collection errors
  with `ModuleNotFoundError: No module named 'respx'`.

- `npm install` MUST run from Windows, not WSL: WSL npm prunes win32 native bindings
  (`@rolldown`, `@tailwindcss/oxide`, `lightningcss`) and Windows `vite build` dies with
  "Cannot find native binding". If it happens, `npm pack` the exact lock version of the
  missing `*-win32-x64-msvc` package and extract it under `node_modules/`.
- `localhost:5010` serves the Docker-baked `dist/` — after frontend changes, rebuild the
  image (`run-docker.bat rebuild` / `docker compose up --build`); a local `npm run build`
  alone does not update Docker.
- A blank/black admin screen = render crash (no error boundary). Check console first;
  usual cause is an API shape assumption (see by_level above).
- Font Awesome is bundled via npm (`@fortawesome/fontawesome-free` imported in
  `admin.css`) — do NOT re-add CDN links (tracking-prevention warnings, offline breakage).
- Workbench `_overlap_terms` needs boundary-aware matching for short tech tokens
  (`.NET`, `AI`, `AWS`); plain word-set overlap silently drops them.
- Workbench `generate_artifacts` MUST NOT reference undefined names in the brief
  path (a missing `LENGTH_GUIDANCE` once 500'd every Generate) — the deterministic
  full-flow test in `test_workbench.py` guards this.
- Proposal Studio modes: `project_explanation` is deterministic (no LLM); context
  rules live in `CONTEXT_RULES` + quality flags; analyze→generate→refine share
  `session_id`; generate returns `stages`/`total_ms` for the progress UI.
- Proposal Studio URLs: only from `collect_known_urls` allowlist; AI-invented URLs are
  scrubbed (`_scrub_urls`). Match score is an "AI relevance estimate", never a probability.

## Key endpoints & collections

- Public: `/api/public/chat` (+`mode:"rag"` → intent/sources, +`language`), `/api/rag/query` (+`language`), `/api/rag/health`, `/api/public/languages`, `/api/public/translations/{lang}`, `/api/public/translate`, `/api/public/agent/{config,chat}`; content endpoints accept `?lang=`.
- Admin i18n: `/api/admin/languages` (+`/{code}`, `/{code}/status`, DELETE guarded), `/api/admin/translations` (+`/generate`, `/coverage`, `/{id}` edit/approve/regenerate/delete).
- Admin RAG: `/api/admin/rag/{dashboard,documents,github-sources,reindex,evaluate}`.
- Admin agents: `/api/admin/agents` (CRUD), `/{slug}` (get/put), `/{slug}/{test,stats,conversations}`.
- Admin GitHub: `/api/admin/github/{config,test,status,sync}`, `/repositories` (+`/{id}` PATCH/sync/knowledge/reindex/disable/delete-knowledge, `/map`).
- Workbench: `/api/admin/ai/proposal/{analyze,generate,refine,save}`, `/proposal/{id}`
  (GET/PUT/DELETE), `/proposal/{id}/duplicate`, `/proposals`, `/ai/chat`.
- CMS/admin: `/api/admin/{dashboard,projects,products,portfolio,resume,profile,content,leads,notifications,logs,github/*}`.
- Collections: `projects`, `products`, `profiles`, `customer_leads`, `customer_conversations`,
  `customer_messages`, `ideas`, `knowledge_documents`, `knowledge_chunks`,
  `proposal_documents`, `proposal_sessions`, `github_repositories`, `notifications`,
  `error_logs` (7-day TTL + daily-agent sweep), `audit_logs`, `ai_agents` (seeded concierge),
  `site_settings` (`github` token doc — write-only API, never returned),
  `languages` (seeded, unique `code`),
  `translations` (unique key+target), `translation_cache` (unique hash+target).

## Verify before finishing any task

- Backend: `python3 -m pytest tests/ -q` from `rajiblabs-ai-backend/`.
- Frontend: `npx tsc --noEmit`, `npx eslint src/pages/admin/ src/components/admin/`,
  `npm run build` from `frontend/`.
- Update this file + `CHANGELOG.md` with what was actually done.
