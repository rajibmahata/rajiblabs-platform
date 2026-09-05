"""Lead/idea business rules — deterministic, no AI here.

The AI extracts; THIS module validates, dedups, merges, scores and persists.
"""
import re

from app.database import utcnow

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_STATUSES = {"new", "contacted", "qualified", "proposal", "won",
                  "lost", "archived", "spam", "closed"}
HOT_LEAD_THRESHOLD = 50

# Explicit marketing opt-in signals only — never auto-subscribe.
CONSENT_PATTERNS = (
    r"subscrib", r"newsletter", r"send me (regular )?updates",
    r"keep me updated", r"opt[\s-]?in", r"add me to (your |the )?(mailing )?list",
    r"email me (updates|news|offers)",
)
# A clearly separate product/business problem starts a NEW idea.
NEW_IDEA_PATTERNS = (
    r"\banother\b.{0,30}\b(idea|project|product|business|startup|venture|app)\b",
    r"\b(different|second|new|other)\b.{0,20}\b(idea|project|product)\b",
    r"\bi also want\b", r"\bwhat about\b.{0,30}\b(building|making|creating)\b",
)
# Explicit correction language — the visitor is replacing a contact detail.
# Without this, a newer value never overwrites an older one.
CORRECTION_PATTERNS = (
    r"\bnew\b.{0,15}\b(number|email|phone|contact|address)\b",
    r"\bchang(e|ed|ing)\b.{0,15}\b(number|email|phone|contact|address)\b",
    r"\bactually\b", r"\bcorrection\b", r"\bupdate my\b", r"\binstead\b",
    r"\bwrong\b.{0,15}\b(number|email)\b",
)


def states_correction(message_text: str) -> bool:
    text = (message_text or "").lower()
    return any(re.search(p, text) for p in CORRECTION_PATTERNS)
PROPOSAL_PATTERNS = (r"proposal", r"quot", r"pricing", r"price", r"\bcost\b", r"how much", r"estimate")
MEETING_PATTERNS = (r"\bmeeting\b", r"\bcall\b", r"\bdemo\b", r"\bschedul", r"talk to",
                    r"discuss with", r"speak with", r"video call", r"google meet", r"\bzoom\b")

SCOPE_DISCLAIMER = ("AI-generated preliminary scope. Final requirements, architecture, "
                    "timeline and pricing will be confirmed during discovery.")


def normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def valid_email(email: str | None) -> bool:
    e = normalize_email(email)
    return bool(e) and len(e) <= 254 and bool(EMAIL_RE.match(e))


def normalize_phone(phone: str | None) -> str:
    p = (phone or "").strip()
    if not p:
        return ""
    digits = re.sub(r"\D", "", p)
    return ("+" if p.startswith("+") else "") + digits


def valid_phone(phone: str | None) -> bool:
    digits = re.sub(r"\D", "", phone or "")
    return 7 <= len(digits) <= 15


def blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def idea_is_substantive(idea: dict) -> bool:
    return bool((idea.get("description") or "").strip()
                and len((idea.get("description") or "").strip()) >= 10)


def missing_fields_for(lead: dict, idea: dict) -> list[str]:
    missing = []
    if blank(lead.get("name")):
        missing.append("name")
    if not valid_email(lead.get("email")):
        missing.append("email")
    if not valid_phone(lead.get("phone")):
        missing.append("phone")
    if not idea_is_substantive(idea):
        missing.append("idea")
    return missing


def score_lead(lead: dict, idea: dict, message_text: str = "") -> int:
    """Deterministic score — the ONLY authoritative score (AI never scores)."""
    score = 0
    if valid_email(lead.get("email")):
        score += 10
    if valid_phone(lead.get("phone")):
        score += 10
    if idea_is_substantive(idea):
        score += 15
    if not blank(lead.get("company_name")):
        score += 5
    if not blank(lead.get("industry")):
        score += 5
    if len((idea.get("problem_statement") or "").strip()) >= 40:
        score += 10
    if not blank(idea.get("desired_outcome")):
        score += 10
    text = (message_text or "").lower()
    if any(re.search(p, text) for p in PROPOSAL_PATTERNS):
        score += 15
    if any(re.search(p, text) for p in MEETING_PATTERNS):
        score += 20
    return min(score, 100)


def wants_new_idea(message_text: str) -> bool:
    text = (message_text or "").lower()
    return any(re.search(p, text) for p in NEW_IDEA_PATTERNS)


def gives_marketing_consent(message_text: str) -> bool:
    text = (message_text or "").lower()
    return any(re.search(p, text) for p in CONSENT_PATTERNS)


def merge_idea(existing: dict, incoming: dict, cap: int = 2000) -> dict:
    """Accumulate business context without losing previous information."""
    merged = dict(existing)
    for key in ("description", "problem_statement", "current_process", "desired_outcome"):
        old, new = (existing.get(key) or "").strip(), (incoming.get(key) or "").strip()
        if not new:
            continue
        if not old:
            merged[key] = new[:cap]
        elif new.lower() not in old.lower():
            merged[key] = (old + " " + new)[:cap]
    return merged


def blank_idea() -> dict:
    return {"description": "", "problem_statement": "",
            "current_process": "", "desired_outcome": ""}


def render_scope_markdown(scope: dict) -> str:
    def bullets(items):
        items = items or []
        return "\n".join(f"- {x}" for x in items) if items else "_To be defined in discovery._"
    sections = [
        ("1. Problem Understanding", scope.get("problem_understanding", "")),
        ("2. Proposed Solution", scope.get("proposed_solution", "")),
        ("3. Core Features", bullets(scope.get("core_features"))),
        ("4. User Roles", bullets(scope.get("user_roles"))),
        ("5. Main Workflow", bullets(scope.get("main_workflow"))),
        ("6. MVP Scope", bullets(scope.get("mvp_scope"))),
        ("7. Future Features", bullets(scope.get("future_features"))),
        ("8. Technology Direction", scope.get("technology_direction", "")),
        ("9. Risks / Assumptions", bullets(scope.get("risks_assumptions"))),
        ("10. Questions for Discovery", bullets(scope.get("discovery_questions"))),
    ]
    body = "\n\n".join(f"**{title}**\n{content}" for title, content in sections)
    return f"*{SCOPE_DISCLAIMER}*\n\n{body}"
