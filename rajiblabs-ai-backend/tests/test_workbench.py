"""Admin AI Proposal Studio tests (20 cases, §35).

No network, no secrets: AI orchestrator and RAG retrieval are faked at the
service boundary; endpoint tests assert admin auth only.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.services import workbench as wb
from app.services.lead_ai import AIError


class DeadAI:
    """Orchestrator stand-in that is never configured."""
    def __init__(self, *a, **k):
        raise AIError("AI not configured")


@pytest.fixture
def no_ai(monkeypatch):
    monkeypatch.setattr(wb.lead_ai, "AIService", DeadAI)


@pytest.fixture
def no_db(monkeypatch):
    def _boom():
        raise RuntimeError("no db in unit test")
    monkeypatch.setattr(wb, "get_db", _boom)


def _ev(title, stype, content, url="", score=0.8, doc="d1"):
    return {"doc_title": title, "title": title, "source_type": stype,
            "content": content, "doc_url": url, "url": url,
            "score": score, "document_id": doc, "chunk_id": "c1",
            "_priority": wb.SOURCE_PRIORITY.get(stype, 6)}


# 1–4. requirement extraction ──

def test_extract_techs_healthcare_stack():
    jd = ("I need an experienced .NET developer to build a healthcare SaaS "
          "application with React, Azure, SQL Server and AI integration.")
    techs = [t.lower() for t in wb.extract_techs(jd)]
    for want in (".net", "react", "azure", "sql server", "ai", "saas"):
        assert want in techs, want


def test_extract_company_explicit_only():
    assert wb.extract_company("Company: Acme Health\nWe need .NET work.") == "Acme Health"
    # No label → never invented.
    assert wb.extract_company("We at Acme need a developer for our hospital app.") == ""


def test_extract_industry_healthcare():
    assert wb.extract_industry("pharmacy management platform for hospitals") == "Healthcare"


def test_rule_analysis_shape_and_years():
    a = wb.rule_analysis("Senior .NET developer with 5+ years experience.\n- Build APIs\n- Deploy to Azure")
    assert a.years_experience.startswith("5")
    assert ".net" in [t.lower() for t in a.technologies]
    assert a.business_problem and a.responsibilities


# 5–8. retrieval / selection / matching ──

async def test_retrieve_evidence_dedupes_and_ranks(monkeypatch, no_db):
    async def fake_retrieve(q, top_k=0, intent="GENERAL", repository=None):
        return [_ev("Rajib Profile", "profile", "Rajib Mahata architect", score=0.9, doc="d0"),
                _ev("Pharmacy Platform", "project", "pharmacy .NET automation", score=0.5, doc="d1"),
                _ev("Pharmacy Platform", "project", "pharmacy .NET automation", score=0.5, doc="d1")]
    monkeypatch.setattr(wb.rag_query, "retrieve", fake_retrieve)
    from app.schemas import RequirementAnalysis
    out = await wb.retrieve_evidence(RequirementAnalysis(title="x"), top_k=6)
    assert [h["document_id"] for h in out].count("d1") == 1  # deduped
    assert out[0]["document_id"] == "d1"  # specific project outranks generic profile


async def test_select_examples_bounded_without_ai(no_ai):
    from app.schemas import RequirementAnalysis
    ev = [_ev(f"P{i}", "project", f"project content {i}", doc=f"d{i}") for i in range(6)]
    sel = await wb.select_examples(RequirementAnalysis(title="t"), ev)
    assert 2 <= len(sel) <= 4


async def test_match_maps_requirement_to_evidence(no_ai):
    from app.schemas import RequirementAnalysis
    sel = [_ev("Pharmacy Automation Platform", "project",
               "pharmacy workflow automation with .NET and React",
               url="https://rajiblabs.com/projects/pharmacy", doc="d1")]
    m = await wb.match_requirements(
        RequirementAnalysis(title="t", technologies=[".NET"], required_skills=[".NET"]),
        sel, sel)
    assert m and m[0].project == "Pharmacy Automation Platform"
    assert m[0].url == "https://rajiblabs.com/projects/pharmacy"
    assert m[0].evidence  # every claim cites evidence


async def test_match_unmatched_requirement_is_gap(no_ai):
    from app.schemas import RequirementAnalysis
    sel = [_ev("Retail Dashboard", "project", "retail charts", doc="d9")]
    m = await wb.match_requirements(
        RequirementAnalysis(title="t", technologies=["COBOL"]), sel, sel)
    assert any(not x.project for x in m)


# 9–12. URL validation ──

def test_validate_url_known_passes():
    known = {"https://rajiblabs.com/projects/pharmacy", "https://github.com/rajibmahata/pestflow"}
    assert wb.validate_url("https://rajiblabs.com/projects/pharmacy", known) == \
        "https://rajiblabs.com/projects/pharmacy"


def test_validate_url_invented_dropped():
    known = {"https://rajiblabs.com/projects/pharmacy"}
    assert wb.validate_url("https://rajiblabs.com/projects/made-up-thing", known) == ""
    assert wb.validate_url("https://github.com/rajibmahata/definitely-not-real", known) == ""


def test_validate_url_scheme_and_host():
    known = {"http://rajiblabs.com/projects/pharmacy", "https://evil.com/x"}
    assert wb.validate_url("http://rajiblabs.com/projects/pharmacy", known) == ""
    assert wb.validate_url("https://evil.com/x", known) == ""
    assert wb.validate_url("javascript:alert(1)", known) == ""


def test_scrub_urls_removes_unverified():
    known = {"https://rajiblabs.com/projects/pharmacy"}
    text = "See https://rajiblabs.com/projects/pharmacy and https://example.com/fake."
    out = wb._scrub_urls(text, known)
    assert "rajiblabs.com/projects/pharmacy" in out
    assert "example.com/fake" not in out


# 13–15. quality gate ──

def test_quality_flags_generic_opener():
    q = wb.quality_check("Dear Hiring Manager,\nI am an experienced developer with skills. Call me.",
                         "", "", [], set())
    assert "generic_opener" in q["issues"] and not q["passed"]


def test_quality_flags_hype_and_missing_cta():
    q = wb.quality_check("Hi, I am the perfect candidate and I guarantee success.", "", "", [], set())
    assert "hype_language" in q["issues"]
    assert "missing_call_to_action" in q["issues"]


def test_quality_clean_passes():
    sel = [_ev("Pharmacy Platform", "project", "x",
               url="https://rajiblabs.com/projects/pharmacy")]
    q = wb.quality_check(
        "Hi, your pharmacy automation problem maps to the Pharmacy Platform work. "
        "See https://rajiblabs.com/projects/pharmacy. Happy to jump on a call next week.",
        "", "", sel, {"https://rajiblabs.com/projects/pharmacy"})
    assert q["passed"], q["issues"]


# 16–18. score + refinement ──

def test_match_score_transparent_weights():
    from app.schemas import RequirementAnalysis
    ev = [_ev("Pharmacy Platform", "project", ".NET React pharmacy automation",
              doc="d1"),
          _ev("Rajib Profile", "profile", "Rajib Mahata 10 years architect", doc="d0")]
    a = wb.RequirementAnalysis(title="t", industry="Healthcare",
                               technologies=[".NET", "React"],
                               required_skills=[".NET", "React"])
    full = wb.match_score(a, [wb.ExperienceMatch(requirement=".NET", project="Pharmacy Platform")],
                          ev[:1], ev)
    assert 0 <= full.match_score <= 100
    empty = wb.match_score(a, [], [], [])
    assert empty.match_score < full.match_score  # evidence moves the score


def test_parse_refine_commands():
    assert wb.parse_refine_instruction("Make it shorter.")["kind"] == "shorter"
    c = wb.parse_refine_instruction("Create a 150-word version.")
    assert c["kind"] == "length" and c["target_words"] == 150
    c2 = wb.parse_refine_instruction("Add the pharmacy project.")
    assert c2["kind"] == "add_project" and "pharmacy" in c2["extra"].lower()
    c3 = wb.parse_refine_instruction("Remove the GitHub link.")
    assert c3["kind"] == "remove_link"
    assert wb.parse_refine_instruction("Focus more on Azure.")["kind"] == "general"


def test_trim_to_words_sentence_boundary():
    text = "First sentence here. Second sentence here. Third sentence here."
    out = wb.trim_to_words(text, 5)
    assert len(out.split()) <= 5 and out.endswith(".")
    assert wb.trim_to_words(text, 500) == text


# 19–20. AI-down fallback + auth ──

async def test_analyze_fallback_without_ai(no_ai, no_db):
    a, ai_used = await wb.analyze_requirements("Need a .NET developer for 3+ years.", db=None)
    assert ai_used is False
    assert ".net" in [t.lower() for t in a.technologies]


async def test_endpoints_require_admin():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for method, path, body in (
                ("POST", "/api/admin/ai/proposal/analyze", {"job_description": "x" * 30}),
                ("POST", "/api/admin/ai/proposal/generate", {"job_description": "x" * 30}),
                ("POST", "/api/admin/ai/proposal/refine", {"instruction": "shorter"}),
                ("POST", "/api/admin/ai/proposal/save", {"title": "t", "job_description": "x" * 30}),
                ("POST", "/api/admin/ai/chat", {"message": "hi"}),
                ("GET", "/api/admin/ai/proposals", None),
                ("GET", "/api/admin/ai/proposal/000000000000000000000000", None),
                ("DELETE", "/api/admin/ai/proposal/000000000000000000000000", None)):
            r = await c.request(method, path, json=body) if body else await c.request(method, path)
            assert r.status_code in (401, 403), (method, path, r.status_code)


def test_project_explanation_mode_registered():
    from app.schemas import WORKBENCH_MODES, AnalyzeIn, GenerateIn
    from app.services.workbench import MODE_GUIDANCE, CONTEXT_RULES
    assert "project_explanation" in WORKBENCH_MODES
    assert "project_explanation" in MODE_GUIDANCE
    a = AnalyzeIn(job_description="x" * 30, mode="project_explanation",
                  company="Acme", instructions="Focus on Azure.")
    assert a.company == "Acme" and a.instructions == "Focus on Azure."
    g = GenerateIn(job_description="x" * 30, session_id="abc123")
    assert g.session_id == "abc123"
    assert set(CONTEXT_RULES) >= {"job_application", "freelance_proposal"}


def test_selection_reason_grounded():
    from types import SimpleNamespace
    from app.services.workbench import selection_reason
    analysis = SimpleNamespace(technologies=["React", "FastAPI"])
    c = {"doc_title": "Shop", "source_type": "project",
         "doc_url": "https://rajiblabs.com/portfolio/shop",
         "content": "React storefront with FastAPI backend"}
    reason = selection_reason(c, analysis)
    assert "React" in reason and "FastAPI" in reason
    assert "verified" in reason.lower()


def test_build_explanation_uses_only_evidence():
    from types import SimpleNamespace
    from app.services.workbench import build_explanation
    analysis = SimpleNamespace(title="Retail site", technologies=[])
    assert build_explanation(analysis, []) == ""
    selected = [{"doc_title": "Shop", "source_type": "project",
                 "doc_url": "https://rajiblabs.com/portfolio/shop",
                 "doc_repo": "rajibmahata/shop",
                 "content": "React storefront, Stripe payments."}]
    text = build_explanation(analysis, selected)
    assert "Shop" in text and "https://rajiblabs.com/portfolio/shop" in text
    assert "http" not in text.replace("https://rajiblabs.com/portfolio/shop", "")
    assert "Why relevant" in text


def test_quality_flags_context_mixing():
    from app.services.workbench import quality_check
    q = quality_check("Apply via Upwork freelance platform today. Call now!",
                      "", "", [], set())
    assert "freelance_leak_in_job" in quality_check(
        "Apply via Upwork freelance platform today. Call now!",
        "", "", [], set(), mode="job_application")["issues"]
    assert "corporate_leak_in_freelance" in quality_check(
        "I work with clients. My current employer uses Azure. Call now!",
        "", "", [], set(), mode="freelance_proposal")["issues"]
    assert q["passed"] is True  # no mode → no context rule applies


async def test_full_flow_deterministic_no_ai_no_db(no_ai, no_db):
    """JD → analyze → select → match → generate → validate, all offline."""
    from app.schemas import RequirementAnalysis
    jd = ("Freelance React + FastAPI project: rebuild our pharmacy storefront. "
          "Must have: React, TypeScript, prescription refill workflow.\n"
          "Client: City Pharmacy\nBudget: fixed price.")
    analysis, ai_used = await wb.analyze_requirements(jd)
    assert ai_used is False and "react" in analysis.technologies
    assert analysis.company == "City Pharmacy"
    ev = [
        _ev("PestFlow", "project", "React pharmacy storefront with refill workflow",
            "https://rajiblabs.com/portfolio/pestflow", doc="d1"),
        _ev("Shop", "github_readme", "React app notes",
            "https://github.com/rajibmahata/shop", doc="d2"),
    ]
    selected = await wb.select_examples(analysis, ev)
    assert 2 <= len(selected) <= 4
    assert all(c.get("selection_reason") for c in selected)
    matches = await wb.match_requirements(analysis, selected, ev)
    assert matches and any(m.project for m in matches)
    report = wb.match_score(analysis, matches, selected, ev)
    assert report.match_score >= 0
    known = {"https://rajiblabs.com/portfolio/pestflow",
             "https://github.com/rajibmahata/shop"}
    artifacts, ai2 = await wb.generate_artifacts(
        analysis, matches, selected, "freelance_proposal",
        "professional", "standard", known)
    assert ai2 is False
    assert artifacts["proposal"] and artifacts["explanation"]
    assert "PestFlow" in artifacts["explanation"]
    assert all(s["reason"] for s in artifacts["sources"])
    q = wb.quality_check(artifacts["proposal"], artifacts["cover_letter"],
                         artifacts["short_summary"], selected, known,
                         mode="freelance_proposal")
    assert q["score"] >= 0 and "unverifiable_url" not in q["issues"]


async def test_explanation_mode_end_to_end_no_ai(no_ai, no_db):
    from app.schemas import RequirementAnalysis
    analysis = RequirementAnalysis(title="Retail site", technologies=["React"])
    ev = [_ev("Shop", "project", "React storefront",
              "https://rajiblabs.com/portfolio/shop")]
    selected = await wb.select_examples(analysis, ev)
    known = {"https://rajiblabs.com/portfolio/shop"}
    artifacts, _ = await wb.generate_artifacts(
        analysis, [], selected, "project_explanation",
        "professional", "standard", known)
    assert "Shop" in artifacts["explanation"]
    assert "http" not in artifacts["explanation"].replace(
        "https://rajiblabs.com/portfolio/shop", "")
