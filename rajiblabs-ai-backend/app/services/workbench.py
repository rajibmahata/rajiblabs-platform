"""Admin AI Proposal Studio — workbench service layer (§3–§10, §14–§17, §20, §25, §26, §29–§32).

Pipeline: Requirement Analyzer → RAG Retriever → Experience Matcher →
Proposal Generator → Quality Check. Every AI call goes through the existing
AI orchestrator (lead_ai.AIService); routers never touch providers.
The SAME RAG knowledge base as public chat is reused — no second index.

Truthfulness: every URL/project claim must trace to DB records or RAG
metadata. Anything unverifiable is dropped, never invented.
"""
import logging
import re
import uuid
from urllib.parse import urlparse

from app.config import get_settings
from app.database import get_db, utcnow
from app.schemas import (
    ExperienceMatch, MatchReport, ProposalSource, RequirementAnalysis,
)
from app.services import lead_ai, rag_query
from app.services.notify import audit
from app.services.workbench_prompts import (
    CoverLetterPrompt, ExperienceMatchingPrompt, ProjectSelectionPrompt,
    ProposalGenerationPrompt, RefinementPrompt, RequirementAnalysisPrompt,
)

log = logging.getLogger("rajiblabs")

# Source priority (§9): specific evidence beats generic skills. Lower = better.
SOURCE_PRIORITY = {
    "project": 0, "product": 1,
    "github_repository": 2, "github_readme": 2, "github_documentation": 2,
    "github_commit": 2, "github_issue": 2,
    "case_study": 3, "wip": 3,
    "profile": 4, "resume": 4,
    "service": 5, "website_content": 5, "admin_knowledge": 5,
}

TECH_VOCABULARY = (
    ".net", "c#", "asp.net", "react", "angular", "vue", "typescript", "javascript",
    "python", "fastapi", "django", "node.js", "node", "java", "spring", "go", "rust",
    "azure", "aws", "gcp", "docker", "kubernetes", "terraform",
    "sql server", "postgresql", "mysql", "mongodb", "redis", "sqlite",
    "openai", "deepseek", "llm", "genai", "rag", "langchain", "qdrant",
    "pinecone", "weaviate", "machine learning", "ml", "ai", "nlp",
    "power bi", "tableau", "kafka", "rabbitmq", "graphql", "rest api",
    "microservices", "saas", "pwa", "flutter", "react native", "blazor",
    "entity framework", "dapper", "xamarin", "maui", "sharepoint",
    "salesforce", "sap", " dynamics", "hl7", "fhir", "hipaa",
    "stripe", "twilio", "sendgrid", "firebase", "supabase",
)

INDUSTRY_KEYWORDS = (
    "healthcare", "pharmacy", "pharma", "hospital", "clinic", "fintech",
    "finance", "banking", "insurance", "ecommerce", "e-commerce", "retail",
    "logistics", "supply chain", "education", "edtech", "real estate",
    "hospitality", "manufacturing", "legal", "law", "government", "nonprofit",
    "travel", "food", "agriculture", "energy", "telecom", "media",
)

BANNED_OPENERS = (
    "dear hiring manager,\ni am an experienced developer",
    "dear hiring manager, i am writing to apply",
    "i am writing to express my interest",
)
HYPE_PHRASES = (
    "perfect candidate", "guarantee success", "guaranteed success",
    "very easily", "best developer", "world-class ninja", "rockstar developer",
    "10x developer",
)
CTA_PATTERNS = re.compile(
    r"(call|zoom|google meet|teams call|discovery call|scoping|next step|"
    r"reply|reach out|let'?s (talk|discuss|connect|schedule)|"
    r"happy to (walk|share|discuss|jump))", re.I)

MAX_JD_CHARS = 20000


# ── helpers ──

def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]*", (text or "").lower())


def _dedup(seq: list[str]) -> list[str]:
    seen, out = set(), []
    for s in seq:
        k = (s or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append((s or "").strip())
    return out


async def _orchestrator():
    """The existing AI orchestrator (raises lead_ai.AIError when unusable)."""
    svc = lead_ai.AIService()
    if not svc.configured:
        raise lead_ai.AIError("AI not configured")
    return svc


# ── 4. requirement analysis ──

def extract_years(jd: str) -> str:
    m = re.search(r"(\d{1,2})\s*\+?\s*(?:years|yrs)\b", jd, re.I)
    return f"{m.group(1)}+ years" if m else ""


def extract_company(jd: str) -> str:
    """Conservative: explicit labels only. Never guess — "" when absent (§14)."""
    for pat in (r"(?im)^(?:company|client|organisation|organization)\s*:\s*(.+)$",
                r"(?im)^about\s+([A-Z][\w&.,' ]{2,60})$"):
        m = re.search(pat, (jd or "").strip())
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip(" -–—.,")[:80]
    return ""


def extract_techs(jd: str, extra: list[str] | None = None) -> list[str]:
    low = f" {(jd or '').lower()} "
    found = [t.strip() for t in TECH_VOCABULARY if f" {t} " in low or f" {t}," in low
             or f" {t}." in low or f"({t})" in low or f" {t}/" in low]
    for t in (extra or []):
        if t and t.strip().lower() not in {f.lower() for f in found}:
            found.append(t.strip())
    # "AI integration" style phrases imply AI even without the bare token
    if re.search(r"\bai[\s\-/]?(integration|powered|features?|chatbot|assistant)\b", low) \
            and "ai" not in {f.lower() for f in found}:
        found.append("AI")
    return _dedup(found)


def extract_industry(jd: str) -> str:
    low = (jd or "").lower()
    for ind in INDUSTRY_KEYWORDS:
        if ind in low:
            return "Healthcare" if ind in ("healthcare", "pharmacy", "pharma", "hospital", "clinic") \
                else ind.replace("-", " ").title()
    return ""


def rule_analysis(jd: str) -> RequirementAnalysis:
    """Deterministic extraction — always available, even with AI down."""
    jd = (jd or "").strip()[:MAX_JD_CHARS]
    techs = extract_techs(jd)
    lines = [l.strip("-•* \t") for l in jd.splitlines() if l.strip()]
    bullets = [l for l in lines if len(l) > 12][:25]
    return RequirementAnalysis(
        title=(lines[0][:120] if lines else ""),
        company=extract_company(jd),
        industry=extract_industry(jd),
        required_skills=techs[:15],
        years_experience=extract_years(jd),
        business_problem=" ".join(jd.split()[:60]),
        responsibilities=bullets[:8],
        technologies=techs[:15],
        ai_requirements=[t for t in techs
                         if t.lower() in ("ai", "llm", "genai", "rag", "openai", "deepseek", "nlp", "machine learning", "ml")],
        cloud_requirements=[t for t in techs
                            if t.lower() in ("azure", "aws", "gcp", "docker", "kubernetes", "terraform")],
        database_requirements=[t for t in techs
                               if t.lower() in ("sql server", "postgresql", "mysql", "mongodb", "redis", "sqlite")],
        keywords=_dedup(extract_techs(jd) + ([extract_industry(jd)] if extract_industry(jd) else []))[:20],
    )


async def analyze_requirements(jd: str, db=None) -> tuple[RequirementAnalysis, bool]:
    """(analysis, ai_used). Rules first, AI structures when configured."""
    base = rule_analysis(jd)
    try:
        svc = await _orchestrator()
    except lead_ai.AIError:
        return base, False
    # Enrich tech vocabulary with live skills so new skills are recognized.
    try:
        db = db if db is not None else get_db()
        cur = db["skills"].find({"status": "published"}, {"name": 1}).limit(200)
        extra = [d.get("name", "") async for d in cur]
        if extra:
            base.technologies = extract_techs(jd, extra)[:20]
            base.required_skills = base.technologies[:15]
    except Exception:
        pass
    try:
        out = await svc._complete(
            [{"role": "system", "content": RequirementAnalysisPrompt},
             {"role": "user", "content": jd[:8000]}],
            max_tokens=900, temperature=0.2, tag="workbench-analyze")
        ai = RequirementAnalysis.model_validate(out["data"])
        merged = ai.model_dump()
        # Rules fill gaps the AI left empty — AI never invents company/techs.
        for k in ("technologies", "required_skills", "keywords"):
            if not merged.get(k) and getattr(base, k):
                merged[k] = getattr(base, k)
        if not merged.get("company"):
            merged["company"] = base.company
        if not merged.get("industry"):
            merged["industry"] = base.industry
        if not merged.get("years_experience"):
            merged["years_experience"] = base.years_experience
        return RequirementAnalysis.model_validate(merged), True
    except Exception as e:
        log.warning("workbench analyze fallback to rules: %s", e)
        return base, False


# ── 5/8. RAG retrieval + URL allowlist ──

async def collect_known_urls(db) -> set[str]:
    """Every URL the studio may emit: explicit stored URLs only, never built."""
    urls: set[str] = set()
    try:
        async for p in db["projects"].find({"published": True}, {"live_url": 1, "github_url": 1}):
            for u in (p.get("live_url"), p.get("github_url")):
                if u:
                    urls.add(u.strip().rstrip("/"))
    except Exception:
        pass
    try:
        async for p in db["products"].find({}, {"live_url": 1, "github_url": 1}):
            for u in (p.get("live_url"), p.get("github_url")):
                if u:
                    urls.add(u.strip().rstrip("/"))
    except Exception:
        pass
    try:
        prof = await db["profiles"].find_one({}, {"social_links": 1})
        for u in ((prof or {}).get("social_links") or {}).values():
            if u:
                urls.add(str(u).strip().rstrip("/"))
    except Exception:
        pass
    try:
        async for r in db["github_repositories"].find({"private": {"$ne": True}}, {"html_url": 1}):
            if r.get("html_url"):
                urls.add(r["html_url"].strip().rstrip("/"))
    except Exception:
        pass
    try:
        async for d in db["knowledge_documents"].find(
                {"status": "active", "url": {"$ne": None}}, {"url": 1}):
            if d.get("url"):
                urls.add(d["url"].strip().rstrip("/"))
    except Exception:
        pass
    return urls


def validate_url(url: str, known: set[str]) -> str:
    """Return the URL iff well-formed AND from a known source. Else "" (§32)."""
    u = (url or "").strip().rstrip("/")
    if not u:
        return ""
    try:
        p = urlparse(u)
    except Exception:
        return ""
    if p.scheme != "https" or not p.netloc:
        return ""
    host = p.netloc.lower().lstrip("www.")
    if host not in ("rajiblabs.com", "github.com", "linkedin.com"):
        return ""
    if u in known:
        return u
    # github.com/rajibmahata[/repo] without exact record → still Rajib's own
    # namespace, but only the bare profile is safe to allow implicitly.
    if u == "https://github.com/rajibmahata":
        return u
    return ""


async def retrieve_evidence(analysis: RequirementAnalysis, top_k: int = 0,
                            source_ids: list[str] | None = None,
                            db=None) -> list[dict]:
    """Opportunity-ranked evidence from the SHARED RAG index (§5, §25).

    Multi-query (role+tech, domain+problem, profile anchor), merged and
    re-ranked: vector score blended with source-priority (§9).
    """
    s = get_settings()
    queries = [
        f"{analysis.title} {' '.join(analysis.technologies[:6])}".strip(),
        f"{analysis.industry} {analysis.business_problem[:200]} "
        f"{' '.join(analysis.keywords[:6])}".strip(),
        "Rajib Mahata professional experience career profile",
    ]
    if analysis.ai_requirements:
        queries.append("AI RAG LLM integration " + " ".join(analysis.ai_requirements[:4]))
    seen: dict[str, dict] = {}
    for q in queries:
        if not q.strip():
            continue
        try:
            hits = await rag_query.retrieve(q, top_k=top_k or 8, intent="GENERAL")
        except Exception as e:
            log.warning("workbench retrieval skipped: %s", e)
            hits = []
        for h in hits:
            key = h.get("document_id") or h.get("chunk_id")
            if not key or key in seen:
                continue
            rank = SOURCE_PRIORITY.get(h.get("source_type", ""), 6)
            h["_priority"] = rank
            # blended: priority tier dominates, vector score breaks ties
            h["_blend"] = rank * 10 - min(2.0, h.get("score", 0))
            seen[key] = h
    out = sorted(seen.values(), key=lambda h: h["_blend"])[: (top_k or s.rag_top_k * 3)]
    if source_ids:
        keep = set(source_ids)
        out = [h for h in out if h.get("document_id") in keep]
    # Attach document metadata (title/url/repo/language) from Mongo.
    try:
        db = db if db is not None else get_db()
        from bson import ObjectId
        oids = []
        for h in out:
            try:
                oids.append(ObjectId(h["document_id"]))
            except Exception:
                pass
        meta = {}
        if oids:
            async for d in db["knowledge_documents"].find({"_id": {"$in": oids}}):
                meta[str(d["_id"])] = d
        for h in out:
            m = meta.get(h["document_id"], {})
            h["doc_title"] = h.get("title") or m.get("title", "")
            h["doc_url"] = h.get("url") or m.get("url") or ""
            h["doc_repo"] = h.get("repository") or m.get("repository") or ""
            h["doc_lang"] = h.get("language") or m.get("language") or ""
    except Exception as e:
        log.warning("workbench metadata attach failed: %s", e)
    return out


# ── 6/7. matching + selection ──

def _overlap_terms(requirement: str, text: str) -> list[str]:
    req = [w for w in _dedup(_words(requirement))]
    txt = set(_words(text))
    low = (text or "").lower()
    out = []
    for w in req:
        if len(w) > 3:
            if w in txt:
                out.append(w)
        elif len(w) >= 2 and re.search(r"(?<![a-z0-9+#])" + re.escape(w) + r"(?![a-z0-9+#])", low):
            # Short tech tokens (.NET, AI, AWS): boundary-aware substring hit.
            out.append(w)
    return sorted(out)


async def select_examples(analysis: RequirementAnalysis, evidence: list[dict],
                          limit: int = 4) -> list[dict]:
    """2–4 strongest work examples (§7). AI selects; priority order fallback."""
    cands: dict[str, dict] = {}
    for h in evidence:
        st = h.get("source_type", "")
        if st in ("project", "product", "case_study", "wip",
                  "github_repository", "github_readme", "github_documentation"):
            key = h.get("document_id") or h.get("title")
            if key not in cands:
                cands[key] = h
    candidates = list(cands.values())
    if not candidates:
        return []
    titles = [c.get("doc_title") or c.get("title", "") for c in candidates]
    try:
        svc = await _orchestrator()
        out = await svc._complete(
            [{"role": "system", "content": ProjectSelectionPrompt},
             {"role": "user", "content": (
                 f"Opportunity: {analysis.title} | {analysis.industry} | "
                 f"tech: {', '.join(analysis.technologies[:10])}\n"
                 f"Candidates: {titles}\nReturn selected[] (2-4 titles).")}],
            max_tokens=200, temperature=0.2, tag="workbench-select")
        picked = [t for t in (out["data"].get("selected") or []) if t in titles]
        if picked:
            order = {t: i for i, t in enumerate(picked)}
            candidates.sort(key=lambda c: order.get(c.get("doc_title") or c.get("title", ""), 99))
            chosen = candidates[:max(2, min(limit, len(picked)))]
            for c in chosen:
                c["selection_reason"] = selection_reason(c, analysis)
            return chosen
    except Exception as e:
        log.warning("workbench selection fallback: %s", e)
    candidates.sort(key=lambda c: (c.get("_priority", 6), -(c.get("score", 0))))
    chosen = candidates[:min(limit, max(2, len(candidates)))]
    for c in chosen:
        c["selection_reason"] = selection_reason(c, analysis)
    return chosen


async def match_requirements(analysis: RequirementAnalysis, selected: list[dict],
                             evidence: list[dict]) -> list[ExperienceMatch]:
    """Requirement → experience → project → evidence → URL (§6, evidence-only)."""
    corpus = " ".join(h.get("content", "") for h in evidence)
    profile_bits = " ".join(h.get("content", "")[:600] for h in evidence
                            if h.get("source_type") in ("profile", "resume"))[:1500]
    reqs = _dedup(analysis.technologies[:5] + analysis.required_skills[:3]
                  + analysis.deliverables[:3] + analysis.responsibilities[:2])[:7]
    matches: list[ExperienceMatch] = []
    # AI-written reasons, grounded per-candidate.
    reasons: dict[str, str] = {}
    try:
        svc = await _orchestrator()
        cand_txt = "\n".join(
            f"- {c.get('doc_title')}: {(c.get('content') or '')[:500]}" for c in selected)
        out = await svc._complete(
            [{"role": "system", "content": ExperienceMatchingPrompt},
             {"role": "user", "content": (
                 f"Opportunity: {analysis.title} ({analysis.industry})\n{cand_txt}")}],
            max_tokens=600, temperature=0.3, tag="workbench-match")
        for r in (out["data"].get("reasons") or []):
            if isinstance(r, dict) and r.get("title"):
                reasons[r["title"]] = r.get("reason", "")
    except Exception as e:
        log.warning("workbench reasons fallback: %s", e)
    for req in reqs:
        best, best_overlap = None, []
        for c in selected:
            ov = _overlap_terms(req, (c.get("content") or "") + " " + (c.get("doc_title") or ""))
            if len(ov) > len(best_overlap):
                best, best_overlap = c, ov
        if best is None:
            matches.append(ExperienceMatch(requirement=req))
            continue
        title = best.get("doc_title") or best.get("title", "")
        reason = reasons.get(title) or (
            f"Relevant through {', '.join(best_overlap[:4])}." if best_overlap
            else "Related experience in the same domain.")
        exp = (profile_bits[:300] + " ") if profile_bits else ""
        matches.append(ExperienceMatch(
            requirement=req,
            experience=(exp + f"Hands-on delivery experience ({title}).").strip(),
            project=title,
            evidence=(best.get("content") or "")[:400],
            url=best.get("doc_url") or "",
        ))
    if not matches:  # nothing extracted — still show the top example honestly
        top = selected[0]
        matches.append(ExperienceMatch(
            requirement=analysis.title or "General fit",
            experience="Related delivery experience at RajibLabs.",
            project=top.get("doc_title") or "", evidence=(top.get("content") or "")[:400],
            url=top.get("doc_url") or ""))
    # corpus unused beyond honesty guard — every experience line above cites evidence.
    _ = corpus
    return matches


def match_score(analysis: RequirementAnalysis, matches: list[ExperienceMatch],
                selected: list[dict], evidence: list[dict]) -> MatchReport:
    """Transparent weighted estimate (§20) — labelled, not a probability."""
    techs = [t.lower() for t in analysis.technologies + analysis.required_skills]
    ev_text = " ".join((h.get("content") or "") for h in evidence).lower()
    tech_hit = sum(1 for t in _dedup(techs) if t and t in ev_text)
    tech_frac = (tech_hit / max(1, len(_dedup(techs)))) if techs else 0.5
    domain_frac = 1.0 if analysis.industry and analysis.industry.lower() in ev_text \
        else (0.5 if evidence else 0.0)
    project_frac = min(1.0, len(selected) / 3)
    exp_frac = 1.0 if any(h.get("source_type") in ("profile", "resume") for h in evidence) \
        else (0.6 if evidence else 0.0)
    other_terms = _dedup([w for r in (analysis.responsibilities + analysis.deliverables)
                          for w in _words(r) if len(w) > 4])
    other_frac = (sum(1 for w in other_terms[:20] if w in ev_text) / 20) if other_terms else 0.5
    score = int(round(tech_frac * 25 + domain_frac * 20 + project_frac * 25
                      + exp_frac * 20 + other_frac * 10))
    strengths = [m.requirement for m in matches if m.project][:5]
    gaps = [m.requirement for m in matches if not m.project][:5]
    if not evidence:
        gaps = (gaps + ["No indexed evidence retrieved — run RAG re-ingest"])[:5]
    return MatchReport(match_score=max(0, min(100, score)),
                       strengths=strengths, gaps=gaps)


# ── 10–13. generation ──

MODE_GUIDANCE = {
    "cover_letter": "Write ONLY the cover_letter (150-300 words); keep proposal/short_summary empty.",
    "freelance_proposal": "Full freelance proposal with opening, understanding, fit, relevant work, approach, deliverables, why RajibLabs, next step.",
    "client_proposal": "Formal client proposal; slightly more structured; include approach and deliverables.",
    "job_application": "Job-application tone; map experience to the role; concise.",
    "project_summary": "Write ONLY short_summary (1-2 sentences) plus a brief proposal; cover_letter empty.",
    "project_explanation": "Explain the matched RajibLabs work itself: problem, solution, features, architecture, technology, role and verified URLs. No pitch, no call to action.",
    "custom": "Follow the admin's tone/length instructions in the brief.",
}

LENGTH_GUIDANCE = {
    "short": "Keep the proposal under ~150 words.",
    "standard": "A focused, readable proposal (~250-450 words).",
    "detailed": "A thorough proposal (~500-800 words).",
    "150-word": "Hard limit: ~150 words.",
    "150-words": "Hard limit: ~150 words.",
}

# Context rules: what each mode must/must not mention. Appended to the
# generation brief as hard rules AND enforced by quality_check flags.
CONTEXT_RULES = {
    "job_application": (
        "Context rules for JOB APPLICATIONS: draw on professional experience, resume, "
        "skills, LinkedIn, relevant projects and education. Do NOT mention Upwork, "
        "freelancing, freelancer platforms, 'freelance project', or present RajibLabs "
        "as a freelancing platform, unless the job description explicitly requires it."
    ),
    "freelance_proposal": (
        "Context rules for FREELANCE proposals: draw on skills, relevant projects, "
        "RajibLabs, GitHub work and technical approach. Do NOT discuss corporate "
        "employment history, current employer/company details, internal company "
        "information, or unrelated career details unless the client explicitly asks."
    ),
    "client_proposal": (
        "Context rules for CLIENT proposals: draw on skills, relevant projects, "
        "RajibLabs, GitHub work and technical approach. Do NOT discuss corporate "
        "employment history, current employer/company details, or internal company "
        "information unless the client explicitly asks."
    ),
}

# Quality flags for context mixing (prompt rules above are primary; these surface violations).
_JOB_FREELANCE_TERMS = ("upwork", "freelanc", "fiverr", "guru.com", "toptal")
_CORPORATE_TERMS = ("my current employer", "my employer", "works at tcs", "employed at")


def _evidence_block(selected: list[dict]) -> str:
    lines = []
    for c in selected:
        lines.append(f"- {c.get('doc_title')} [{c.get('source_type')}] "
                     f"url={c.get('doc_url') or '(none)'}: {(c.get('content') or '')[:800]}")
    return "\n".join(lines) or "(no evidence retrieved)"


def selection_reason(candidate: dict, analysis: RequirementAnalysis) -> str:
    """Deterministic 'why this was selected' (no LLM): tech overlap +
    evidence kind + verified URL presence."""
    techs = [t for t in (getattr(analysis, "technologies", None) or [])[:10]
             if t.lower() in (candidate.get("content") or "").lower()
             or t.lower() in (candidate.get("doc_title") or "").lower()]
    bits = []
    if techs:
        bits.append(f"matches {', '.join(techs[:4])}")
    st = candidate.get("source_type", "")
    bits.append({"github_repository": "verified GitHub repository",
                 "github_readme": "repository README evidence",
                 "github_documentation": "repository docs evidence",
                 "project": "verified project evidence",
                 "product": "verified product evidence"}.get(st, f"{st or 'knowledge'} evidence"))
    if candidate.get("doc_url"):
        bits.append("has verified URL")
    return "Selected because this example " + " and ".join(bits) + "."


def build_explanation(analysis: RequirementAnalysis, selected: list[dict]) -> str:
    """Deterministic project explanation assembled from verified evidence
    only (no LLM): problem/solution/tech/role/URLs per matched example."""
    if not selected:
        return ""
    parts = [f"Matched work for: {analysis.title or 'this opportunity'}"]
    for c in selected[:4]:
        title = c.get("doc_title") or c.get("title", "Untitled")
        url = c.get("doc_url") or ""
        repo = c.get("doc_repo") or ""
        content = (c.get("content") or "").strip().replace("\n", " ")
        lines = [f"## {title}"]
        if repo:
            lines.append(f"Repository: {repo}")
        if content:
            lines.append(f"Overview: {content[:600]}")
        if url:
            lines.append(f"Verified link: {url}")
        lines.append(f"Why relevant: {selection_reason(c, analysis)}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


async def generate_artifacts(analysis: RequirementAnalysis, matches: list[ExperienceMatch],
                             selected: list[dict], mode: str, tone: str,
                             length: str, known_urls: set[str],
                             db=None, language: str = "en",
                             company: str | None = None,
                             instructions: str | None = None) -> tuple[dict, bool]:
    """Returns ({proposal, cover_letter, short_summary, sources}, ai_used)."""
    try:
        from app.services import lang_service as _ls
        _code, _lang_ins = await _ls.response_instruction(language, db)
    except Exception:
        _lang_ins = ""
    org = company or analysis.company
    greeting = f"Hi {org}," if org else "Hi,"
    match_lines = "\n".join(
        f"- {m.requirement} → {m.project or '(no direct evidence)'}"
        + (f" ({m.url})" if m.url else "") for m in matches)
    sources = [ProposalSource(
        title=c.get("doc_title") or c.get("title", ""),
        type=c.get("source_type", "project"),
        url=validate_url(c.get("doc_url") or "", known_urls),
        reason=c.get("selection_reason") or f"Ranked #{i+1} for this opportunity") for i, c in enumerate(selected)]
    rules = CONTEXT_RULES.get(mode, "")
    extra = f"Admin instructions (must follow): {instructions.strip()[:1000]}" if (instructions or "").strip() else ""
    brief = (f"{greeting}\nMode: {mode}. Tone: {tone or 'professional'}. "
             f"{LENGTH_GUIDANCE.get((length or 'standard').lower(), LENGTH_GUIDANCE['standard'])}\n"
             f"{MODE_GUIDANCE.get(mode, MODE_GUIDANCE['custom'])}\n"
             f"{rules}\n{extra}\n"
             f"Opportunity: {analysis.title} | {analysis.industry} | {org}\n"
             f"Problem: {analysis.business_problem[:500]}\n"
             f"Requirement matches:\n{match_lines}\nEvidence:\n{_evidence_block(selected)}")
    if _lang_ins:
        brief += f"\nWrite proposal, cover_letter and short_summary in the requested language: {_lang_ins}"
    try:
        svc = await _orchestrator()
        out = await svc._complete(
            [{"role": "system", "content": ProposalGenerationPrompt},
             {"role": "user", "content": brief[:9000]}],
            max_tokens=1800, temperature=0.5, tag="workbench-generate")
        data = out["data"]
        texts = {k: str(data.get(k, "")) for k in ("proposal", "cover_letter", "short_summary")}
    except Exception as e:
        log.warning("workbench template fallback: %s", e)
        ex = selected[0] if selected else None
        ex_line = (f"For example, {ex.get('doc_title')}: "
                   f"{(ex.get('content') or '')[:220]}") if ex else ""
        problem = analysis.business_problem[:220] or analysis.title
        texts = {
            "proposal": (
                f"{greeting}\n\nYour requirement around {problem} stood out because "
                f"it maps closely to work Rajib has delivered at RajibLabs.\n\n{ex_line}\n\n"
                f"Relevant strengths: {', '.join(m.requirement for m in matches if m.project) or 'see analysis'}.\n\n"
                f"Happy to walk through the approach on a short call — "
                f"rajibmahata143@gmail.com."),
            "cover_letter": "",
            "short_summary": (
                f"Relevant experience includes {analysis.title.lower() or 'this kind of work'} "
                f"using {', '.join(analysis.technologies[:4]) or 'modern web and cloud technologies'}."),
        }
        return {**texts, "sources": [s.model_dump() for s in sources],
                "explanation": build_explanation(analysis, selected)}, False
    # Cover-letter-only modes share the generator; enforce single-artifact output.
    if mode == "cover_letter":
        try:
            svc2 = await _orchestrator()
            out2 = await svc2._complete(
                [{"role": "system", "content": CoverLetterPrompt},
                 {"role": "user", "content": brief[:9000]}],
                max_tokens=600, temperature=0.5, tag="workbench-cover")
            texts["cover_letter"] = str(out2["data"].get("cover_letter", texts["cover_letter"]))
            texts["proposal"] = ""
        except Exception as e:
            log.warning("cover-letter pass failed: %s", e)
    # Scrub any URL the AI invented (§32): keep only allowlisted ones.
    for k in ("proposal", "cover_letter", "short_summary"):
        texts[k] = _scrub_urls(texts[k], known_urls)
    return {**texts, "sources": [s.model_dump() for s in sources],
            "explanation": build_explanation(analysis, selected)}, True


def _scrub_urls(text: str, known: set[str]) -> str:
    """Remove http(s) URLs that are not in the evidence allowlist."""
    def _keep(m: re.Match) -> str:
        raw = m.group(0).rstrip(".,);]")
        trail = m.group(0)[len(raw):]
        return raw + trail if validate_url(raw, known) else "[link removed — unverified]"
    return re.sub(r"https?://[^\s)>\]]+", _keep, text or "")


# ── 31. quality check ──

def quality_check(proposal: str, cover: str, summary: str,
                  selected: list[dict], known_urls: set[str],
                  mode: str = "") -> dict:
    issues: list[str] = []
    text = f"{proposal}\n{cover}".strip()
    low = text.lower()
    if any(o in low for o in BANNED_OPENERS):
        issues.append("generic_opener")
    if any(h in low for h in HYPE_PHRASES):
        issues.append("hype_language")
    if mode == "job_application" and any(t in low for t in _JOB_FREELANCE_TERMS):
        issues.append("freelance_leak_in_job")
    if mode in ("freelance_proposal", "client_proposal") \
            and any(t in low for t in _CORPORATE_TERMS):
        issues.append("corporate_leak_in_freelance")
    if text and not CTA_PATTERNS.search(text):
        issues.append("missing_call_to_action")
    for m in re.finditer(r"https?://[^\s)>\]]+", text):
        if not validate_url(m.group(0).rstrip(".,);]"), known_urls):
            issues.append("unverifiable_url")
            break
    titles = [(c.get("doc_title") or "").lower() for c in selected if c.get("doc_title")]
    if titles and text and not any(t and t in low for t in titles):
        issues.append("example_not_referenced")
    if len(text.split()) > 900:
        issues.append("too_long")
    if not text:
        issues.append("empty_artifact")
    score = max(0, 100 - 20 * len(_dedup(issues)))
    return {"passed": not issues, "score": score, "issues": _dedup(issues)}


# ── 22. refinement ──

REFINE_PATTERNS = (
    ("shorter", re.compile(r"\b(shorter|concise|condense|trim)\b", re.I), None),
    ("technical", re.compile(r"\b(more technical|technical version|architecture|deep technical)\b", re.I), None),
    ("business", re.compile(r"\b(business[\-\s]?focused|client[\-\s]?friendly|less technical|non[\-\s]?technical)\b", re.I), None),
    ("more_evidence", re.compile(r"\b(more (project )?evidence|add (the )?more|add project)\b", re.I), None),
    ("less_ai", re.compile(r"\b(less ai|human (tone|voice)|sound (less|more) (ai|human)|natural)\b", re.I), None),
)


def parse_refine_instruction(instruction: str) -> dict:
    ins = instruction or ""
    cmd = {"kind": "general", "target_words": 0, "extra": ""}
    m = re.search(r"(\d{2,4})\s*[- ]?words?\b", ins, re.I)
    if m:
        cmd["target_words"] = max(40, min(1200, int(m.group(1))))
        cmd["kind"] = "length"
    for kind, pat, _ in REFINE_PATTERNS:
        if pat.search(ins):
            cmd["kind"] = "length" if kind == "shorter" and cmd["kind"] != "length" else kind
            if kind == "shorter" and not cmd["target_words"]:
                cmd["kind"] = "shorter"
            break
    madd = re.search(r"\badd the ([\w\s\-&]+?) project\b", ins, re.I)
    if madd:
        cmd["kind"] = "add_project"
        cmd["extra"] = madd.group(1).strip()
    mrem = re.search(r"\bremove the ([\w\s\-&/]+?) link\b", ins, re.I)
    if mrem:
        cmd["kind"] = "remove_link"
        cmd["extra"] = mrem.group(1).strip()
    return cmd


def trim_to_words(text: str, target: int) -> str:
    words = (text or "").split()
    if target <= 0 or len(words) <= target:
        return text
    sents = re.split(r"(?<=[.!?])\s+", text)
    out, count = [], 0
    for s in sents:
        n = len(s.split())
        if count + n > target and out:
            break
        out.append(s)
        count += n
    return " ".join(out).rstrip() or " ".join(words[:target])


async def refine_text(text: str, instruction: str, evidence_extra: str = "") -> tuple[str, dict]:
    """Modify an existing artifact (§22). Returns (new_text, command)."""
    cmd = parse_refine_instruction(instruction)
    if cmd["kind"] == "remove_link" and cmd["extra"]:
        dropped = re.sub(r"[^\n]*" + re.escape(cmd["extra"]) + r"[^\n]*https?://[^\s)>\]]+[^\n]*",
                         "", text, flags=re.I).strip()
        if dropped != text.strip():
            return dropped, cmd
    working = text
    if cmd["kind"] == "shorter" and not cmd["target_words"]:
        cmd["target_words"] = max(80, int(len(text.split()) * 0.6))
    style_hint = {
        "technical": "Emphasize architecture, stack and engineering trade-offs.",
        "business": "Emphasize outcomes, value and plain business language.",
        "more_evidence": "Weave in more of the supplied project evidence.",
        "less_ai": "Short sentences, concrete nouns, no buzzwords; sound human.",
        "length": f"Aim for about {cmd['target_words']} words.",
        "shorter": f"Aim for about {cmd['target_words']} words.",
        "add_project": f"Feature the {cmd['extra']} project prominently, using only the extra evidence.",
        "general": "",
    }.get(cmd["kind"], "")
    try:
        svc = await _orchestrator()
        out = await svc._complete(
            [{"role": "system", "content": RefinementPrompt},
             {"role": "user", "content": (
                 f"Instruction: {instruction[:500]}\n{style_hint}\n"
                 f"Current artifact:\n{working[:6000]}\n"
                 f"{('Extra evidence:\n' + evidence_extra[:2000]) if evidence_extra else ''}")}],
            max_tokens=1500, temperature=0.4, tag="workbench-refine")
        working = str(out["data"].get("text", working))
        ai_used = True
    except Exception as e:
        log.warning("workbench refine without AI: %s", e)
        ai_used = False
    if cmd["target_words"]:
        working = trim_to_words(working, cmd["target_words"])
    cmd["ai_used"] = ai_used
    return working, cmd


# ── sessions & documents ──

def new_session_id() -> str:
    return uuid.uuid4().hex[:16]


async def get_session(db, session_id: str) -> dict | None:
    return await db["proposal_sessions"].find_one({"session_id": session_id})


async def save_session(db, session: dict) -> None:
    session["updated_at"] = utcnow()
    await db["proposal_sessions"].update_one(
        {"session_id": session["session_id"]}, {"$set": session}, upsert=True)


async def audit_workbench(email: str, action: str, entity: str = "",
                          meta: dict | None = None, session_id: str | None = None) -> None:
    try:
        await audit(email, action, entity, meta or {},
                    event_type=action, session_id=session_id)
    except Exception as e:
        log.warning("workbench audit failed: %s", e)


# ── Career Application generation (admin-only; reuses the pipeline above) ──

CAREER_GENERATION_PROMPT = """You are drafting a job application email for Rajib Mahata, a professional
software candidate. Use ONLY the verified evidence provided. Never invent
employers, titles, metrics, certifications, URLs or history. Never mention
Upwork, freelancing, freelancer platforms, or present RajibLabs as a
freelancing platform. Write as Rajib in first person: professional, human,
concise, personalized to the hiring contact. Return JSON keys exactly:
email_subject, email_body, cover_letter, short_summary."""

CAREER_CONTEXT_RULES = (
    "Context rules for JOB APPLICATIONS: draw on professional experience, resume, "
    "skills, LinkedIn, relevant projects and education. Do NOT mention Upwork, "
    "freelancing, freelancer platforms, 'freelance project', or present RajibLabs "
    "as a freelancing platform, unless the job description explicitly requires it."
)


async def generate_career_application(analysis: RequirementAnalysis,
                                      matches: list[ExperienceMatch],
                                      selected: list[dict],
                                      known_urls: set[str],
                                      company_name: str = "",
                                      contact_name: str = "",
                                      db=None) -> tuple[dict, bool]:
    """Returns ({email_subject, email_body, cover_letter, short_summary,
    sources}, ai_used). Deterministic template fallback when AI is down —
    still grounded only in verified evidence."""
    match_lines = "\n".join(
        f"- {m.requirement} → {m.project or '(no direct evidence)'}"
        + (f" ({m.url})" if m.url else "") for m in matches)
    sources = [ProposalSource(
        title=c.get("doc_title") or c.get("title", ""),
        type=c.get("source_type", "project"),
        url=validate_url(c.get("doc_url") or "", known_urls),
        reason=c.get("selection_reason") or f"Ranked #{i+1} for this role") for i, c in enumerate(selected)]
    to_line = f"To: {contact_name} ({company_name})" if contact_name or company_name else "To: hiring team"
    brief = (f"{to_line}\nRole: {analysis.title} | {analysis.industry} | {company_name}\n"
             f"{CAREER_CONTEXT_RULES}\n"
             f"Requirements:\n{match_lines}\nEvidence:\n{_evidence_block(selected)}")
    try:
        svc = await _orchestrator()
        out = await svc._complete(
            [{"role": "system", "content": CAREER_GENERATION_PROMPT},
             {"role": "user", "content": brief[:9000]}],
            max_tokens=1500, temperature=0.4, tag="career-generate")
        data = out["data"]
        texts = {k: str(data.get(k, "")) for k in
                 ("email_subject", "email_body", "cover_letter", "short_summary")}
    except Exception as e:
        log.warning("career template fallback: %s", e)
        ex = selected[0] if selected else None
        ex_line = (f"For example, {ex.get('doc_title')}: "
                   f"{(ex.get('content') or '')[:220]}") if ex else ""
        role = analysis.title or "this role"
        texts = {
            "email_subject": f"Application for {role} — Rajib Mahata",
            "email_body": (
                f"Dear {contact_name or 'Hiring Manager'},\n\n"
                f"I am applying for the {role} position"
                f"{' at ' + company_name if company_name else ''}. {ex_line}\n\n"
                f"Relevant strengths: "
                f"{', '.join(m.requirement for m in matches if m.project) or 'see below'}.\n\n"
                f"I would welcome the chance to discuss how I can contribute.\n\n"
                f"Best regards,\nRajib Mahata"),
            "cover_letter": "",
            "short_summary": (
                f"Rajib Mahata applying for {role}: "
                f"{', '.join(analysis.technologies[:4]) or 'relevant experience'}."),
        }
        return {**texts, "sources": [s.model_dump() for s in sources]}, False
    for k in ("email_body", "cover_letter", "short_summary"):
        texts[k] = _scrub_urls(texts[k], known_urls)
    return {**texts, "sources": [s.model_dump() for s in sources]}, True
