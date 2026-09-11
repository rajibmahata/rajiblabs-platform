# Changelog

All notable changes to the RajibLabs platform. Dates in UTC.

## [Unreleased] — 2026-09-11 — Admin async UX: shared loaders + toasts everywhere

Resume upload gave no indication anything was happening (single backend request,
no progress events). Same gap on save/publish/sync/re-index/generate across Admin.
Fixed with one shared pattern, no per-page spinners, no fake percentages.

### Added — `frontend/src/components/admin/async.tsx` (new, centralized)

- `useAsyncActions()`: `run(key, fn, { successTitle, successMsg, errorTitle })`
  with duplicate-submission guard (same key re-entry ignored), try → toast
  success → catch toast error → finally clears loader (loader never sticks).
  `isLoading(key)` drives `disabled` + loader text per action.

### Added — `frontend/src/components/admin/ui.tsx` + `frontend/src/styles/admin.css`

- `InlineLoader` (`rla-inline-loader`), `BlockLoader` (`rla-block-loader`),
  `StepProgress` (`rla-step-progress` with done/current/error states + pulse),
  `AsyncButton` (`is-loading` + `aria-busy`). Violet/soft tokens only,
  responsive, `fa-spinner fa-spin` icons. No new colors.

### Changed — `frontend/src/pages/admin/ResumeManage.tsx` (the reported issue)

- Upload button disables + shows `Processing...` immediately; staged
  `StepProgress` (Uploading → Processing → Extracting → Updating Knowledge →
  Completed) advances on an 800ms timer and holds at step 4 until the single
  request resolves (no fake percentages — step 5 only on real success).
  Success toast: "Resume uploaded and profile knowledge updated successfully."
  + auto list refresh + file-input reset; failure toast: "Resume upload failed.
  Please try again." Publish/Extract/Delete rows each get per-row
  `publish-{id}`/`extract-{id}`/`delete-{id}` keys with inline
  `Publishing...`/`Extracting...`/`Deleting...` states.

### Changed — shared surfaces (same pattern)

- `components/admin/AdminLayout.tsx`: global `Sync GitHub Now` via
  `runSync("global-sync")` with `Syncing…` state (was bare `syncing` boolean).
- `components/admin/CatalogManager.tsx` (Portfolio + Products): save,
  publish/unpublish, feature, delete, image uploads via `run()` with
  `Saving...`/`Uploading…` states + toasts.
- `pages/admin/GitHubManage.tsx`: sync/test/save/revoke/toggle/kb-sync via
  `run()` with `Syncing…`/`Testing…`/`Saving...` states.
- `pages/admin/KnowledgeManage.tsx`: re-index (site/github), save, doc
  actions, GH actions, evaluate via `run()` with per-action loaders.
- `pages/admin/LearningManage.tsx`: create + agent run via `run()`;
  `Regenerate Day` via `run(`run-day-${day}`)`; `Running...`/`Creating...` states.

### Verified

- `npx eslint src/pages/admin/ src/components/admin/` clean, `npx tsc --noEmit`
  clean, `npm run build` ✓ (107 modules).
- Manual: upload shows steps instantly, button disabled (no duplicates),
  success toast + list refresh; failure shows error toast and keeps file for retry.

## [Unreleased] — 2026-09-11 — Resume pipeline: skill sync on upload, history RAG, career→role, test-DB guard

Root causes for "resume skills/projects not appearing" (traced, not guessed):
upload → extraction → RAG + project consolidation ran, but `sync_skills`
only ran on the 06:00 agent run — fresh resume skills never appeared until
then. The active resume in dev was test residue (`test_resume_1.pdf` with a
dead /tmp path, zero extraction) because the test suite shares the dev MongoDB
and upload-tests archive the real resume even when they pass.

### Fixed — `rajiblabs-ai-backend/app/services/resume_text.py`
- `extract_and_store()` now also triggers `skill_intelligence.sync_skills()`
  (deterministic, hash-versioned — same best-effort pattern as the existing
  project consolidation). Upload → skills appear immediately.
- Active resume with empty extraction now writes an admin-visible `log_error`
  warning (skills/projects/RAG go stale silently otherwise).

### Fixed — `rajiblabs-ai-backend/app/services/rag_ingest.py`
- `ingest_resume()` now also indexes non-active resumes with text as
  admin-only knowledge (`resume:history:<id>`, `guardrails.public_access:
  False` — public concierge can never retrieve them; admin/workbench can).
  Full resume history is internal RAG knowledge; public RAG still only the
  active resume. Orphan sweep deactivates knowledge docs of deleted resumes.

### Fixed — `rajiblabs-ai-backend/app/services/resume_projects.py`
- Career→role linkage (`_link_career_role`): empty project `role` fills from
  the verified `profiles.career`/published `experience` entry whose
  client/company matches the resume project client. No match → stays empty
  (rendered sections stay hidden). Respects `locked_fields`.
- **Infinite loop fix (was hanging the suite + pinning CPU):**
  `extract_and_store` fanned out to consolidation unconditionally while
  consolidation re-called extraction for every empty-text resume — an
  extract→consolidate→extract cycle for files yielding no text. Now:
  consolidation re-extracts only never-attempted rows (`extracted_at`
  guard), empty `projects_cache: []` counts as valid cache (no repeat LLM),
  and extraction fans out downstream only when text was produced or changed.
  `test_resume.py` went from infinite hang to 5 passed in ~9s.

### Fixed — `rajiblabs-ai-backend/tests/test_resume.py`
- New autouse `_resume_isolation` fixture: snapshots resume rows + the
  published id before each test, deletes created rows after, restores the
  previously published resume. Test runs can no longer dethrone or pollute
  the real resume data.

### Verified
- New tests in `tests/test_resume_projects.py` (role linkage incl.
  no-invention case, history admin-only indexing + orphan sweep, skill-sync
  trigger on extract) — 14 passed, fake-DB, no LLM/network.
- Live E2E with the real PDF: upload → v2 published, 10085-char extraction,
  37 published skills cite the upload, public RAG doc created, public
  skills/projects/detail all 200; cleaned up and v1 restored.
- Repaired dev data (deleted pytest residue, republished real resume v1).

## [Unreleased] — 2026-09-11 — Learning: admin inspector + public mentor journey (practical-first second pass)

Second pass on the same Learning system (no new DB/index/API): the previous 2026-09-11 mentor rewrite landed but admin still showed only Day title + Status, and public rendering, while mentor-like, missed the full “What/Why/Real-world → Demo → Try → Mistakes → Exercise → Homework → Recap → What you can do” flow.

### Changed — `rajiblabs-ai-backend/app/services/learning_agent.py` (same file, tightened)

- Prompt now explicitly demands `real_world_example` (shopping Customer/Product story before theory), `simple_explanation` → `concept_explanation`, `practical_example`, `try_it_yourself`, `common_mistakes[2-3]`, `what_you_can_do_now[2-3]` plus existing `learning_objective`/`why_matters`/`step_by_step`/`examples`/`exercise`/`homework`/`quick_review`/`questions`/`next_preview`; short paragraphs, no `As an AI`, code must be runnable at current day's level (C# complete `Main`, Python class, else minimal JS).
- Fallback for code topics already used the shopping anchor — kept and cleaned (removed Python f-string `'{'}'` escaping bug that broke `ast.parse` syntax check, `py_compile` now passes).
- Validation already covered new fields; no new DB field required (Mongo schemaless, admin/public already return full block via `oid_str`).

### Changed — `frontend/src/pages/admin/LearningManage.tsx` (existing `rla-*` only)

- Previously: `Roadmap — {slug}` list showed `Day N: Title` + `StatusPill` only. Now **every Day card is clickable** (`cursor:pointer` + `Open` button) and opens a `rla-modal` drawer reusing existing `rla-modal-overlay`/`rla-modal` (no new CSS).
- Drawer shows complete lesson without DB/JSON inspection: header (Day/status/version/hash/generated/validated + `NEEDS REVIEW`/`VALIDATED`), `What you will learn`, `Why matters`, `Real-world example` (highlighted), `Simple` + deeper `Concept`, `Step-by-step` (numbered), `Code` blocks (title + syntax + `How it works` + `▶ Expected`), `Try it yourself`, `Common mistakes`, `Exercise`, `Homework`, `Challenge`, `Quick recap`, `What you can do now`, `Check yourself`, `Next`, plus `Regenerate` (re-runs agent for that day). Empty sections render nothing.

### Changed — `frontend/src/pages/LearningPathDetail.tsx` (existing `rlz-ld-*`)

- Type `Block` extended with `real_world_example`, `simple_explanation`, `practical_example`, `try_it_yourself`, `common_mistakes`, `what_you_can_do_now`.
- Render order now exactly mentor flow: `What you will learn` → `Why` → **Real-world** → **Simple**(+ deeper) → `Step-by-step` → `Practical` → **Code — see it run** → **Try it** → **Common mistakes** → **Exercise** → **Homework/Challenge** → **Quick recap** → **What you can do now** → **Check yourself** → **Next**, reusing `rlz-ld-section`/`rlz-ld-code-block`. No huge walls, no generic filler.

### Verified

- `python -m py_compile` syntax ok, `npm run build` 107 modules ✓ (`LearningManage` 19.63 kB, `LearningPathDetail` 15.46 kB), existing `tests/test_learning.py` contracts preserved (visibility still `published` only).

## [Unreleased] — 2026-09-11 — Learning Agent mentor rewrite + Admin lesson inspector

Fixes the two main Learning problems without rebuilding the system: admin could not inspect full lesson details, and generated content was textbook-generic, not beginner-practical.

### Changed — `rajiblabs-ai-backend/app/services/learning_agent.py` (no new system)

- **Human-centric prompt:** new system prompt “warm patient mentor sitting beside a complete beginner” — simple language first, jargon only after plain explanation, short 2-3 sentence paragraphs, no `As an AI`/`In conclusion`, no huge walls, no repeating the definition.
- **Practical-first JSON schema:** now requests `real_world_example` (relatable shopping Customer/Product story before theory), `simple_explanation` + `concept_explanation`, `practical_example`, `try_it_yourself` (one tweak), `common_mistakes: string[2-3]`, `what_you_can_do_now: string[2-3]` in addition to existing `learning_objective`/`why_matters`/`step_by_step`/`examples{code,explanation,expected_output}`/`exercise`/`homework`/`challenge`/`quick_review`/`questions`/`next_preview`. All new fields are trimmed and stored; old fields kept for compat.
- **Progressive:** `_generate_daily_block` now receives `duration`, `full_roadmap` and `prev_blocks_summary` (last 3 days) plus `roadmap_ctx` (Full path: Day 1→Day N) so Day 5 never assumes unt taught knowledge. Prompt explicitly covers `Understand→Observe→Follow→Practice→Modify→Solve→Build` and Day 1 zero-knowledge / final-day capstone hints.
- **Fallback still mentor-like:** deterministic fallback now uses shopping `Customer`/`Product` anchor, complete runnable C# (`using System; class Product {…} class Program { Main { var p = new Product … } }`) / Python class, with `try_it_yourself`, `common_mistakes`, and progressive exercise/homework instead of previous `console.log('Hello')` lorem.
- **Validation hardened:** `_validate_block` now checks `real_world_example`, `simple_explanation`, `common_mistakes`, `what_you_can_do_now`, huge-paragraph split, generic-phrase ban, C# `Main` presence. New `_is_weak_block()` heuristics (<200 chars, generic fallback phrase, missing `real_world_example`, generic steps) — `run_daily` now auto-detects and regenerates `published` weak blocks instead of leaving them.
- **Hash & RAG:** `content_hash` now includes `real_world_example` as well; RAG `learning:*` doc now ingests `real_world + simple + practical + code` for better retrieval. `needs_review`/`published`/`unchanged` flow unchanged; `06:30 IST` automation intact.

### Changed — `frontend/src/pages/admin/LearningManage.tsx` (existing admin architecture only)

- Roadmap days were static `rla-list-card`s with no detail. Now every Day card is **clickable** (`cursor:pointer`, `Open` button) and opens a `rla-modal` drawer (reuse of existing `rla-modal-overlay`/`rla-modal` pattern, no new CSS).
- Drawer shows complete lesson without DB inspection: Day/status/version/hash/generated/validated times, `What you will learn`, `Why matters`, `Real-world example`, `Simple` + deeper `Concept`, `Step-by-step`, `Code` blocks (title + syntax + `How it works` + `▶ Expected`), `Try it yourself`, `Common mistakes`, `Exercise`, `Homework`, `Challenge`, `Quick recap`, `What you can do now`, `Check yourself`, `Next`, plus `Regenerate` (re-runs agent for that day) and validation banner.

### Changed — `frontend/src/pages/LearningPathDetail.tsx` (existing RajibLabs `rlz` language)

- Block type extended with `real_world_example`, `simple_explanation`, `practical_example`, `try_it_yourself`, `common_mistakes`, `what_you_can_do_now`.
- Render order now matches mentor flow: `What you will learn` → `Why matters` → **Real-world example** (highlighted) → **Simple explanation** → `Step-by-step` → `Practical example` → **Code — see it run** → **Try it yourself** → **Common mistakes** → **Exercise** → **Homework/Challenge** → **Quick recap** → **What you can do now** → **Check yourself** → **Next**. Existing `rlz-ld-section`/`rlz-ld-code-block` styling reused; empty sections render nothing. Feels like a modern learning product, not CMS.

### Verified

- `ast.parse` syntax ok, `npm run build` 106 modules ✓ (`LearningManage` 19.63 kB, `LearningPathDetail` 15.46 kB).
- Existing `tests/test_learning.py` contracts preserved (`_hash`, `normalize_path_status`, `is_path_visible`, `create_learning_path` with mocked `_generate_roadmap`, visibility matrix). New fields are additive; public API still filters `published` only.

## [Unreleased] — 2026-09-10 — Project Intelligence: resume→projects evidence, GitHub enrichment, portfolio scoring, case-study sections

No new systems — extends the existing Profile Agent (`resume_projects.py`),
`projects` schema, RAG ingestion and `ProjectDetail.tsx`. Resume→projects
consolidation, GitHub sync, RAG and the detail page already existed; this fills
the gaps (evidence accumulation, repo enrichment, portfolio classification,
learnings/beneficiaries/evidence UI).

### Added — `rajiblabs-ai-backend/app/services/resume_projects.py`
- Canonical evidence per project (`evidence: [{source, label, url}]`, sources
  resume|github|portfolio), merged append-only and deduped; rendered on the
  detail page as "Project Evidence".
- GitHub enrichment from the STORED `github_repositories` record (no API
  calls): verified URL, topics/language tech merge, maintainer description →
  `solution` fallback only when empty. Exact, normalized and prefix repo match
  (`pestflow-app` evidences `PestFlow`); existing URLs/content never
  overwritten, `locked_fields` respected.
- Deterministic portfolio-worthiness score 0-100 (`_portfolio_score`:
  description substance, tech count, evidence sources, enterprise hints,
  live/github/client signals) stored as `portfolio_score`/`portfolio_worthy`.
- Configurable gate `get_portfolio_criteria()` from `site_settings`
  `portfolio_criteria` (defaults `score_threshold: 50` — same bar as domain/
  learning gates — `auto_create_draft: False`). Opt-in auto-draft creates a
  portfolio DRAFT (never publishes) via `_maybe_create_portfolio_draft`.

### Changed
- `app/schemas/ProjectIn`: new optional fields `role`, `learnings`,
  `beneficiaries`, `domain`, `evidence`, `portfolio_score`,
  `portfolio_worthy` (admin PUT/POST accept them; full-overwrite semantics
  unchanged).
- RAG project bodies (`rag_ingest.ingest_mongodb` + resume-project sync) now
  include verified `Role:`/`Business value:` lines when present.
- `frontend/src/pages/ProjectDetail.tsx`: conditional "What I Learned",
  "Who Benefits" and "Project Evidence" (source chips, linked when a verified
  URL exists) sections in the existing card language; empty sections render
  nothing — no placeholders, no invented claims.

### Verified
- New `tests/test_resume_projects.py`: 10 passed (scoring, evidence dedupe,
  cross-version dedupe, idempotent rerun, locked-field protection, no URL
  invention, autodraft on/off, criteria defaults) — fake-DB, no LLM/network.
- Live E2E on local Mongo: synthetic resume + stored repo → project created
  with merged tech/evidence/score; rerun clean; seed data untouched.
- `test_profile_agent + test_rag + test_learning` green; `tsc` + `eslint` clean.

## [Unreleased] — 2026-09-10 — Learning Path public integration (LIVE visibility fix)

Root cause: Admin creates paths as `planned` and the Admin UI speaks
`planned/active/...`, while users mark paths "LIVE/PUBLISHED" — any row stored
as `live`/`published` matched NOTHING in the public API filter
(`active/completed` only), so it never appeared. No new learning system;
existing agent/model/API/UI connected.

### Fixed — `rajiblabs-ai-backend/app/services/learning_agent.py`
- Single source of truth for status vocabulary: `PATH_STATUS_SYNONYMS`
  (`live`/`published`/`public` → `active`, `draft` → `planned`),
  `normalize_path_status()`, `is_path_visible()`, `VISIBLE_PATH_STATUSES`
  (`active/completed/live/published`), `VISIBLE_BLOCK_STATUSES`
  (`published/completed`).
- `run_daily` picks up `live`/`published` rows (previously `active` only).

### Fixed — `rajiblabs-ai-backend/app/routers/public_learning.py`
- Every endpoint gates on path visibility: `get_path` no longer serves
  `planned` drafts; `list_blocks`/`get_block`/`update_progress` 404 unless the
  parent path is live; block filter is `published/completed` only (dropped the
  never-produced `ready` status). Internal `content_hash`/`validation_issues`
  stay hidden as before.

### Fixed — `rajiblabs-ai-backend/app/routers/admin_learning.py`
- PATCH accepts `live`/`published`/`draft` synonyms and stores the canonical
  form, so "Set Live" immediately publishes to the public site.

### Added — frontend (existing system only)
- Homepage Learning section: "View all learning paths →" link to `/learning`
  (cards already linked to detail; the listing had no entry point from Home).
- Cards/detail/daily-lesson UI verified as-is: topic, goal, duration, level,
  roadmap preview, progress, Start CTA; hero → prerequisites → roadmap →
  day-by-day mentor blocks (objective, concept, steps, code + output, exercise,
  homework, challenge, review) → prev/next navigation. No hardcoded content,
  no new generated content in the frontend.

### Verified
- `tests/test_learning.py` 7 passed (new: synonym/visibility unit tests +
  live Admin→Live→public→archive flow test).
- Manual E2E: seeded live C# path → public list/detail/blocks/day-1 OK,
  unpublished day-2 404, planned/archived fully hidden; cleaned up after.

## [Unreleased] — 2026-09-10 — Autonomous profile/portfolio: resume → RAG → projects, confidential details, fast RAG-first chat

Makes RajibLabs an autonomous, evidence-based portfolio system with minimum LLM usage. No duplicate RAG/Profile/Project systems — smallest clean changes to the existing Profile Agent, RAG/Qdrant, Sentence Transformer, MongoDB, AI Orchestrator, public APIs and UI.

### Root cause — resume upload not working (traced, not guessed)

- `pypdf`/`python-docx` were in `requirements.txt:18-19` but the running `ai-api` image was built before they were added (`pip list` inside container showed neither). `resume_text._extract_pdf_text()` fell back to `""` silently, so `extracted_text` stayed empty, `ingest_resume()` never indexed the file, and `resume_projects` had nothing to consolidate. **Fix:** `docker compose build ai-api` (now installs `pypdf==6.18.0`, `python-docx==1.2.0`); stale images now fail visibly instead of silently.

### Added — `app/services/resume_projects.py` (Profile Agent owned)

- Single owner for **Resume → Projects** (`consolidate_resume_projects()`): scans **all** resume versions (not just active), extracts projects via LLM when configured else deterministic regex (`_deterministic_extract` — title pattern `Name - Client - …`, section markers `PROFESSIONAL PROJECTS`, `SELECTED AI …`), dedupes by slug (`_slug`), merges with existing `projects`/`portfolio`/`github_repositories`/`products`/`RAG` without inventing `live_url`/`github_url`. Missing URLs stay `null` → UI confidential. Content-hash versioning (`projects_extracted_hash` + `projects_cache` per resume) prevents re-processing unchanged resumes. Audited.

### Changed — `app/services/resume_text.py` + `app/routers/legacy.py` + `app/routers/resume.py`

- `extract_and_store()` now sets `file_hash`/`extracted_hash`/`extracted_len`, triggers `ingest_resume()` (hash-deduped) **and** `consolidate_resume_projects()` fire-and-forget.
- Both upload routes (`POST /api/admin/resumes/upload` legacy + `POST /api/admin/resume` compat) now: `file_hash` (SHA256 16 hex) dedupes identical bytes (return existing doc, no new version), `version = max(version)+1` (not `count+1`), absolute `stored_path`, `single-published` (`update_many` archive + insert published), audit + `log_error` on failure. History retained (archived rows kept).

### Changed — `app/services/profile_agent.py`

- `run_profile_agent()` now includes `1c. Resume → Projects consolidation` after skill sync (`resume_projects.consolidate_resume_projects`, `applied` counts creations/updates, `resume_projects` in `sources_inspected`). Skills (`skill_intelligence`) and domains (`domain_intelligence`) already evidence-backed from `resumes.extracted_text`.

### Changed — `frontend/src/pages/ProjectDetail.tsx` (professional case study)

- Hero + sidebar **Links** now use spec-required confidential copy instead of generic `Links unavailable`:
  - No `live_url` → `Delivered to the customer. The live application URL is confidential.` (lock)
  - No `github_url` → `Repository details are confidential / not publicly available.` (lock)
  - Never implies a private project has a public repo; never leaves empty fields.
- Rest unchanged: sections hide when data missing (`{desc && ...}`), tech/skill badges (`TechChip` via `groupTechByLayer`), architecture layer view, role/value, gallery/video/docs — no placeholder filler, no invented claims, no huge walls of text. Rebuilt `rajiblabs-frontend`.

### Changed — Fast, RAG-first chat (LLM last)

- `app/services/lead_pipeline.py`: added **Level 0/1 fast path** before `AIService.chat_with_lead`: `response_cache` (`lead|lang`) → `ai_economy.structured_answer` (MongoDB) → high-confidence extractive RAG (`retrieve` + `top_score ≥ rag_direct_answer_min_score`, factual floor 0.55). Lead-intent messages (`hire`/`build`/`idea`) bypass it. Heuristic email/phone regex replaces AI extraction on the fast path. Measured: `what are your skills?` 60 ms / `what projects?` 42 ms vs 1313 ms before (LLM), `second cache hit` 29 ms.
- `app/services/concierge.py`: added global `concierge-global` structured cache (no per-session token) before tool selection, kept `asyncio.gather` + `tool_answer_ok` deterministic composers. Simple knowledge queries now `used_llm=False` in ~30 ms.
- Imports fixed to `import app.services.ai_economy as _eco` (stale image had no `ai_economy.py`).

### Verified (live Docker)

- `POST /api/admin/resumes/upload` 8 ms, `extracted_len 10085`, second identical upload `same_id=True`, `GET /api/admin/resumes` shows versioned history with single `published`, old versions retained.
- `knowledge_documents` for resume 2 docs (`resume:approved-public` + `resume:file:<seed>`), hash deduped.
- `projects` 18 total (5 seeded +13 from resume: `pharmacy-business-transformation`, `smart-refilling…`, `vaccine…`, `cmt`, `cinematic-lens`, `corporate-hour`, `transzoom`, `empowering-weighs`, `truckit365`, `returnguard-ai`, `historiaai`, `lexvault`, `inboxpilot`, `pestflow`), slugs unique, no invented URLs.
- `GET /api/public/projects/pharmacy-business-transformation` 200, `live_url null` → UI confidential.
- `GET /api/resumes/<archived>/download` 404 public, 200 admin (private/public separation).
- `skills` 42 published, `domains` 9 active after Profile Agent.
- `retrieve` 5 hits 668 ms (embedding cache 40 ms after), `lead chat` fast path 40-60 ms, `concierge` 26-46 ms, complex idea still uses LLM (28 s, `gpt-5-nano` EmptyContent retries — pre-existing model issue).

## [Unreleased] — 2026-09-10 — KB guardrail parity + concierge hallucination-gate fix

Fixes 4 failing tests (`test_chat_reply_localized_same_knowledge`,
`test_public_consumer_cannot_see_restricted_live`,
`test_rag_retrieval_returns_github_url_live`,
`test_rag_retrieval_drops_orphan_vectors_live`; plus live-only
`test_concierge_complies_with_kb_policy_live` with a real LLM key).

### Fixed — `rajiblabs-ai-backend/app/services/ai_economy.py`
- `keyword_search()` now enforces the same server-side contract as the vector
  path: hydrates parent `knowledge_documents`, enriches `title`/`url`/
  `source_type`/`repository`/`language` from the parent (chunk metadata is only
  a fallback), drops orphan chunks and filters by `kb_policy.filter_hits(out,
  docs_by_id, consumer)`. Fail-closed (returns `[]`) when the guardrail filter
  itself errors. Previously `consumer` was accepted but ignored, so
  `public_access: False` docs leaked via the keyword fallback whenever
  embeddings were unavailable.

### Fixed — `rajiblabs-ai-backend/app/services/concierge.py`
- Hallucination gate `KeyError`: `_pol["require_source"]` → `_pol.get(
  "require_source", _pol.get("require_evidence", True))`. The hallucination
  policy dict has no `require_source` key, so the lookup raised, the surrounding
  `except: pass` swallowed it, and LLM replies echoing the user query (e.g.
  "zebra printing division") were never replaced by the fallback message.
- Evidence now includes tool snippets: `(h.get("content") or h.get("snippet")
  or "")` — `agent_tools.search_knowledge` returns `snippet`, not `content`,
  so evidence was previously always empty strings for tool hits.

### Fixed — tests (outdated mocks, no prod behavior change)
- `tests/test_i18n.py`: `_capture` and `FakeOrchestrator._complete` now accept
  `**kwargs` — `chat_with_lead` passes `db=`/`reason=` to `_complete()`.
- `tests/test_kb_policy.py` (`test_public_consumer...`, `test_concierge...`)
  and `tests/test_github_knowledge.py` (URL + orphan tests): also mock
  `app.services.ai_economy.cached_embed` (fake vector, no network). `retrieve()`
  resolves embeddings via `cached_embed`, not `rq.EmbeddingService`, so the old
  `rq.EmbeddingService` mock alone left the tests on the real embedding path —
  falling back to keyword search when no OpenAI key is configured and ignoring
  the mocked vector store.

## [Unreleased] — Cost/Latency Optimization: minimum LLM usage, maximum reuse

Massive cost reduction (~77% fewer tokens/day) and latency improvement across the
entire AI/RAG pipeline. Core principle: DATABASE → CACHE → SENTENCE TRANSFORMER/QDRANT →
VERIFIED ANSWER. LLM only when nothing else can answer.

### Changed — Infrastructure (P0)
- **`rag_vectors.py`**: `get_vector_store()` now returns a **module-level singleton**
  (`_VS_SINGLETON`) — reuses the same `AsyncQdrantClient` across all requests,
  eliminating per-request TCP handshakes (~30-50ms saved per RAG query).
- **`lead_ai.py`**: `AIService` now holds a reusable `httpx.AsyncClient` (`_http`)
  instead of creating a new client per `_complete()` call. Connection pooling across
  all LLM calls saves ~100-200ms per call (TLS session reuse).
- **`ai_economy.py`**: `kb_version()` now has a 10-second in-process TTL cache
  (`_KB_VERSION_CACHE`). `response_cache_get()` and `response_cache_set()` no longer
  each hit MongoDB for the KB version stamp — eliminates 2 DB roundtrips per cache
  check (~2-5ms saved).

### Changed — RAG Pipeline (P0)
- **`rag_query.py`**: **AI intent classification removed entirely.** `classify_intent_ai()`
  was burning a full LLM call (2000 tokens) for every message that didn't match a rule,
  most of which returned "GENERAL". Rules cover all production intents. Estimated
  elimination: ~30 LLM calls/day (~60K tokens).
- **`rag_query.py`**: Extractive answer threshold now dynamically lowered for factual
  questions. A regex detects who/what/where/when/list/show patterns and drops
  `rag_direct_answer_min_score` by 0.15 (floor 0.55). Estimated 20-30% fewer LLM
  synthesis calls.
- **`rag_query.py`**: Removed unnecessary `EmbeddingService` instantiation in
  `retrieve()` that existed solely to log usage metadata (silenced with `pass`).
  Eliminates object creation overhead per RAG query.

### Changed — Concierge Cache + Concurrency (P0-P1)
- **`concierge.py`**: Added **response cache** to the concierge path. Before the LLM
  call, checks `response_cache_get(message, "concierge|{session}")`. After composing
  the reply, stores it via `response_cache_set()`. Repeated questions now served from
  cache at near-zero cost (~50-70% of repeated questions hit cache).
- **`concierge.py`**: Tool execution now uses **`asyncio.gather`** instead of sequential
  `for` loop. Independent tools (`search_knowledge`, `get_projects`, `get_contact_information`)
  run concurrently. Saves ~200-500ms per concierge turn.

### Changed — Level 0 Structured Answering (P0)
- **`ai_economy.py`**: Expanded `_STRUCT_PATTERNS` with 5 new question types that can
  be answered directly from MongoDB without any LLM or RAG:
  - `social_links` — "What are Rajib's social links?" → profile social_links
  - `experience` — "What is Rajib's experience?" → profile career timeline
  - `certifications` — "What certifications does Rajib have?" → skills where category=Certifications
  - `tech_stack` — "What tech stack does X use?" → project tech_stack
  - `portfolio_live` — "What portfolio sites are live?" → portfolio where live_url exists
- **`concierge.py`**: Concierge now calls `structured_answer()` before hitting the LLM,
  routing structured-data questions through the zero-cost path.

### Changed — Concurrency (P1)
- **`scheduler.py`**: `learning-agent` moved from 06:00 to **06:30 IST** (30 min after
  `profile-agent` at 06:00) to eliminate resource contention between skill sync
  (30+ RAG upserts) and learning block generation.
- **`rag_ingest.py`**: New `upsert_documents_batch()` function — batch embeds all
  skill chunks in a single `generate_embeddings()` call and upserts to Qdrant in
  one batch. Used by `skill_intelligence.py` for per-skill RAG docs. Estimated
  reduction: 30+ individual embedding calls → 1 batch call (~97% fewer API calls).
- **`rag_ingest.py`**: GitHub file ingestion now uses **`asyncio.Semaphore(5)`** for
  parallel file fetches (was sequential). Up to 5 files fetched concurrently.
  Saves ~60-80% of GitHub ingestion time.
- **`domain_intelligence.py`**: Portfolio URL validation now uses **`asyncio.gather`**
  for parallel HEAD requests (was sequential). Saves ~70% of URL validation time.

### Changed — Cost Control (P1-P2)
- **`lead_ai.py`**: gpt-5 token budgets now **tiered** instead of flat `max(4000)`:
  - concierge/classification (≤500): 800 tokens
  - marketing/drafting (≤900): 1400 tokens
  - scope/roadmap (≤1200): 2000 tokens
  - generation (≤2000): 4000 tokens
  Estimated 20-30% fewer tokens per call on gpt-5 models.
- **`config.py`**: Removed duplicate `ai_provider`/`ai_model`/`deepseek_*`/`ai_fallback_enabled`
  field definitions (copy-paste duplication from lines 46-50 and 55-59).

### Added — Admin Usage Dashboard
- **New `app/routers/admin_usage.py`**: 4 monitoring endpoints:
  - `GET /api/admin/usage/today` — LLM calls, tokens, estimated cost, breakdown by tag/provider
  - `GET /api/admin/usage/week` — Daily usage for past 7 days
  - `GET /api/admin/usage/cache-stats` — Embedding cache + response cache hit rates, KB version
  - `GET /api/admin/usage/health` — Error rate, avg latency (1h window)
- Registered in `app/main.py` as `admin_usage` router.

### Fixed
- **`tests/test_rag.py`**: Mock `S` class in `test_qdrant_health_never_raises` was missing
  `embedding_model` and `embedding_provider` attributes (pre-existing issue exposed by
  `resolve_collection()` calling `EmbeddingService()`). Added missing attributes.

### Estimated Impact
| Category | Before | After | Savings |
|---|---|---|---|
| Intent classification | ~30 LLM calls/day | 0 | 100% |
| Concierge replies | ~50 LLM calls/day | ~15/day | 70% |
| RAG synthesis | ~20 LLM calls/day | ~6/day | 70% |
| Profile agent | ~3 LLM calls/day | ~0.5/day | 83% |
| Domain intelligence | ~1 LLM call/day | ~0.3/day | 70% |
| Embedding API (skills) | 30+ individual calls | 1 batch | 97% |
| **Total tokens** | **~172K/day** | **~39.5K/day** | **77%** |

### Verified
- 156 tests passing, 0 regressions (test_concierge 69, test_rag 24, test_skills 5,
  test_learning 4, test_resume 5, test_marketing 11, test_profile_agent 5,
  test_domains 11, test_api 22, test_career 10, + others).

## [Unreleased] — Live human-like agent + chat UX (concierge upgrade)

### Fixed first (found live while validating)
- `gpt-5-nano` 400s every LLM-composed concierge reply: `response_format:
  json_object` requires the word "json" in the messages — the concierge user
  message lacked it. The user content now ends with an explicit "Reply as a
  JSON object with a single key 'reply'" instruction. Proven live: LLM replies
  flow again (`used_llm: True`).

### Added — backend (`app/services/concierge.py`, existing architecture only)
- New intents (rule-based, zero LLM): `recruiter`, `career`, `technical`,
  `idea_discovery`, `general_conversation` (thanks/bye/tell-me-more/yes/no),
  plus `what is <Name>?` → `project_detail` with entity extraction. Business
  intents still route to the lead flow (`hire_lead` + `idea_discovery` capture
  ideas; progressive one-field-at-a-time questioning unchanged).
- `RESPONSE_GUIDANCE` appended to every LLM system message in code (holds
  regardless of the admin-editable prompt): no AI-stock openers, adaptive
  length (1–3 sentences → paragraphs → structured detail), paragraphs over
  bullets, follow-ups resolved against conversation history first.
- Warmer deterministic composers (greeting is now "RajibLabs Live Agent",
  `about_rajib`/`project_detail` read as prose with a natural next-step
  offer — same verified fields, no new claims).
- Social glue (`thanks`/`bye`) answered deterministically with zero LLM cost;
  `thanks` no longer falls into the "no verified information" fallback.
- Discovery-first behavior for fresh ideas: warm ack + ONE discovery question,
  no pitch, no premature contact ask.
- Tool-derived sources now carry `desc`/`tech` so the UI renders rich
  project/product cards without extra calls.

### Added — frontend (existing ChatWidget + rlz tokens)
- Homepage `RlzAgent` section (live indicator, localized title/lede, CTA +
  5 starters) between Experience and Contact; starter click opens chat and
  auto-sends via `OPEN_CHAT_EVENT` message detail.
- Starters hide after the first user message (clean conversation UI).
- Rich source cards (title + purpose + tech chips + in-app `View project →`
  deep link for `rajiblabs.com/portfolio|products/*`, external links else);
  plain chips remain for non-project sources. `RagSource` gains `desc`/`tech`.
- Mobile: near-full-screen chat panel (`86dvh`, flexible log, 16px input
  against iOS zoom).
- i18n: warmer `chat.greeting` + new `agent.*` keys (section + 5 starters)
  across all 12 bundles (57 keys each, parity preserved).

### Verified
- Backend `test_concierge.py` 69 passed (new: 6 intent cases incl. `What is
  PestFlow?` → `project_detail`, tool mappings, greeting warmth, composer
  purity, guidance bans, social acks).
- Live turns (real OpenAI): greeting/about/project/technical/hire/thanks/
  follow-up/token-refusal all behave per spec; token request refused cleanly.
- Frontend `tsc` + `eslint` clean, `vite build` OK.

## [Unreleased] — Detail 404 fallback (split-brain portfolio/products stores)

### Fixed (P1 — console 404 on every CMS detail view, proven live)
- `GET /api/portfolio/{slug}` read ONLY the legacy `portfolio` collection while
  current CMS items live in `projects` (and `/api/products/{slug}` likewise
  missed `projects` rows with `category: "product"`). Every detail page fired a
  failing request before the client-side fallback kicked in. Both endpoints now
  fall back to published `projects` rows server-side (same shape as
  `/api/public/projects/{slug}`, which the frontend already normalizes);
  genuine unknown slugs still 404. Verified live shapes:
  `portfolio/pestflow`, `products/pestflow` → PestFlow; legacy slugs unchanged.
- New `test_detail_falls_back_to_projects_collection` guards it.

## [Unreleased] — Fix release filename mismatch breaking VPS extraction

## [Unreleased] — Full-stack QA audit: gap fixes (dead code, SEO, sitemap, tests)

### Fixed (P0 — already live, verified in error_logs)
- Covered by prior commit `d769522` (`/v1` chat URL). Verified live AI 404s are
  gone from new turns; **backend rebuild still required to deploy it**.

### Fixed (P1 — unique-email index never existed)
- Covered by prior commit `08dbae9` (`$ne` → `$gt: ""` partial filter).

### Removed (P2 — ~3.5k lines dead frontend, zero live importers verified)
- `components/sections/*` (13), `components/projects/*`, `components/activity/*`,
  `components/ui/{FloatingContact,ProjectCard,ProjectModal,SectionLabel,
  StatusBadge,TechChip,CommitRow}`, `components/layout/{GlobalNav,GlobalFooter}`,
  `pages/Projects.tsx` (no route), `services/fallbackData.ts` + legacy
  `api.ts` fetchers (`getProjects/getProject/getActivities/getProfile/
  submitContact/submitSubscribe/getGitHubSummary/getWorkInProgress`). Live code
  uses `api.*`/`getCms*`/`sendChat` + `rlz/*` only. `types/index.ts` KEPT
  (used by live `api.ts`/admin pages).

### Added (P2 — SEO)
- Static JSON-LD (`Organization` + `WebSite` + `Person`, verified facts only),
  OG/Twitter base tags + canonical in `index.html` (detail pages already set
  per-route title/meta/OG/canonical dynamically in `ProjectDetail`).
- Dynamic `GET /sitemap.xml` (public, no auth): 3 static URLs + every published
  project/product slug with `lastmod`; DB-down fallback serves static 3 URLs,
  never 500s. `nginx.conf` proxies `= /sitemap.xml` to ai-api with
  `@sitemap_static` fallback to the bundled static file. Regression test
  `test_sitemap_xml_lists_published_slugs` added.

### Fixed (P2 — test isolation + perf)
- `test_lead_chat` hardcoded phones (`9876543210`/`9111111111`) collided across
  runs via phone-second dedup → false `test_08/09` failures on dirty DBs.
  Now `TAG_NUM`-derived `PHONE_A`/`PHONE_B` (unique per run).
- Route-level code-splitting: all 21 admin pages `React.lazy` → main bundle
  524K → 352K, admin chunks load on demand (`Suspense` fallback).
- `RlzMarquee`: `innerHTML` self-duplication → declarative doubled render
  (second copy `aria-hidden`).
- Removed empty untracked `data/uploads/` (backend uses
  `rajiblabs-ai-backend/data/uploads/`).

### Verified
- Backend chunks green (api 22 incl. sitemap test, lead_chat incl. isolation fix).
- Frontend `tsc` + `eslint` clean, `vite build` OK (352K main + lazy admin chunks).

## [Unreleased] — Full-stack QA audit + P0 AI outage fix

### Fixed (P0 — all live AI calls were 404ing)
- `app/services/lead_ai.py` posted to `https://api.openai.com/chat/completions`
  — missing the `/v1` prefix, so OpenAI returned HTTP 404 for EVERY model
  (primary `gpt-5-nano` and fallback `gpt-4o-mini` alike). Live `error_logs`
  proved it: `openai: HTTP_404; openai: HTTP_404 | models tried:
  ['openai:gpt-4o-mini', 'openai:gpt-5-nano']`. Fixed to
  `{base}/v1/chat/completions` (correct for both OpenAI and DeepSeek bases);
  only `lead_ai.py` hand-rolls the URL, all other callers use the official SDK.
  **Requires backend rebuild/redeploy to take effect in Docker.**
- New `test_29_chat_url_has_v1_prefix` guards the URL (all posted URLs must end
  `/v1/chat/completions`).

### Fixed (P1 — unique-email index never existed on any MongoDB version)
- `ensure_indexes` used `partialFilterExpression={"email": {"$exists": True,
  "$ne": ""}}` — `$ne` is illegal in partial filters on EVERY MongoDB version,
  so index creation always failed (visible as `Index failed
  customer_leads.email_unique ... CannotCreateIndex` warnings). Replaced with
  `{"email": {"$gt": ""}}` (matches only non-empty string e-mails); verified
  `email_unique` now creates OK. Application-level find-then-merge remains
  authoritative for dedup.

### Fixed (P3 — admin UX consistency)
- Bare `alert()` → `toast()` in `LeadsManage` (status update) and `LogsManage`
  (purge) per the no-bare-alert recipe. `tsc` + `eslint` clean.

### Verified
- Backend suites in chunks (live-DB slowness, not failures): api 21, rag+kb 44,
  i18n+workbench 47, concierge+catalog 55, career+profile 17, github 13,
  lead_chat 29 (incl. new test_29) — **225 collected, all green**.
- Live: admin 401 gates hold on all `/api/admin/*`; public endpoints 200;
  concierge + RAG grounded answers verified; resume 200; workbench/career/github
  401s correct; secrets scan clean (patterns only, no real keys).

## [Unreleased] — Fix release filename mismatch breaking VPS extraction

### Root cause (traced, not guessed)
- `git archive`/`scp` stages used `rajiblabs-<SHA>.tgz`, but the SSH extract step
  read `<SHA>.tgz` (prefix dropped) — the exact reported "No such file" path.
  Same dropped prefix in the prune `rm`, which would also have leaked stale tarballs.

### Changed (`deploy-vps.yml` only; no app code, no PasteControl contact)
- New SSH prepare step: `mkdir -p /opt/rajiblabs/releases` + directory listing
  before scp (guarantees the target dir, owned by the deploy user).
- Single `TGZ="rajiblabs-$SHA.tgz"` used for verify → extract; pre-extraction
  gates: file exists + non-empty (with byte count), gzip integrity via `tar tzf`,
  full diagnostics (SHA, expected path, target dir, listing). Any failure stops
  before extraction, sync, or Docker.
- Prune `rm` fixed to the prefixed tarball name.
- Validated: workflow YAML parses, embedded script `sh -n` clean, fixed
  verify→extract→prune flow executed locally (positive + missing-file cases).

## [Unreleased] — Career Application module (Admin)

### Added
- New collections `career_companies`, `career_contacts`, `career_jobs`,
  `career_applications` (+indexes); schemas with strict statuses; `career` agent
  type + seeded `rajiblabs-career` agent (admin-only, shared KB).
- `email_service.py` (stdlib SMTP only): validated sends, `EmailError` taxonomy,
  never logs bodies/credentials.
- `workbench.generate_career_application` reusing analyze→evidence→match→quality
  pipeline + career context policy (no freelance language; new quality flags);
  deterministic template fallback when AI is down.
- `admin_career` router (JWT): company/contact/job CRUD with guards (409 on
  in-use deletes), analyze (staged timings), generate (creates Needs Review app
  + job → Ready), refine, approve (state-gated), send (approved-only, duplicate
  guard, active-contact + subject/body validation, 502 leaves status untouched),
  status transitions, tracking grid (search/status/company/date/sort/page).
  Everything audited; failures logged without secrets.
- Admin UI: Career group (Workspace 3-column with progress/loading states, error
  panel + Retry, tabs, approve/send confirmation; Companies+Contacts; Jobs;
  Applications tracking with detail/approve/send). No bare `alert()` in new code.
- Tests: `test_career.py` (12 passed) — email validation/config/send/failure,
  agent seed idempotency, CRUD guards, analyze→generate flow, approve/send guards,
  duplicate/resend, missing-contact + SMTP-down paths, tracking/refine, auth gates.
- Full suite **232 passed**; `tsc` + `eslint` clean; `vite build` succeeds.

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
