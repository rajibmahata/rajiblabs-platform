# Changelog

All notable changes to the RajibLabs platform. Dates in UTC.

## [Unreleased] — Fix CI suite: seed fixture + fake provider key (7 failures)

### Fixed (root causes, not symptoms)
- `/api/profile` 404 + empty-profile tools on fresh DBs: live tests assumed a
  seeded database but nothing seeds it (ASGI transport skips lifespan). New
  session `tests/conftest.py` runs seed-if-empty `init_db()` when Mongo is
  reachable (never wipes; no-op when down, existing skip-guards unchanged).
- 5× `lead_ai` retry/repair tests died at the `AI not configured` gate: they mock
  HTTP but never opened the config gate. New `fake_ai_key` fixture (fake
  `OPENAI_API_KEY` + `lru_cache` reset, torn down after) wired into exactly those
  5 tests — no network happens, other unconfigured-behavior tests untouched.
- Verified: full suite **208 passed**, including the 7 previously failing.

## [Unreleased] — Transfer-based VPS deploy (no git on server)

### Changed
- `deploy-vps.yml` rebuilt: `build-frontend` (npm ci/lint/tsc/build, Node 20) +
  `test-backend` (pytest on 3.12 + mongo service) gate `deploy-vps`; the deploy job
  ships the exact commit via `git archive` tarball → `releases/<sha>/` → validate →
  `rsync --delete` → `app/` → secrets → `deploy-vps.sh` → prune (fixed: keeps newest
  2 SHA pairs, `uniq`-free dedupe verified by test). No `.git`, no secrets in transit.
- `deploy-vps.sh`: rollback reference uses `DEPLOY_SHA` (no git assumption).
- New `deploy/rollback-vps.sh [<sha>]`: re-syncs a kept release + `.release`, reruns
  the full deploy (build/health/smoke). Validated: YAML parses, both scripts `sh -n`
  clean, prune + rollback-pick logic tested locally.

## [Unreleased] — VPS checkout bootstrap (fix `not a git repository` CI failure)

### Fixed
- `deploy-vps.yml` failed at `git pull` when `/opt/rajiblabs/app` wasn't a checkout.
  The SSH block now inspects first: lists the dir, detects nested `.git` below it,
  refuses (no deletions) on non-empty non-repo content, clones `main` only into a
  missing/empty dir, then verifies toplevel + `main` branch + `rajiblabs-platform`
  remote + `deploy/deploy-vps.sh` presence before pulling. Logic tested for all four
  cases locally. PasteControl untouched (RajibLabs paths only).

## [Unreleased] — Full Products + Portfolio CMS

### Added — backend (`legacy.py`, `main.py`, `database.py`, `rag_ingest.py`)
- Extended portfolio/product models: tags, featured image + gallery, video URL
  (validated YouTube/Vimeo → safe `videoEmbedUrl`), live/docs/CTA URLs, SEO
  title/description/image, `ragIndexed` flag. Public shapes unchanged + new fields.
- Admin lists now support search (title/descriptions/tags/tech, regex-escaped),
  status/category/featured/tech/tag filters, sorting, pagination envelope.
- New `PATCH .../status` + `PATCH .../featured` toggles (publish = active;
  drafts/hidden never served publicly); deletes remove knowledge vectors.
- Image uploads (`POST /api/admin/uploads/image?kind=`, 5MB, magic-byte check,
  uuid filenames) + delete; served via `/uploads` static mount (Starlette
  traversal-safe; uuid names unguessable). Fixed the same latent
  `isinstance(UploadFile)` version-skew bug in resume upload (was 400ing).
- RAG lifecycle: publish+approved → upsert (`portfolio:`/`product:` source ids,
  verified URLs, tech/tags); unpublish/opt-out → deactivate; delete → vectors
  removed; content-hash dedup avoids needless re-embedding. `ingest_mongodb`
  now covers both collections, so bulk re-ingest stays in one pipeline.
- Indexes for status/featured/display_order/updated_at on both collections.

### Added — admin UI (shared `CatalogManager`, same template)
- Grids with search, status/category/featured/tech/tag filters, sorting,
  pagination, active + featured inline toggles, view/edit/delete.
- Sectioned form (Basic/Description/Media/Tech&Tags/Links/Publishing/SEO) with
  validation errors, image upload + preview + gallery, Save/Save&Continue/Cancel/
  Preview/Delete; Markdown description editor + safe `Markdown` renderer.
- Public detail pages render gallery, tags, video, live/GitHub/docs/CTA links,
  SEO title; empty fields hidden; responsive as before.

### Tests — full suite 208 passed
- New `tests/test_catalog.py` (9): video providers/rejections, query builder,
  auth gates, portfolio + products CRUD/filter/toggle round-trips, upload
  validation, RAG upsert/deactivate/opt-out lifecycle.

## [Unreleased] — Fix CI lint failures blocking frontend build

### Fixed
- `npm run lint` (CI `build` job gate) failed with 3 `react-hooks/set-state-in-effect`
  errors in `AgentsManage.tsx` / `LogsManage.tsx` — same defect class as the earlier
  Workbench fix. LogsManage restructured (pagination resets in event handlers, single
  debounced load effect); AgentsManage mount-fetch carries an explicit disable comment.
- Verified: `npm run lint` exit 0, `tsc` + `vite build` clean, backend 199 passed.

## [Unreleased] — Fix homepage neural canvas (full-page, not hero-only)

### Fixed
- `rlz-neural-canvas` was rendered inside `RlzHero` as an `absolute` hero-only
  layer — invisible on the rest of the homepage. Moved to a dedicated
  `RlzNeuralCanvas` fixed component (`position:fixed; inset:0; z-index:-1;
  opacity:.85`) covering the entire viewport, with DPR-aware resize, mouse
  attraction (180px), inter-particle links (120px), page-visibility pause,
  and `prefers-reduced-motion` support — matching the vanilla design spec.
  Homepage layers now: page-bg `#f7f8fc` (-4) → grid (-3) → orbs (-2) →
  canvas (-1) → content. `RlzHero` no longer owns a canvas; its `useNeuralCanvas`
  hook removed. Verified: `tsc` + `vite build` clean, canvas visible across
  all homepage sections.

## [Unreleased] — Production deployment: PasteControl coexistence + deploy hardening

### Fixed (deployment blockers found by inspection)
- Reported frontend Docker failure (`RUN npm run build`, exit 2) root-caused to TS6133
  (`anyBusy`) — already fixed in 8e3389b. Re-verified at HEAD: `tsc` + `vite build`
  clean, lock in sync, imports case-exact, `.dockerignore` correct.
- `docker-compose.production.yml` required external `pestflow-internal` network, which
  does not exist on the PasteControl VPS → `up` would have failed before starting
  anything. Removed the external network; gateway is `rajiblabs-internal`-only.
- `deploy/deploy-vps.sh` hard-failed without that network. Replaced with a
  `:80/:443`-ownership sanity check (warn-only) plus the existing `:8080` clash guard.
- `deploy/` was gitignored, so CI `git pull` could never deliver `deploy-vps.sh`,
  `gateway.conf`, or the Phase-2 snippet to the VPS. Removed the `deploy/` ignore
  rule (dir holds exactly 4 secret-free files, verified) — must be committed+pushed.
- All compose invocations in `deploy-vps.sh` now pass explicit `-p rajiblabs`
  (in addition to `name:` in the file); added `curl` preflight and a rollback
  reference (git SHA + image IDs printed before every build).

### Changed
- All PestFlow coexistence assumptions replaced with PasteControl-agnostic ones:
  compose/gateway comments, deploy script + workflow headers.
- `deploy/nginx/rajiblabs-behind-pestflow.conf` replaced by
  `deploy/nginx/rajiblabs-behind-proxy.conf` — generic Phase-2 server blocks proxying
  to `127.0.0.1:8080` loopback (no shared Docker network needed), with discovery
  steps for host-vs-container edge, certbot guidance, and test-before-reload safety.

### Verified (repo-side; VPS SSH not available from this environment)
- Production + dev compose YAML parse: only `:8080` + localhost mongo published in
  prod, no external networks, healthchecks + persistent binds intact.
- `deploy-vps.sh`: `sh -n` clean. Workflows YAML-valid.
- nginx static check: braces balanced, upstreams match compose service names.
- Backend: 199 passed. Frontend: `npm run build` clean.

## [Unreleased] — Fix frontend build (Workbench lint/type errors)

### Fixed
- `npm run build` was failing: unused `anyBusy` flag tripped `tsc noUnusedLocals`,
  and the progress hook set state inside an effect (`react-hooks/set-state-in-effect`).
  Progress timer now stops via an explicit `stop()` in request `finally` blocks.
  Verified: `tsc`, `eslint`, and `npm run build` all clean.

## [Unreleased] — Docs/config audit: RAG vars documented, committed secrets sanitized

### Security — ACTION REQUIRED
- `.env.example` and `.env.production` contained real-looking `SECRET_KEY`/
  `JWT_SECRET`/`API_KEY` (one shared UUID) plus `ADMIN_INITIAL_PASSWORD=Test@1234`,
  all committed to git. Replaced with empty placeholders. **Rotate these values in
  `/opt/rajiblabs/config/.env` + GitHub Secrets** — treat the committed ones as
  burned (rotation only forces admin re-login).

### Changed
- New `docs/configuration.md §5b`: all 16 RAG/Qdrant/embedding vars documented
  (were missing despite existing in code).
- Same 16 vars added to `.env.example`, `.env.production`,
  `deploy/dotenv.production.example`; `OPENAI_FALLBACK_MODEL` aligned to config
  default (`gpt-5.6-luna`) in both templates.
- `MEMORY.md`: test inventory (8 files, ~199 tests), Secrets section (placeholders
  only, rotation procedure); `README.md`: Qdrant in deploy topology.
- Verified: 199 passed, `tsc` clean (previous turn).

## [Unreleased] — Proposal Studio reliability fix + workspace redesign

### Fixed (reliability root cause)
- `generate_artifacts` referenced undefined `LENGTH_GUIDANCE` → every Generate raised
  `NameError` (500). Defined the length table; Generate works with or without AI.

### Added — backend (`workbench.py`, schemas, `admin_workbench.py`)
- `project_explanation` mode (guidance + deterministic evidence-assembled explanation
  artifact, no extra LLM call); `CONTEXT_RULES` per mode (job hides freelance talk,
  freelance/client hide corporate internals) enforced in prompts + new quality flags
  (`freelance_leak_in_job`, `corporate_leak_in_freelance`).
- Optional `company`/`instructions` on analyze/generate; `session_id` continuity
  across analyze→generate→refine (was always-new sessions); per-stage server timings
  (`stages` + `total_ms`, `elapsed_ms` on analyze); per-example `selection_reason`
  surfaced as source reasons; `explanation` artifact stored + refinable.
- `ProposalSaveIn.explanation`; refine target `explanation` supported.

### Added — UI (`Workbench.tsx`)
- 3-column workspace: input (+mode/company/instructions) / analysis (+match details,
  gaps, GitHub evidence) / output tabs (Proposal, Cover Letter, Summary,
  Explanation, Sources).
- Real progress UX: per-action busy states, staged progress labels with elapsed
  timer during Analyze/Generate, server stage timings after completion.
- Full action set: Analyze/Re-analyze, Generate/Regenerate, Shorter/Technical/
  Business/De-AI, +/− Project, Copy, Save, Markdown download; error panel with
  Retry (no `alert()`; content preserved on failure).

### Tests — full suite 199 passed
- New: mode registration, selection reasons, explanation purity (no invented URLs),
  context-mixing flags, deterministic full flow (analyze→generate→validate offline).

## [Unreleased] — 2026-09-05 — Homepage style alignment to reference design

### Changed
- `rlz-cyan` token `#0e7490` → `#0891b2` (reference `--cyan`); project-media
  background aligned to `var(--rlz-bg)`.
- Scroll-reveal safety net (reference pattern): `.rlz-reveal` visible by default,
  hidden only once JS confirms (`.rlz-js` on `<html>` via `useLayoutEffect`, no
  flash), plus a 2.5s force-visible timeout so sections can never stick hidden.
- Deliberately NOT copied from the mock: invented stats (15/40/7), placeholder
  video IDs, fictional employers, fake contact details/links, alternate tech
  marquee — live site keeps verified data (12/30/6, real YouTube IDs, real career
  history, siteConfig contact, real stack) and the i18n wiring.

### Verified
- Frontend `tsc` + `eslint` clean, `vite build` OK.

## [Unreleased] — KB Guardrails + Hallucination Control (central, enforced)

No duplicate config/RAG systems: one `kb_policy` service, enforced by retrieval + concierge, edited in the KB Admin form.

### Added
- `app/services/kb_policy.py`: `DEFAULT_GUARDRAILS` (public/admin access, allow_rag/urls/source-code/internal/sensitive, require_source, blocked_fields) + `DEFAULT_HALLUCINATION` (grounded_only, min confidence, inference/general toggles, require evidence/verified-URLs, max_unsupported_claims=0, fallback/clarify, fallback message); `FIELD_META` drives the Admin form; normalize/resolve helpers with safe defaults (no migration — old docs resolve to defaults).
- Enforcement: `rag_query.retrieve(consumer=)` drops disallowed/orphan chunks server-side (fail-closed); `upsert_document` stores normalized policies; concierge validates LLM replies deterministically (no-evidence/low-confidence/unsupported-claims → fallback or clarify) and merges agent + per-doc policies (strictest wins); tool-derived sources ground `require_source`.
- Admin APIs: `GET /api/admin/rag/guardrail-schema`; doc create/update accept both policy blocks; metadata/policy-only saves skip re-indexing (no version bump, no embedding cost).
- Admin UI: Knowledge form gains Access/Visibility + Guardrails + Hallucination Control (schema-driven widgets with help tooltips) + RAG/Indexing note.

### Tests — full suite 192 passed
- New `tests/test_kb_policy.py` (20): normalization/clamps, consumer matrix, sensitive/code/rag gates, fail-closed orphans, blocked fields, grounding validation (missing/low-confidence/unsupported/ok), URL gate, schema shape, auth gates, live persistence + no-reindex save + public/admin retrieval split + concierge compliance. Fixed `test_github_knowledge` retrieval fixture for fail-closed (parent doc now inserted; new orphan-drop test).

## [Unreleased] — 2026-09-05 — AI orchestrator: precise failure diagnosis + JSON repair

### Fixed
- `AIService._complete` no longer collapses every failure into bare `JSONDecodeError`.
  Stages are now distinguished: `HTTP_{status}`, `NonJsonBody`, `EmptyContent`
  (with `finish_reason`), `Refusal`, `BadJson`, network errors. The admin error log
  records the cause plus a scrubbed raw snippet, so the next failure is diagnosable
  from System Logs alone.
- Repair path: prose/code-fence-wrapped JSON is parsed via balanced-brace extraction
  (`_extract_json_object`) instead of failing; downstream Pydantic validation still
  applies, so garbage is rejected, never trusted.
- Retry discipline: refusals and 400/401/403/404 break after 1 attempt (deterministic);
  429/5xx/network/empty/bad-JSON keep exponential backoff. Final `AIError` contract
  and visitor-facing graceful fallback unchanged.
- Rationale for the 12:49am incident (`openai: JSONDecodeError` ×3 on lead-chat):
  HTTP 200s with unparseable content — almost certainly empty/refused content for that
  specific visitor message, NOT a key/config problem (auth failures surface as
  HTTP_401). Key verified present; chain is OpenAI-only (no DeepSeek key set).

### Verified
- 5 new tests (23–27: prose repair, empty-content retries, refusal/401 early-break
  with attempt counts, extractor unit cases). Full suite 171/171 pytest.

## [Unreleased] — 2026-09-05 — 404 model fallback + request tracing in orchestrator

### Fixed
- `openai: HTTP_404` (e.g. concierge-reply, 1:03am incident): unknown/inaccessible
  primary model now retries ONCE with `openai_fallback_model`, then stops. Wired the
  previously dead `openai_fallback_model` setting into `_complete`.
  (Correction: an earlier draft of this entry wrongly called the `gpt-5.6-luna`
  default bogus — it is a REAL model, GPT-5.6 cheap tier $0.20/$1.20, verified
  against OpenAI docs. The default was kept; only the wiring was missing.)
- Error details now include `models tried: [...]` + OpenAI `x-request-id` when present
  (non-secret; proves WHICH model 404'd and lets support trace the call).

### Verified
- New test_28 (404 primary → success on configured fallback, model asserted dynamically).
  Lead-chat suite 28/28.

## [Unreleased] — Qdrant DOWN fix (missing client + no prod server)

### Fixed
- Root cause of dashboard "qdrant-client unavailable: No module named 'qdrant_client'":
  the package was never declared. Pinned `qdrant-client==1.12.1` in
  `requirements.txt` (same pin as PestFlow) and installed it.
- Production had no vector server at all (ai-api defaulted to `localhost:6333`,
  unreachable in-container). Added internal-only `qdrant` service
  (`qdrant/qdrant:v1.11.3`, persistent `/opt/rajiblabs/data/qdrant`, no published
  ports — no PestFlow clash) + `QDRANT_URL=http://qdrant:6333` to ai-api env;
  `deploy-vps.sh` creates the data dir. Aligned `LOG_RETENTION_DAYS` default to 7.
- Verified live: import OK, client↔server round-trip (upsert/search/delete on a
  scratch collection, removed afterwards), health endpoint now reports real
  collection status instead of the import error.

### Tests — full suite 166 passed
- New in `test_rag.py`: requirements-guard (package declared), import check,
  health-never-raises on unreachable server, live upsert/search/health round-trip.

## [Unreleased] — Docs refresh for future development

### Changed
- `MEMORY.md`: 15 admin pages + Login; routers/services/tests inventory current (~162
  tests, 7 files); new Concierge/agents rules section (tools, guardrails, lead flow,
  `ai_agents` store); Motor `db or get_db()` bool-trap + `respx` install gotchas;
  current endpoint/collection inventory (`/api/public/agent/*`, `/api/admin/agents/*`,
  GitHub knowledge lifecycle, `github-sources`; `error_logs` 7-day TTL + sweep).
- `README.md` deployment: shared-VPS `:8080` edge, `deploy-vps.yml` auto-deploy,
  full GitHub Secrets list (SSH + app secrets sync).
- Verified while writing: `?lang=` endpoint suffix (not `?lang/`), `LOG_RETENTION_DAYS=7`
  in config/env/docs, `docker-compose.production.yml` edge + external network.

## [Unreleased] — 2026-09-05 — Agentic database-driven multilingual framework (12 languages)

Agentic, cost-capped i18n as a clean extension: English default, admin-controlled
languages, static + database + cached-LLM translation levels, one shared RAG index.

### Added
- Language master: `languages` collection + `SEED_LANGUAGES` (en default + bn/hi/fr/ja/de/es/pt/zh-CN/ko/it/ar, ar RTL) seeded in `init_db`; unique `code` index; admin Languages page (enable/disable, add, edit, order, delete-if-unused; default protected).
- `translations` + `translation_cache` collections + indexes. Priority chain: approved → content cache → valid generated → English source (+ background LLM fill) → explicit LLM only when asked; every LLM call via `AIService` orchestrator, secrets refused, result cached permanently under source hash.
- Agents: `TranslationAgent` (orchestrator-only, call-counted, URL/code/placeholder protection) + `TranslationQualityAgent` (zero-cost: URLs, placeholders, formatting, script-mismatch, echo, length checks) in `app/services/translation_agents.py`; `LanguageService` / `TranslationService` / `TranslationCache` (+ `localize_doc`, `localize_many`, `universe`, `coverage`).
- Public API: `GET /api/public/languages`, `GET /api/public/translations/{language}` (hash-checked), `POST /api/public/translate` (rate-limited); `?lang=` overlay on `/home`, `/projects`, `/projects/{slug}`, `/products`, legacy `/api/products*` (English = zero-cost passthrough).
- Admin API (`require_admin`, audited): languages CRUD + `PATCH /{code}/status` + guarded `DELETE`; translations list/generate/regenerate/edit/approve/delete + coverage. Admin Languages + Translations pages (nav group Localization).
- Multilingual chat, same KB: `language` on lead chat, RAG `/query`, and concierge agent (final-reply localization via content-hash cache, ≤1 call first time, 0 steady-state); workbench generate/chat accept `language`.
- Frontend L1: 12 locale bundles (`src/i18n/*.json`, key-parity checked), `LanguageProvider` (stored → browser-detect → default; `<html lang/dir>` sync; English fallback per key), top-right selector (enabled-only) in `RlzNav`, localized Nav/Hero/Contact/Footer/ChatWidget, `?lang=` on CMS fetches, chat sends UI language.

### Fixed
- `test_lead_chat.py` strict fake updated for backward-compatible `language` kwarg.
- Pre-existing build breaks fixed: missing `Field` import (GitHubManage), unused import (AgentsManage).

### Verified
- Backend 161/161 pytest (21 new `test_i18n.py`: seed/resolve/guards, protection, secret refusal, quality flags, chain priority, bill-once caching, stale handling, overlay skips, auth, public fallback, chat instruction).
- Frontend `tsc` + `eslint` clean, `vite build` OK.

## [Unreleased] — Public AI Concierge + Admin Agent Management

Reuses chat sessions/messages, RAG/Qdrant, GitHub knowledge, lead/idea pipeline, AIService orchestrator — no duplicate systems.

### Added — concierge (`/api/public/agent/*`)
- `agent_tools.py`: 10 sanitized public tools (profile, projects/detail/live-url, products, services, GitHub, contact, RAG search/sources); allowlisted outputs, URLs DB-only, admin-only names rejected server-side.
- `concierge.py`: rule-based intent (13 intents) + entity extraction + allow-list tool selection; tool/DB/RAG lookup → single small LLM reply; deterministic tool-only fast paths (greeting/contact/verified live URL/lead follow-ups) that never call the LLM; guardrail source filtering + reply-URL validation (unverified links stripped); gradual lead capture (one field/turn, Thanks-greeting on capture) via existing pipeline storage; turn persistence with intent/tools/sources/lead/latency/model.
- `GET /config` (public card: name, starters) + `POST /chat` (rate-limited, graceful degradation when disabled/down).

### Added — agents store + admin (`/api/admin/agents/*`, JWT)
- `ai_agents` collection (seeded concierge): prompt, tools, knowledge policy per source (public_allowed/priority), guardrail/hallucination/response policies, style, lead + fallback config; future types supported. CRUD/test-console/stats (turns, tools, conversions, errors, p50 latency, models)/conversations endpoints.

### Added — UI
- Homepage: "Chat with RajibLabs Agent" hero button opens chat; widget shows server-driven conversation starters, concierge greeting, ask-tab on the agent endpoint (plan/blueprint flow untouched).
- Admin AI Agents page (Intelligence group): agent switcher, enable/public toggles, full editor, test console, stats, conversations, future-agent creator.

### Tests — `tests/test_concierge.py`: 46 passed
- Intent matrix (incl. all starters), entities, tool mapping/allow-list, auth rejection, sanitization, policy filter, URL validation/collection, fallback purity, contact extraction, lead triggers, config CRUD, live tool shapes, LLM-free tool-only turns, full lead capture, disabled-agent, provider-failure, endpoint auth. Full suite: **161 passed**, `tsc` clean.

## [Unreleased] — GitHub Integration & Knowledge Sync (Admin)

Built on the existing pipeline (`github_service` + `rag_ingest` + shared Qdrant index) — no duplicate GitHub/RAG/vector/auth systems.

### Added — token & connection (`/api/admin/github/*`, JWT)
- `POST /config` stores the PAT in `site_settings` (write-only, shape-validated, audited); `GET /config` returns masked status (`***last4`, source db|env, owner) — full token never returned; `DELETE /config` revokes; `POST /test` validates any token and returns account info (login, name, repos, followers). DB token wins over env (`resolve_github_token/owner`), `sync_now` refactored onto it.

### Added — repo knowledge lifecycle
- `PATCH /repositories/{id}` (`rag_enabled`, classification); `POST .../sync` (manual incremental sync, 409 when disabled, last-error recorded); `GET .../knowledge` (docs/chunks/last-indexed/status rollup); `POST .../reindex`, `POST .../disable` (flag off + vectors removed), `DELETE .../knowledge` (docs + vectors removed).
- `upsert_document` + Qdrant payloads gain `branch`/`file_path`/`commit_sha`; ingest passes them per doc. Stale-file cleanup deletes docs + vectors for files gone from the tree; `rag_enabled=False` repos refuse ingest; file content secret-scrubbed before indexing.
- `GET /api/admin/rag/github-sources`: per-repo tree (docs, chunks, last indexed, index/sync status) for the KB Admin; `GET /documents` gains `repository` filter.
- Proposal Studio: `github_documentation` chunks are now selectable as work examples (URLs already attached from retrieval — no invented links).

### Added — Admin UI (same template, no new routes)
- GitHub Projects page: Connection panel (masked token status, save/test/revoke, account info) + Knowledge-sync table (toggle, per-repo Sync Now, last sync, errors). Portfolio-publish cards untouched.
- Knowledge Base page: GitHub sources panel (counts, status, View/Re-index/Enable/Disable/Sync/Delete).

### Tests — new `tests/test_github_knowledge.py`: 12 passed
- Masking, config masked/revoke + auth gates, mocked connection ok/401, discovery upsert (no dup, token never persisted), sync metadata, incremental (unchanged/update/stale-removal), secret-content scrub, failure-record + retry, disable/delete (vectors removed), RAG retrieval URL passthrough, workbench GitHub selection.
- Full suite: my areas green (`test_rag` + `test_workbench` + `test_github_knowledge` = 52 passed; `tsc` clean). NOTE: 25 pre-existing failures in `test_lead_chat.py`/`test_i18n.py` (other agent's uncommitted lead system — verified unrelated: fails identically with my config reverted, my only touches there are additive log kwargs).

## [Unreleased] — System Logs upgrade: grid, search, details, 7-day retention

### Added
- `GET /api/admin/logs` now takes `q` (message/source/module/path/error search, regex-escaped), `level` (info|warning|error), `source`, `date_from`/`date_to`, `sort` (newest|oldest), `page`/`page_size` (≤200) and returns `{items, total, page, page_size, retention_days, window_start}` — always constrained to the latest 7 days. New `GET /api/admin/logs/{id}` detail endpoint.
- Log docs gain `logger` (module), `path`, `stack_trace`; all call sites enriched; daily-agent failures record full tracebacks. Old docs read fine (fields optional).
- Retention 5→7 days (`LOG_RETENTION_DAYS` default + both env templates + `docs/configuration.md`): TTL index (auto-rebuilt) + new daily-agent `purge_old_logs` sweep as backup.
- Secret scrubbing on every write (`password/token/secret/key` assignments, Bearer, `sk-/ghp-/pat/xox-` tokens, credentialed DB URIs); truncation caps kept.
- Frontend `LogsManage`: `rla-table` grid (Time sortable, Level pill, Source+module, truncated message, View action), debounced search, level/date/sort/page-size filters, pagination, details modal (full fields + error details + stack trace, ESC/overlay close), new `rla-*` CSS (filter grid, pager, modal, kv, pre).

### Tests — `pytest -q`: 83 passed
- New: scrub cases, level normalization, cutoff math, query-builder (window/filters/escaping), detail auth gate, live filtering + window exclusion + sweep + scrub-integration (real Mongo).

## [Unreleased] — 2026-09-04 — Admin light redesign: shared template on all 12 pages + Proposal Studio + RAG fixes

### Added
- Admin light design system: `frontend/src/styles/admin.css` (scoped `.rl-admin`, Sora/Inter/JetBrains Mono, violet→cyan) + `frontend/src/components/admin/ui.tsx` template primitives (`PageHead`, `Panel`, `StatusPill`, `Chip`, `Field`, `Empty`) + `frontend/src/components/admin/toast.ts` event toast bus. All 12 admin pages (Dashboard, Resume, Portfolio, GitHub, Products, Profile, Content, Leads, Knowledge, AI Proposal Studio, Logs, Settings) + Login rewritten onto it; public site untouched.
- Rebuilt `AdminLayout`: grouped sidebar, section search + ⌘K quick-jump, live notifications bell, working topbar GitHub sync, mobile drawer, real admin email.
- Rebuilt `Dashboard`: real-data KPIs, quick actions, system status (backend/GitHub/RAG/AI), recent activity, needs-attention, content library. Rebuilt `Login` to match.
- Admin AI Proposal Studio (end-to-end): `app/services/workbench{,_prompts}.py` (analyzer → shared-RAG retriever → matcher → generator → quality gate → refiner, all via `AIService` orchestrator), `app/routers/admin_workbench.py` (8 JWT endpoints under `/api/admin/ai`), `proposal_documents` + `proposal_sessions` collections + indexes, `frontend/src/pages/admin/Workbench.tsx` (`/admin/ai-workbench`, `/admin/ai-workbench/history`), `tests/test_workbench.py` (20 cases).
- RAG completion: public `POST /api/rag/query` + `GET /api/rag/health`, admin `/api/admin/rag/*` (dashboard/CRUD/reindex/evaluate), RAG-augmented lead chat (`intent`+`sources` in chat response, `mode:"rag"`), `KnowledgeManage.tsx` admin page, `tests/test_rag.py` (20 cases), Qdrant service in `docker-compose.yml`.
- Font Awesome bundled locally (`@fortawesome/fontawesome-free` npm import in `admin.css`); cdnjs CDN link removed (was flagged by tracking prevention, broke offline).

### Fixed
- Black screen after admin login (`TypeError: ... .reduce is not a function`): `/api/admin/logs/stats` returns `by_level` as an **object**, Dashboard treated it as an array. Fixed + `Array.isArray` guards on every admin list fetch (Dashboard, AdminLayout notifications).
- RAG chunk hydration: Qdrant point IDs are UUIDv5, unresolvable as Mongo ObjectIds → vectors now carry `mongo_chunk_id` in payload; Mongo rows written first, rolled back on vector failure.
- `github_rag_repos` is a comma-separated **string** (not a list) — admin reindex now parses it, falling back to tracked public repos.
- `EmbeddingService.descriptor()` keys are `embedding_provider/model/version/dim`; routers updated (`health_check()` replaces nonexistent `collection_info()`).
- GitHub skip lists extended (secret filenames, key/data/binary extensions).
- `_overlap_terms` ignored short tech tokens (`.NET`, `AI` never matched evidence) — boundary-aware substring matching added.
- Windows dev builds broken by WSL-run `npm install` pruning win32 native bindings — restored `rolldown`, `@tailwindcss/oxide`, `lightningcss` win32-x64-msvc bindings at exact lock versions. **Run `npm install` from Windows, not WSL.**
- Full verification: backend 75/75 pytest, frontend `tsc` + `eslint` clean, `vite build` OK (FA woff2 bundled in `dist/assets`).

## [Unreleased] — App secrets from GitHub Secrets (VPS deploy)

### Added
- `deploy-vps.yml` syncs `OPENAI_API_KEY`, `GITHUB_TOKEN`, `ADMIN_INITIAL_PASSWORD`, `SECRET_KEY`, `JWT_SECRET` from GitHub Secrets into `/opt/rajiblabs/config/.env` on every deploy (non-empty win, server file stays fallback; values never printed, file `chmod 600`). Upsert logic verified (replace/preserve/skip-empty/reload).

## [Unreleased] — Dedicated VPS workflow (auto-deploy on merge to main)

### Added
- `.github/workflows/deploy-vps.yml`: standalone "Deploy VPS" workflow — fires on every push/merge to `main` (+ manual dispatch). SSHes to the VPS, pulls `/opt/rajiblabs/app`, runs `deploy-vps.sh` (30 min timeout), skips cleanly without secrets. The old manual `deploy-vps` job was removed from `ci.yml` (now build + FTP only) so there is exactly one VPS path.

## [Unreleased] — CI VPS deploy job (SSH, manual)

### Added
- `deploy-vps` job in `ci.yml`: manual ("Run workflow") SSH deploy to 169.58.165.10 — pulls `/opt/rajiblabs/app` and runs `deploy-vps.sh` (30 min timeout). Skips cleanly without secrets. Needs `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` (+ optional `VPS_SSH_PORT`). YAML-validated.

## [Unreleased] — Shared-VPS POCs: zero PestFlow impact proven, keep :8080

### POC results (all PASS — decision: no port change needed)
- **POC-1 clash matrix** (both production composes): published ports disjoint (PestFlow `80/443/127.0.0.1:1433` vs RajibLabs `8080/127.0.0.1:27017`) → **OVERLAP: NONE**; container names disjoint; networks separate (`pestflow-internal` attached external-only); `/opt` binds disjoint (`/opt/pestflow/*` vs `/opt/rajiblabs/*`); images and env files separate. Only 8080 user elsewhere is PestFlow's **dev** compose, which never runs on the VPS.
- **POC-2**: production compose renders clean (edge `8080:80`, external net attached).
- **POC-3**: `gateway.conf` static check 10/10 (single `:80` server, `/`→frontend, `/api/`+`/health`→ai-api, 12 MB uploads, no PestFlow coupling, balanced braces).
- Verdict: :8080 already IS the "different port" — PestFlow untouched (no shared ports/names/volumes; Phase-2 domain move is additive server blocks + reload only).

### Changed
- `deploy-vps.sh`: added `pestflow-internal` network preflight (fails with fix instructions if PestFlow stack absent) alongside the existing `:8080` clash check. `sh -n` clean.

## [Unreleased] — 2026-09-03 — Default OpenAI model → gpt-4o-mini

### Changed
- `OPENAI_MODEL` default is now `gpt-4o-mini` ($0.15/1M in, $0.60/1M out) per operator choice: `app/config.py`, `.env.example`, `.env.production`, backend `README.md`, local `.env`, `deploy/dotenv.production.example`, `docker-compose.production.yml` fallback.
- `docs/configuration.md`: model table + cost math updated (~3,300 chats / ~1,150 AI jobs per $1). `gpt-5-nano` ($0.05/$0.40) documented as the cheaper env-only alternative; fallback stays `gpt-5.6-luna`.
- `pytest -q`: 11 passed, 2 skipped (unchanged).

## [Unreleased] — VPS deploy readiness (169.58.165.10)

### Added
- `deploy/deploy-vps.sh`: one-command VPS deploy — tooling/env/secret preflight (refuses empty `<16-char` secrets), host dirs + `gateway.conf` install (never overwrites), `up -d --build`, ai-api health-gate with log dump on failure, edge smoke tests (`/health`, `/api/health`, `/`, `/api/projects`), plus admin URL and SQLite-migration runbook in the success banner. `sh -n` syntax-checked.
- `rajiblabs-ai-backend/Dockerfile` now ships the resume seed PDF (`init_db` copies it to `UPLOAD_DIR` on first boot); new `.dockerignore` files for backend (no tests/`__pycache__`/`.env`/uploads in the image) and frontend (no `node_modules`/`dist` in build context).
- `deploy/dotenv.production.example`: IP-based production env template (points at `docs/configuration.md` + domain-oriented `.env.production` for reference).

### Verified
- `docker compose -f docker-compose.production.yml config`: renders clean (only expected unset-secret warnings); only `:80` + localhost mongo published.
- Frontend `npm run build` (`tsc -b` + vite): clean, 776 ms.
- `pytest -q`: 11 passed, 2 skipped.
- Not runnable here: `docker build` / `nginx -t` (this box's Docker client is broken — SIGBUS; user runs Docker Desktop 29.7.2 on Windows, verified working). Re-verify images + gateway on the VPS via `deploy-vps.sh` smoke tests.

## [Unreleased] — run-docker.bat batch-syntax fix

### Fixed
- `not was unexpected at this time` crash: unescaped `)` in three `echo` lines inside parenthesized blocks prematurely closed the blocks at parse time (`(v2 plugin)`, `(fill secrets!)`, `(%%i/18)` → `^)`). The first one fired on every run at the compose-version check.
- Quoted all `if "%errorlevel%" neq "0"` comparisons (empty-safe); detection commands (`where`, `docker info`, `docker compose version`) keep `>nul` on stdout but no longer swallow stderr; `TEMP` fallback + `if exist` guard on the health-file read.
- Validated per-label-section with a paren-balance checker (no unescaped `)` in blocks, no unbalanced closers, no unquoted comparisons). No Docker/WSL changes; modes and behavior preserved.

## [Unreleased] — VPS production compose (169.58.165.10, PestFlow pattern)

### Added
- `docker-compose.production.yml` (root): production stack for the VPS — `mongo` (internal, 127.0.0.1:27017 host-tooling only, `/opt/rajiblabs/data/mongo`, mongosh healthcheck), `ai-api` (full env wiring with `${VAR}` secrets from `/opt/rajiblabs/config/.env`, uploads bind `/opt/rajiblabs/data/uploads`, urllib `/health` check, starts only after mongo healthy), `frontend` (static only), `gateway` (nginx:1.27-alpine, sole publisher on `:80`). Private `rajiblabs-internal` network, `unless-stopped` everywhere, persistent bind mounts (reboot-safe), full setup/deploy commands in the header.
- `deploy/nginx/gateway.conf`: edge routing (`/` → frontend PWA, `/api/*` + `/health` → ai-api, 12 MB uploads, security headers; plain HTTP — IP-only VPS, no certs).
- `deploy/dotenv.production.example`: production env template (`APP_URL=http://169.58.165.10`, required secrets + optionals).
- Validated with `docker compose config` (renders clean; only expected unset-secret warnings). Gateway `nginx -t` pending Docker daemon access — re-verify on the VPS at deploy time.

## [Unreleased] — .NET API removed, all APIs on Python (FastAPI + MongoDB)

Joint work with the parallel agent (removal, seeds, CI/run-script cutover, route test) — consolidated to a single port.

### Removed
- Deleted `backend/RajibLabs.Api/` (.NET 8 + SQLite: `Program.cs`, EF models/`LabDbContext`, Docker assets, tracked `rajiblabs.db`; resume PDF preserved via move to `rajiblabs-ai-backend/data/`). DB recoverable from git history for migration.
- Deleted orphaned `scripts/admin_server.py` (SQLite-backed mini-admin with hardcoded credentials; unreferenced).
- Removed `dotnet-api` from `docker-compose.yml` (ai-api moved to host `:8090`); nginx now routes all `/api/` to FastAPI.
- Removed .NET from CI (`setup-dotnet`, restore/build/publish, backend artifacts, backend FTP mirror), `run.bat` (rewritten: frontend-native + `docker` delegate mode), and `.gitignore` backend entries.

### Added — `app/routers/legacy.py`: Site API (v1), 47 routes, same paths + camelCase shapes
- Public: `GET /api/projects|projects/{id}|activity|profile|health|learning|portfolio|portfolio/{slug}|products|products/{slug}|content/{key}|resume/current`, `POST /api/contact|activity*|learning|subscribe|unsubscribe`, `PATCH /api/projects/{id}*` (*`X-Api-Key`, unchecked when `API_KEY` empty — new setting, mirrors .NET).
- Legacy admin auth: `POST /api/admin/login|logout`, `GET /api/admin/me` (same BCrypt admin store, dual-email; sets `rlabs_token` + `rlabs_access` cookies).
- Admin parity: dashboard (exact legacy shape), profile GET/PUT, portfolio + products CRUD, GitHub repos/sync-log/heuristic-sync/PATCH (dotnet `review`/`professional`/`ai`/`dotnet` semantics, manual edits preserved), resumes full cycle (upload/download/publish/delete, extraction + decision), content list/PUT.
- New collections: `legacy_projects`, `activities`, `profiles`, `contacts`, `courses`, `subscribers`, `portfolio`, `legacy_repos`, `sync_logs`, `website_contents`, `resume_extractions`. Reuses seeded `products`, `website_contents`, `resumes`.
- Consolidation: the parallel `legacy_admin.py` (28-route subset on conflicting collections) was removed in favor of this single router; route-param convention is `{rid}` (contract test normalizes names).

### Data — `scripts/migrate_sqlite_to_mongo.py` migrates all 14 tables
- `legacy_id` preservation, idempotent re-runs (matched by id/slug/key/url/email). Verified live against real MongoDB: test DB (4 projects, 6 activities, 1 profile, 5 courses) migrated, `init_db` seeded the rest (products 2, content 1, resume 1 from PDF). Public + admin + CRUD round-trip verified (both admin emails login, dashboard counts, portfolio publish/edit/delete, subscribe idempotency).

### Fixed along the way
- `ensure_indexes`: `db or get_db()` crashes on Motor (`__bool__` raises) — startup would have failed once lifespan was wired; now `get_db() if db is None`.
- **passlib 1.7.4 + bcrypt≥4.1 is broken** (raises on its own probe) — `app/auth/utils.py` now uses `bcrypt` directly; `requirements.txt` swaps `passlib[bcrypt]` → `bcrypt>=4.1`. Hash/verify + .NET-hash compat verified.
- `POST /api/subscribe` returns 200 for existing/reactivated (was hardcoded 201).

### Tests — `pytest -q`: 11 passed, 2 skipped
- `test_legacy_public_shapes` (paths + camelCase keys, Mongo-gated skip), `test_legacy_validation_no_db` (400/401 gates without DB), `test_legacy_routes_registered` (normalized names). `tsc --noEmit`: clean.

### Changed
- `frontend/src/services/auth.ts` is FastAPI-only (`/api/admin/auth/*`); `vite.config.ts` proxy → `localhost:8000`; `run-docker.bat` simplified to frontend :5010 / API :8090 / Mongo :27017.
- Docs updated: root `README.md`, `IMPLEMENTATION_PLAN.md`, `rajiblabs-ai-backend/README.md`.
- Supersedes the coexistence notes below: dual-backend entries (validation gaps, .NET Swagger) describe the retired setup; gap items 1–5 are closed by this port.

### ⚠️ Production note
- SmarterASP previously served `/api/*` from the .NET publish output. Until FastAPI is hosted for production, **do not wipe the live `/rajiblabs` backend files** — CI now deploys frontend `dist/` only. Point production `/api` at the FastAPI host (set `VITE_API_BASE` or proxy) before removing server-side .NET artifacts.

## [Unreleased] — 2026-09-03 — Swagger for both APIs

### Added
- **FastAPI Swagger** (`rajiblabs-ai-backend`): full OpenAPI metadata (description, contact, license, 10 tag groups), every operation tagged (41 ops, zero untagged), Bearer Authorize button via existing JWT scheme. Served at `/docs` (Swagger UI), `/redoc`, `/openapi.json` in non-production; **all three now consistently disabled in production** (previously only `/docs` was gated — `/redoc` + `/openapi.json` leaked in prod). Regression test `test_swagger_spec_tagged` added (`pytest -q`: 8 passed, 1 skipped).
- **.NET Swagger** (`backend/RajibLabs.Api`): Swashbuckle 6.6.2 (`AddEndpointsApiExplorer` + `AddSwaggerGen` with "RajibLabs API (.NET)" doc info and Bearer security definition/requirement for the `POST /api/admin/login` JWT, incl. `rlabs_token` cookie note). UI + `swagger.json` served in Development always, in Production only with `Swagger:Enabled=true`. Verified live: dev → 37 paths + UI 200 + Bearer scheme; prod → 404. `dotnet build`: 0 errors (2 pre-existing warnings untouched).

### Docs
- `rajiblabs-ai-backend/README.md`: new "API docs (Swagger)" section; root `README.md`: Swagger rows in the API tables.

## [Unreleased] — 2026-09-03 — Gap fixes + admin System Logs (5-day retention)

### Fixed (all 7 gaps from the 2026-09-03 validation report)
1. **nginx routing** (`frontend/nginx.conf`): added FastAPI locations for `/api/admin/projects`, `/api/admin/logs`, `= /api/admin/github/status`, `/api/admin/github/repositories`; removed the dead `/api/admin/qa` rule (real path `/api/admin/agent/qa` was already covered by the `/api/admin/agent/` prefix). `/api/admin/dashboard` and `/api/admin/github/repos|sync-log` intentionally stay on .NET — the React admin pages depend on the .NET response shapes.
2. **`app/main.py` startup**: `lifespan` is now passed to `FastAPI()` so `init_db` + scheduler start correctly; deprecated `@app.on_event("startup")` double-init removed (also clears the FastAPI deprecation warning in tests).
3. **Dashboard serialization** (`GET /api/admin/dashboard`): `last_sync`/`last_agent` now converted with `oid_str`, `None`-guarded — no more `ObjectId` 500 risk.
4. **Resume fields**: upload now stores canonical `stored_path`/`filename`/`size_bytes`; public `GET /api/public/resume` strips both `stored_path` and legacy `path`; `/resume/download` reads `stored_path` with legacy-`path` fallback and returns 404 (instead of `KeyError` 500) when the file is missing.
5. **Admin CMS parity**: decision confirmed — .NET stays authoritative for profile/portfolio/products/content/resumes/github-repos admin paths until FastAPI ports land; documented in nginx + `IMPLEMENTATION_PLAN.md §8`.
6. **Test coverage**: suite grew 4 → 9 tests — added lifespan-wiring, log-truncation unit, auth-gate, and Swagger-spec tests for `/api/admin/logs|stats|dashboard|projects|leads` (all Mongo-independent). `pytest -q`: **8 passed, 1 skipped**.
7. **`.env.example` drift**: added all 15 missing keys (`BASE_URL`, `CORS_ORIGINS`, `APP_TIMEZONE`, `MONGO_DB_NAME`, `JWT_EXPIRE_MINUTES`, `REFRESH_EXPIRE_DAYS`, `JWT_ISSUER`, `OPENAI_MAX_RETRIES`, `AI_QUALITY_THRESHOLD`, `DAILY_AGENT_HOUR/MINUTE`, `LOG_RETENTION_DAYS`, `UPLOAD_DIR`, `MAX_IMAGE_MB`, `MAX_RESUME_MB`). `tsc --noEmit` on frontend: clean.

### Added — admin System Logs section (failures kept 5 days)
- New `error_logs` Mongo collection: `{level: error|warning, source, message, details, created_at}`, text capped (source 120 / message 500 / details 2000 chars) so one failure can't bloat the DB.
- **5-day retention** via TTL index on `created_at` (`expireAfterSeconds = LOG_RETENTION_DAYS * 86400`, default 5, configurable); index auto-rebuilt if the setting changes; supporting indexes on `(level, created_at)`, `(source, created_at)`.
- Failure capture wired (each guarded so logging can never break the fallback path): `daily_agent` failure → `error`; `github_sync` failure → `error`; OpenAI enrichment/chat fallback → `warning`.
- Admin API (JWT, FastAPI): `GET /api/admin/logs?level=&source=&limit=` (max 500), `GET /api/admin/logs/stats` (retention window, counts by level/source, newest/oldest), `DELETE /api/admin/logs` (early purge + audit entry). Nginx routes `/api/admin/logs` → ai-api.
- Frontend: new **System Logs** page (`/admin/logs`, nav entry, level filter, expandable details, purge button with confirm, empty-healthy state).

## [Unreleased] — 2026-09-03 — Backend sync & validation (FastAPI + .NET coexistence)

### Sync with other agent
- Reviewed the FastAPI + MongoDB backend (`rajiblabs-ai-backend/`, commit `4251c3c`) built by the parallel agent against the requirement spec (`proposals/rajiblabs-ai-backend-master-prompt.md`) and `IMPLEMENTATION_PLAN.md`.
- Confirmed coexistence strategy: **both backends run side-by-side** via Docker (`dotnet-api:8090`, `ai-api:8091`) with nginx routing (`frontend/nginx.conf`) splitting `/api/*` by prefix. Legacy `.NET 8 + SQLite` API stays authoritative for the React admin panel; FastAPI + MongoDB serves new public CMS (`/api/public/*`), chat/leads, AI rewrite, and daily-agent endpoints. No data loss, no breaking change to the live admin.
- Frontend `App.tsx` detail pages (`/portfolio/:slug`, `/products/:slug`) and `services/api.ts` (`getCmsProjects`, `sendChat`, `submitLead`) already try FastAPI first with graceful fallback — parity path verified in code.

### Validation — PASS with known gaps (see below)
- `pytest -q` in `rajiblabs-ai-backend/`: **3 passed, 1 skipped** (MongoDB not running locally; `test_public_projects_published_only` skips gracefully). Health, GitHub-URL validator, and quality-gate tests green.
- `python scripts/run_qa.py`: pytest PASS; secret scan reports 2 hits, both false positives (empty `OPENAI_API_KEY` placeholders in `.env.example` and the spec doc). No hardcoded `sk-`/`ghp_` keys or passwords in `app/` or `scripts/`.
- `py_compile` over all `app/` modules: OK.
- Route inventory (38 endpoints) verified against code: health, 9 public CMS, 3 admin-auth, 9 admin-CMS (dashboard/projects/leads/notifications), 4 GitHub, 4 AI, 3 agent, 3 chat/lead/quote, 2 resume.
- Security spot-checks: JWT access (15 min) + refresh (7 d, HttpOnly `Secure; SameSite=Strict`) cookies; login rate-limit 5/min/IP; bcrypt hashing; admin seed never overwrites; `GITHUB_TOKEN`/`OPENAI_API_KEY` server-only, masked from responses/logs (`core_logging.RedactFilter`); upload validation (resume PDF/DOCX ≤10 MB, images ≤5 MB, randomized filenames, `stored_path` stripped from public responses); CORS restricted to `localhost:5173` + `https://rajiblabs.com`; no `.env` committed (gitignored).
- Spec deviations recorded as **accepted decisions** (not defects): MongoDB instead of SQLite (§1 stack), React admin instead of Jinja2 panel (§5.2), `/api/public/*` + `/health` paths instead of legacy `/api/*` paths (§4 — nginx + frontend fallback bridge the gap), renamed collections (`customer_conversations/customer_messages/customer_leads`, `github_sync_runs`, `ai_content_versions`), OpenAI model `gpt-5-nano`/`gpt-5.6-luna` instead of `gpt-4o-mini`.

### Known gaps / follow-ups (not regressions — new work for backlog)
1. **nginx routing gaps** (`frontend/nginx.conf`): `/api/admin/dashboard`, `/api/admin/projects`, `GET /api/admin/github/status|repositories`, `POST .../repositories/{rid}/map`, and `/api/admin/agent/qa` have no FastAPI location rule — they fall through to `dotnet-api` (404 on both stacks for the new paths; `/api/admin/qa` rule points at a non-existent FastAPI path, real path is `/api/admin/agent/qa`). Fix by adding explicit locations for each FastAPI prefix.
2. **`app/main.py` startup**: `lifespan` context (init_db + scheduler) is defined but never passed to `FastAPI()`; legacy `@app.on_event("startup")` (deprecated) double-runs `init_db` without starting the scheduler. Fix: `FastAPI(lifespan=lifespan)`, drop `on_event`.
3. **`GET /api/admin/dashboard` serialization**: returns raw `last_sync`/`last_agent` Mongo docs containing `ObjectId` — will 500 on JSON encode. Wrap with `oid_str` and guard `None`.
4. **Resume field mismatch**: upload stores `path`/`filename`/`size`, public `GET /api/public/resume` + `/resume/download` read `stored_path`/`filename` — download raises `KeyError`. Unify on one field name and guard missing file with 404.
5. **Admin CMS parity incomplete** (frontend admin still wired to .NET paths): `/api/admin/profile`, `/api/admin/portfolio`, `/api/admin/products`, `/api/admin/content`, `/api/admin/resumes*`, `/api/admin/github/repos`, `/api/admin/github/sync-log` exist only on .NET. Either keep .NET authoritative (current, working) or port these to FastAPI before switching nginx.
6. **Test coverage**: only 4 tests; master-prompt QA checklist §11 items (auth, CRUD, chat, agents with mocks) not yet automated. `scripts/run_qa.py` records to `agent_runs` only when Mongo is up (graceful warning otherwise — accepted).
7. **`.env.example` drift**: missing `JWT_EXPIRE_MINUTES`, `REFRESH_EXPIRE_DAYS`, `JWT_ISSUER`, `DAILY_AGENT_HOUR/MINUTE`, `MAX_IMAGE_MB`, `MAX_RESUME_MB`, `UPLOAD_DIR`, `MONGO_DB_NAME`, `APP_TIMEZONE` keys present in `config.py`. Add them so fresh setup matches code.

## 4251c3c — 2026-09-02 — feat: FastAPI + MongoDB AI portfolio CMS (replaces SQLite plan, .NET kept intact)
- New `rajiblabs-ai-backend/` (FastAPI, Motor/MongoDB, APScheduler daily agent, OpenAI content engine with hash-dedup + quality gate, GitHub sync preserving `is_manually_edited`, chat with knowledge fallback + rate limits, dual-email admin auth).
- Frontend: `ChatWidget`, `VITE_API_BASE` admin helper, CMS detail pages, `robots.txt`/`sitemap.xml`, admin layout updates.
- Dual-backend Docker + nginx split; `scripts/` for `create_admin`, `run_agent`, `run_qa`, SQLite→Mongo migration.

## ddea60c — 2026-09-01 — chore: agents/Design replaces stitch_* portfolio redesign assets
## 32bda2c — 2026-08-31 — fix: unified API deploy (`frontend/wwwroot` + backend to `/rajiblabs`)
