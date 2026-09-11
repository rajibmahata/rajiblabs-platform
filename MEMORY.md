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
  (`ai_agents` store), `workbench.py`, `github_service.py`, `translation_*`,
  `resume_text.py` (PDF/DOCX extraction), `resume_projects.py` (resume→projects
  consolidation, Profile Agent owned), `ai_economy.py` (LEVEL 0 structured +
  caches), `skill_intelligence.py`/`domain_intelligence.py` (evidence-backed),
  `learning_agent.py` (mentor daily blocks, RAG-grounded, hash-versioned).
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
   Every async action MUST show a loader + disable its button + toast on
   success/error + refresh UI: `const { run, isLoading } = useAsyncActions()`
   from `components/admin/async`, then
   `run("save", async () => { await api.put(...); load(); },
   { successTitle: "Saved", errorTitle: "Save failed" })` with
   `disabled={isLoading("save")}` and `{isLoading("save") ?
   <InlineLoader text="Saving..." /> : "Save"}`. Loaders come from
   `components/admin/ui` (`InlineLoader`, `BlockLoader`, `StepProgress`,
   `AsyncButton`) + `admin.css` (`rla-inline-loader`, `rla-block-loader`,
   `rla-step-progress`); never invent new colors or per-page spinners.
   Pattern: try → toast success → catch toast error → finally clears loader
   (the hook guarantees the loader never sticks).
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
   Tests hitting `lead_ai._complete` retry logic need the `fake_ai_key` fixture
   (fake `OPENAI_API_KEY` + cache reset) — otherwise they die at the unconfigured gate.
   `tests/conftest.py` seeds-if-empty on a reachable Mongo so live tests are
   deterministic on fresh DBs; never assert on ambient seed content beyond that.
6.    `python3 -m pytest tests/ -q` (~156 tests, must stay green).

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
- **Vector store is a module-level singleton** (`rag_vectors._VS_SINGLETON`) — never
  create `QdrantVectorStore()` directly in hot paths; use `get_vector_store()`.
- `qdrant-client==1.12.1` is pinned in requirements (dashboard goes DOWN without it);
  dev compose runs `qdrant/qdrant:v1.11.3`, prod compose its own internal instance
  (`QDRANT_URL=http://qdrant:6333`, persistent `/opt/rajiblabs/data/qdrant`).
- `github_rag_repos` config is a comma-separated STRING; empty = all tracked public repos.
- `/api/admin/logs/stats` returns `by_level` as an OBJECT `{level: count}`.
- **Batch RAG ingestion**: `rag_ingest.upsert_documents_batch()` embeds + upserts
  multiple documents in one cycle — used by `skill_intelligence.py` for per-skill docs.
  Never call `upsert_document()` in a loop for the same source type; batch instead.
- **Resume knowledge**: `resume_text.extract_and_store()` → `rag_ingest.ingest_resume()`
  (scrubbed, hash-deduped). One doc per file (`resume:file:<id>`) plus
  `resume:approved-public`. `resume_projects.consolidate_resume_projects()` is the
  single owner for resume→projects (all versions, slug-deduped, no invention).

## Cost optimization rules (do not break)

- **LLM is the LAST resort.** Answer hierarchy: Level 0 (MongoDB structured) →
  Level 1 (cache/embedding/Qdrant) → Level 2 (cheap classification) → Level 3 (strong LLM).
- **Level 0 structured answering** (`ai_economy.structured_answer()`) handles: products,
  projects, skills, domains, resume, contact, live URLs, social links, experience,
  certifications, tech stack, portfolio live. Questions matching these patterns go
  straight to MongoDB — no embedding, no RAG, no LLM.
- **AI intent classification is removed.** `classify_intent_ai()` returns "GENERAL" stub.
  All production intents are covered by rule-based classification in `rag_query.py`
  and `concierge.py`. Never re-add AI intent classification.
- **Response cache** is used by both RAG (`ai_economy.response_cache_get/set`) and
  concierge (`concierge.py`). Keyed by question hash + KB version. Stable information
  (skills, products, contact) caches longer. Invalidate via `bump_kb_version()`.
  Concierge also has a **global** `concierge-global` cache (no per-session token) for
  structured answers — next visitor is free.
- **KB version** (`ai_economy.kb_version()`) has a 10-second in-process TTL cache.
  Never call `site_settings.find_one({"key": "kb_version"})` directly in hot paths.
- **gpt-5 token budgets** are tiered: concierge 800, marketing 1400, scope 2000,
  generation 4000. Never request more than needed. `max_completion_tokens` (not `max_tokens`).
- **Concurrent tool execution** in concierge uses `asyncio.gather`. Never run independent
  tools sequentially. `search_knowledge`, `get_projects`, `get_contact_information`
  are independent and must run in parallel.
- **Scheduler staggering**: `profile-agent` at 06:00, `learning-agent` at 06:30 IST.
  Never schedule resource-intensive agents at the same time.
- **AIService._http** is a reusable `httpx.AsyncClient`. Never create a new client per
  `_complete()` call. The client is shared across all providers and retries.
- **Embedding cache**: content-hash keyed in `embedding_cache` collection, TTL
  `rag_cache_ttl_seconds`. Never re-embed unchanged content. `cached_embed()` handles this.
- **Lead chat fast path** (`lead_pipeline.process_chat_message`): Level 0/1
  `response_cache` → `structured_answer` → high-confidence extractive RAG
  (score ≥ `rag_direct_answer_min_score`, factual threshold 0.55) before any
  `AIService.chat_with_lead` call. Simple knowledge queries (`what are your skills`,
  `what projects have you built`) return in ~40 ms with `used_llm=False`.
  Only `hire`/`build`/`idea` lead-intent messages go to the LLM.
- Admin usage dashboard: `GET /api/admin/usage/{today,week,cache-stats,health}` for
  monitoring LLM costs, cache hit rates, and latency.

## Concierge / agents rules (do not break)

- Flow is intent → sanitized tools → ONE small LLM reply (`concierge.py`).
  Pure lookups (greeting/contact/verified live URL/lead follow-ups) never call the LLM;
  provider failure falls back to the deterministic tool-only composer.
  **Fast path:** global `concierge-global` structured cache + `tool_answer_ok`
  for `projects_list`/`github_work`/`products`/`services`/`about_rajib` etc. with
  verified tool output — no LLM when retrieval is sufficient.
- Public tools live ONLY in `agent_tools.PUBLIC_TOOL_NAMES`; `run_public_tool`
  rejects admin-only/unknown names server-side — the LLM never decides authorization.
  Tool outputs are allowlisted + secret-scrubbed; reply URLs are validated against
  tool-returned URLs (others stripped); unknown info → fallback message, never invented.
- **Project details confidential handling** (`frontend/src/pages/ProjectDetail.tsx`):
  missing `live_url` → `Delivered to the customer. The live application URL is confidential.`
  missing `github_url` → `Repository details are confidential / not publicly available.`
  Never imply a private project has a public repo; never leave empty link fields.
- KB policy is central (`kb_policy.py`) and enforced server-side, never by prompt:
  `rag_query.retrieve(consumer=)` drops disallowed/orphan chunks (fail-closed);
  `ai_economy.keyword_search(consumer=)` enforces the SAME contract (parent
  hydration + `filter_hits`, fail-closed) — the keyword fallback must never be
  a guardrail bypass when embeddings are down; `upsert_document` normalizes +
  stores per-doc `guardrails`/`hallucination_control`; concierge validates LLM
  replies deterministically (no-evidence/low-confidence/
  unsupported-claims → fallback or clarify question). Admin edits policies in the
  KB form (`GET /api/admin/rag/guardrail-schema` drives the widgets); policy-only
  saves skip re-indexing.
- Concierge hallucination gate: read policy keys with `.get()` — the
  hallucination dict has `require_evidence`, NOT `require_source` (a direct
  `_pol["require_source"]` raises `KeyError`, gets swallowed by the surrounding
  `except: pass`, and the gate silently stops replacing ungrounded replies).
  Evidence must include `snippet` (`search_knowledge` returns `snippet`, not
  `content`).
- Knowledge guardrails: per-agent `knowledge_policy` in `ai_agents`
  (`{source: {public_allowed, priority}}`, unknown types denied); RAG hits filtered
  server-side in the concierge (shared index, never a second one).
- Lead capture is gradual (one field/turn) and stored ONLY via
  `lead_pipeline.find_or_create_lead` / `upsert_idea`; marketing consent never implied.
- Agent runtime config: `ai_agents` collection (seeded `rajiblabs-concierge`);
  edit via `/api/admin/agents/*`, never via prompt edits.
- Chat turns persist intent/tools/sources/lead/latency/model on `customer_messages`
  (+ `agent_slug`); admin stats aggregate from there.

## Learning Agent rules (do not break)

- Mentor, not textbook: `learning_agent._generate_daily_block` uses a warm, simple-language system prompt. Real-world scenario (e.g. Customer/Product shopping story) comes BEFORE any theory; jargon is introduced only after plain explanation. Short paragraphs (2-3 sentences), no huge walls, no generic AI phrases.
- Practical-first structure every day: `what you will learn` → `why matters` → `real_world_example` → `simple_explanation`/`concept_explanation` → `step_by_step (3-5 actionable)` → `practical_example` → `code example (runnable, beginner-level, complete Main for C#)` + `explanation` + `expected_output` → `try_it_yourself` (one tweak) → `common_mistakes (2-3)` → `exercise (5-10 min)` → `homework (15-20 min)` → `quick_review (3)` → `what_you_can_do_now (2-3)` → `questions (3)` → `next_preview`. Only render when data exists.
- Progressive: agent is given full `roadmap` + last 3 days summary (`prev_blocks_summary`) and `duration`; Day 1 is zero-knowledge, Day N never assumes future knowledge (`Understand → Observe → Follow → Practice → Modify → Solve → Build`).
- RAG-first, LLM-last: `rag_query.retrieve(f"{topic} {day_title}")` top_k 3 grounds the prompt; `content_hash` (`concept+exercise+real_world`) dedupes unchanged lessons; `needs_review`/`published` statuses control re-generation. Unchanged hash → `unchanged` (no LLM).
- Validation is mentor-quality: `_validate_block` checks `real_world_example`, `simple_explanation`, `step_by_step 3-5`, `common_mistakes`, `what_you_can_do_now`, code `Main` for C#, exercise/homework length, generic phrase bans. `_is_weak_block` catches short/generic fallback lessons (e.g. `<200` chars, missing `real_world_example`, generic steps) and forces regeneration on next `run_daily`.
- Admin detail is the source of truth: `GET /api/admin/learning/paths/{slug}/blocks` returns full blocks (all new fields), admin `LearningManage` makes every Day card clickable → `rla-modal` drawer showing complete lesson (objective, real-world, code, try, mistakes, exercise, homework, recap, what-you-can-do, validation, version, hash, generated/validated times). No DB/JSON inspection needed.
- Public `LearningPathDetail` renders the same mentor order with `Markdown` for concept, `rlz-ld-*` sections, progress and roadmap. Public API only serves `published`/`completed` blocks on `active`/`completed` paths.
- Never break: path creation (`Topic+Duration→roadmap→Day 1..N`), day scheduling, `06:30 IST` automation, `learning_paths`/`learning_blocks`/`learning_progress`/`learning_agent_runs` indexes, RAG `learning:*` docs, `/api/learning/*` + `/api/admin/learning/*` auth.

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
- **Resume PDF extraction**: `pypdf` + `python-docx` MUST be in `requirements.txt`
  and the Docker image must be rebuilt (`docker compose build ai-api`). A stale
  image silently returns `extracted_text=""` (no error, just no RAG/projects).
- **Resume versioning**: `file_hash` (SHA256 of raw bytes, 16 hex) dedupes identical
  uploads — same file returns existing doc, no new version or re-embedding.
  Version is `max(version)+1`, not `count+1` (handles deletions).

- `npm install` MUST run from Windows, not WSL: WSL npm prunes win32 native bindings
  (`@rolldown`, `@tailwindcss/oxide`, `lightningcss`) and Windows `vite build` dies with
  "Cannot find native binding". If it happens, `npm pack` the exact lock version of the
  missing `*-win32-x64-msvc` package and extract it under `node_modules/`.
- `localhost:5010` serves the Docker-baked `dist/` — after frontend changes, rebuild the
  image (`run-docker.bat rebuild` / `docker compose up --build`); a local `npm run build`
  alone does not update Docker.
- Production VPS is SHARED with PasteControl: RajibLabs must never use host :80/:443,
  shared networks, or shared volumes (edge is host :8080; DBs on 127.0.0.1 only).
  Never add an `external:` network belonging to another app — `up` fails hard when
  it is absent. Phase-2 domain routing goes through the existing edge proxy to
  `127.0.0.1:8080` loopback (`deploy/nginx/rajiblabs-behind-proxy.conf`).
- `deploy/` is TRACKED (un-ignored on purpose) — CI pulls `deploy-vps.sh` and nginx
  confs from git. Never re-ignore it. All VPS compose commands use `-p rajiblabs`.
- A blank/black admin screen = render crash (no error boundary). Check console first;
  usual cause is an API shape assumption (see by_level above).
- Font Awesome is bundled via npm (`@fortawesome/fontawesome-free` imported in
  `admin.css`) — do NOT re-add CDN links (tracking-prevention warnings, offline breakage).
- Effects must never call setState synchronously (`react-hooks/set-state-in-effect`
  fails CI lint): reset pagination/filters in event handlers with a single debounced
  load effect; mount-only fetches carry an explicit disable comment. Progress timers
  stop via explicit `stop()` in request `finally`, never in an effect.
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
  Resume: `POST /api/admin/resumes/upload` (multipart, `file_hash` dedup, versioned, single published) + `POST /api/admin/resume` (compat), `GET /api/admin/resumes`, `PATCH /api/admin/resumes/{id}` (publish), `DELETE`, `POST .../extract`, `GET /api/resume/current`, `GET /api/public/resume/download`.
- Admin i18n: `/api/admin/languages` (+`/{code}`, `/{code}/status`, DELETE guarded), `/api/admin/translations` (+`/generate`, `/coverage`, `/{id}` edit/approve/regenerate/delete).
- Admin RAG: `/api/admin/rag/{dashboard,documents,github-sources,reindex,evaluate}`.
- Admin agents: `/api/admin/agents` (CRUD), `/{slug}` (get/put), `/{slug}/{test,stats,conversations}`.
- Admin usage: `/api/admin/usage/{today,week,cache-stats,health}` (cost/latency/cache monitoring).
- Admin GitHub: `/api/admin/github/{config,test,status,sync}`, `/repositories` (+`/{id}` PATCH/sync/knowledge/reindex/disable/delete-knowledge, `/map`).
- Workbench: `/api/admin/ai/proposal/{analyze,generate,refine,save}`, `/proposal/{id}`
  (GET/PUT/DELETE), `/proposal/{id}/duplicate`, `/proposals`, `/ai/chat`.
- Career: `/api/admin/career/{companies,contacts,jobs,applications}` (+`/{id}` CRUD),
  `/jobs/{id}/{analyze,generate}`, `/applications/{id}/{refine,approve,send,status}`.
  Email sends ONLY approved apps via `email_service` (stdlib SMTP); duplicate sends
  refused without `resend:true`; sent apps are history-immutable.
- CMS/admin: `/api/admin/{dashboard,projects,products,portfolio,resume,profile,content,leads,notifications,logs,github/*}`.
- Collections: `projects`, `products`, `profiles`, `customer_leads`, `customer_conversations`,
  `customer_messages`, `ideas`, `knowledge_documents`, `knowledge_chunks`,
  `proposal_documents`, `proposal_sessions`, `github_repositories`, `notifications`,
  `career_companies`, `career_contacts`, `career_jobs`, `career_applications`,
  `error_logs` (7-day TTL + daily-agent sweep), `audit_logs`, `ai_agents` (seeded concierge),
  `site_settings` (`github` token doc — write-only API, never returned),
  `languages` (seeded, unique `code`),
  `translations` (unique key+target), `translation_cache` (unique hash+target),
  `embedding_cache` (content-hash+provider+model, TTL), `response_cache` (question-hash+kb_version, TTL),
  `ai_usage` (LLM/embedding call records for cost dashboard).

## Verify before finishing any task

- Backend: `python3 -m pytest tests/ -q` from `rajiblabs-ai-backend/` (~156 tests).
- Frontend: `npx tsc --noEmit`, `npx eslint src/pages/admin/ src/components/admin/`,
  `npm run build` from `frontend/`.
- Update this file + `CHANGELOG.md` with what was actually done.

- Catalog split-brain (do not reintroduce): THREE content stores exist —
  legacy `portfolio` (4 .NET-parity imports), current CMS `projects` (5 items,
  `category` product|project), legacy `products` (page-flow, docuflow). Detail
  endpoints `/api/portfolio|products/{slug}` fall back to published `projects`
  rows so no valid slug 404s; guarded by
  `test_detail_falls_back_to_projects_collection`. Admin CRUD stays per-store.

- Concierge voice rules (do not regress): `RESPONSE_GUIDANCE` is code-appended
  to every LLM system message (admin prompt stays editable); `gpt-5-nano`
  REQUIRES the literal word "json" somewhere in messages when using
  `response_format: json_object` (HTTP 400 otherwise — diagnosed live via the
  classified error log); new intents `recruiter/career/technical/
  idea_discovery/general_conversation` are rule-ordered (career+technical sit
  before products/about_rajib; general is last); `what is <Name>?` needs the
  lowercase-tolerant rule because matching runs on lowercased text; social
  acks (thanks/bye) short-circuit with zero LLM cost; fresh-idea turns lead
  with ONE discovery question, never a contact ask.
- Homepage agent section is `rlz/RlzAgent.tsx` (between Experience and
  Contact); starter clicks dispatch `OPEN_CHAT_EVENT` with `{detail: message}`
  which `ChatWidget` auto-sends via a `sendTextRef` (stale-closure safe).
  Chat starters hide after the first user message; project/product sources
  render as rich cards (`desc`/`tech` ride the source objects); mobile chat
  is near-full-screen (`86dvh`).

## QA audit 2026-09-08 (full-stack, live Docker) — known gaps, do not regress

- P0 (fixed): `lead_ai._complete` posted to `{base}/chat/completions` without
  `/v1` → every live AI call 404'd. Only hand-rolled URL in the codebase;
  guarded by `test_29_chat_url_has_v1_prefix`. Rebuild/redeploy backend to apply.
- P1 (fixed): `email_unique` partial index used illegal `$ne` (fails on ALL
  MongoDB versions) → replaced with `{"email": {"$gt": ""}}`, verified created.
- Dead frontend code (DELETED 2026-09-08 after verifying zero live importers,
  no dynamic imports anywhere): `components/sections/*` (13),
  `components/projects/*`, `components/activity/*`, `components/ui/
  {FloatingContact,ProjectCard,ProjectModal,SectionLabel,StatusBadge,TechChip,
  CommitRow}`, `components/layout/{GlobalNav,GlobalFooter}`,
  `pages/Projects.tsx` (had no route), `services/fallbackData.ts` + legacy
  `api.ts` fetchers. `types/index.ts` KEPT (live `api.ts`/admin use it). Home
  renders `rlz/*` exclusively.
- Admin pages are route-split (`React.lazy` in `App.tsx`); main bundle ~352K.
  New admin pages must be added as lazy imports, not eager.
- SEO baseline: static JSON-LD + OG/Twitter + canonical in `index.html`;
  dynamic `GET /sitemap.xml` (backend lists published slugs, static fallback);
  nginx proxies `= /sitemap.xml` with `@sitemap_static` fallback. Detail pages
  set per-route title/meta/OG/canonical in `ProjectDetail`.
- RAG live tests must mock `app.services.ai_economy.cached_embed` (fake vector),
  not just `rq.EmbeddingService`: `retrieve()` resolves embeddings via
  `cached_embed`, so without that mock the test hits real embeddings and — with
  no OpenAI key — silently falls back to keyword search, ignoring the mocked
  vector store (caused `test_public_consumer...`, github URL + orphan failures).
- Mocks of `AIService._complete` must accept `**kwargs`: `chat_with_lead` /
  concierge pass `db=`/`reason=` (caused
  `test_chat_reply_localized_same_knowledge` TypeError).
- Learning visibility: public serves ONLY `learning_agent.VISIBLE_PATH_STATUSES`
  (`active/completed/live/published`) and `VISIBLE_BLOCK_STATUSES`
  (`published/completed`). Admin PATCH normalizes `live`/`published`/`draft`
  via `normalize_path_status()` — never add a second status vocabulary or a
  parallel learning index. Draft/paused/archived paths AND unpublished blocks
  404 publicly (slug knowledge must not leak them).
- Project Intelligence (single owner: `resume_projects.consolidate_resume_projects`,
  run by the Profile Agent + on every resume extraction): dedupes across ALL
  resume versions by slug, merges tech/descriptions, NEVER overwrites
  `locked_fields`, NEVER invents URLs (github only from stored non-private
  repos, live never invented). Evidence (`resume|github|portfolio` entries) is
  append-only. Portfolio scoring is deterministic (`_portfolio_score`,
  threshold from `site_settings.portfolio_criteria`, default 50); auto-draft
  is opt-in and creates DRAFTs only. New `projects` fields (`role`,
  `learnings`, `beneficiaries`, `domain`, `evidence`, `portfolio_score`,
  `portfolio_worthy`) render conditionally on the detail page — empty means
  hidden, never placeholder text.
- Resume pipeline triggers (all best-effort in `extract_and_store`): RAG
  ingest + project consolidation + `sync_skills` — skills must refresh on
  upload, not just on the 06:00 agent run. `ingest_resume` indexes the active
  resume publicly AND history resumes admin-only (`resume:history:<id>`,
  `public_access: False`), plus an orphan sweep for deleted resumes. Empty
  extraction on the ACTIVE resume fires an admin-visible `log_error`.
- NEVER fan out unconditionally from extraction: `extract_and_store` runs
  downstream only when text was produced or changed, and consolidation
  re-extracts only rows without `extracted_at`. Otherwise empty extractions
  form an extract→consolidate→extract infinite loop (pinned CPU, hung
  `test_resume.py`). Empty cache `[]` is valid cache — never LLM-repeat it.
- Tests share the dev MongoDB (no isolation): `test_resume.py` uploads archive
  the real published resume, so its autouse `_resume_isolation` fixture
  snapshots/restores published state and deletes created rows. Never assume a
  scratch DB — any upload-touching test needs the same guard.
- Lead-chat tests use per-run phones (`PHONE_A`/`PHONE_B` from `TAG_NUM`);
  never hardcode phone numbers in tests (phone-second dedup merges across runs).
- Lead-chat tests are order/state-sensitive: hardcoded phones (`9876543210`,
  `9111111111`) collide across runs via phone-second dedup; run on a clean DB
  or expect `test_08/09`-style false failures. Full suite is too slow for one
  shot (~110s+ on live DB) — run per-file chunks.
- SEO gaps (open): no JSON-LD anywhere; `sitemap.xml` lists only 3 URLs (no
  project/product detail URLs); OG tags only set dynamically in `ProjectDetail`;
  no canonical tags; no per-route meta beyond index.html.
- Rate limits are in-memory per-process (`chat.py`/`lead_chat.py` `_limit`) —
  correct for single-container VPS, lost on restart, not shared across replicas.
- `bn` translations `count: 0` — no data yet, fallback-to-English path verified
  correct; generate via admin Translations page when ready.
- `RlzMarquee` uses `innerHTML += innerHTML` self-duplication (benign — own
  static nodes, StrictMode-guarded) — leave unless rewritten.
- `data/uploads/` (repo root) is an empty leftover; backend uses
  `rajiblabs-ai-backend/data/uploads/`. `app/static/` + `app/templates/` are
  empty dirs. `scripts/sync_linkedin_learning.py` is cron-style manual, unwired
  to any scheduler.
