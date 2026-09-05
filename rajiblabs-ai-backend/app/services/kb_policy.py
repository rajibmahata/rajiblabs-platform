"""Central Knowledge Base policy — guardrails + hallucination control.

Single source of truth for what each knowledge document allows and how
strictly answers must be grounded. Enforced SERVER-SIDE by the retrieval
layer (`rag_query.retrieve(consumer=...)`) and the agent runtime
(`concierge`), never by prompt alone. Admin edits policies via
`/api/admin/rag/*`; documents without stored policies get safe defaults
(no migration needed).
"""
import re

CONSUMERS = ("public", "admin", "workbench", "rag")

DEFAULT_GUARDRAILS = {
    "public_access": True,
    "admin_access": True,
    "allow_rag": True,
    "allow_urls": True,
    "allow_source_code": False,
    "allow_internal_details": False,
    "allow_sensitive_data": False,
    "contains_sensitive_data": False,
    "require_source": True,
    "blocked_fields": [],
}

DEFAULT_HALLUCINATION = {
    "grounded_only": True,
    "minimum_confidence": 0.0,
    "allow_inference": False,
    "allow_general_fallback": False,
    "require_evidence": True,
    "require_verified_urls": True,
    "max_unsupported_claims": 0,
    "on_insufficient": "fallback",  # or "clarify"
    "fallback_message": (
        "I don't currently have verified information about that in the "
        "RajibLabs knowledge base. I can help you contact RajibLabs if you'd like."
    ),
}

# Drives the Admin form (type → widget) with inline help. Single source of
# truth — the UI renders this schema instead of hardcoding fields.
FIELD_META = {
    "guardrails": {
        "public_access": {"type": "bool", "label": "Public AI access",
                          "help": "Public concierge may retrieve this source."},
        "admin_access": {"type": "bool", "label": "Admin AI access",
                         "help": "Admin agents and previews may retrieve this source."},
        "allow_rag": {"type": "bool", "label": "Allow RAG retrieval",
                       "help": "Off = invisible to every retrieval path (direct doc reads still work)."},
        "allow_urls": {"type": "bool", "label": "Expose URLs",
                       "help": "Off = URLs stripped from hits and answers."},
        "allow_source_code": {"type": "bool", "label": "Expose source code",
                              "help": "Code files are excluded from public/workbench answers unless on."},
        "allow_internal_details": {"type": "bool", "label": "Expose internal details",
                                   "help": "Off = architecture/config content stays admin-only."},
        "allow_sensitive_data": {"type": "bool", "label": "May contain sensitive data",
                                 "help": "Informational flag; combine with Public AI access OFF to quarantine."},
        "contains_sensitive_data": {"type": "bool", "label": "Contains sensitive data",
                                    "help": "On = blocked for public/workbench/rag even if access flags are on."},
        "require_source": {"type": "bool", "label": "Require source citation",
                           "help": "Answers citing this source must include its verified URL."},
        "blocked_fields": {"type": "list", "label": "Blocked fields",
                           "help": "Comma-separated doc keys never sent to any LLM (e.g. internal_notes)."},
    },
    "hallucination_control": {
        "grounded_only": {"type": "bool", "label": "Require grounded answer",
                          "help": "No evidence = fallback message, never invention."},
        "minimum_confidence": {"type": "number", "label": "Minimum retrieval confidence",
                               "help": "0–1. Top hit below this = fallback/clarify. 0 disables."},
        "allow_inference": {"type": "bool", "label": "Allow inference",
                            "help": "Off = only state what evidence directly supports."},
        "allow_general_fallback": {"type": "bool", "label": "Allow general-knowledge fallback",
                                   "help": "Off = never answer from model knowledge when evidence is missing."},
        "require_evidence": {"type": "bool", "label": "Require source evidence",
                             "help": "Same as grounded-only, kept explicit for audit clarity."},
        "require_verified_urls": {"type": "bool", "label": "Require verified URLs",
                                  "help": "URLs in answers must come from tool/RAG metadata."},
        "max_unsupported_claims": {"type": "number", "label": "Max unsupported claims",
                                   "help": "Factual sentences with no evidence overlap allowed. 0 = strict."},
        "on_insufficient": {"type": "select", "label": "When knowledge is insufficient",
                            "options": ["fallback", "clarify"],
                            "help": "Show the fallback message, or ask a clarifying question."},
        "fallback_message": {"type": "text", "label": "Fallback response",
                             "help": "Shown instead of any invented answer."},
    },
}

_CODE_EXTS = (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".go",
              ".rb", ".php", ".c", ".h", ".cpp", ".sql", ".sh", ".yml",
              ".yaml", ".json", ".xml", ".toml", ".ini", ".cfg")
_SKIP_WORDS = frozenset(
    "the,a,an,and,or,of,to,in,on,for,with,is,are,was,were,be,been,that,this,"
    "it,its,as,at,by,from,into,over,after,before,between,has,have,had,will,"
    "would,can,will,just,than,then,there,their,what,which,when,while,also,"
    "rajiblabs,rajib,here,there,using,use,used".split(","))
URL_RE = re.compile(r"https?://[^\s)>\]]+")


def _as_bool(v, default: bool) -> bool:
    return default if v is None else bool(v)


def normalize_guardrails(raw: dict | None) -> dict:
    raw = raw or {}
    blocked = raw.get("blocked_fields") or []
    if isinstance(blocked, str):
        blocked = [b.strip() for b in blocked.split(",") if b.strip()]
    return {
        "public_access": _as_bool(raw.get("public_access"), True),
        "admin_access": _as_bool(raw.get("admin_access"), True),
        "allow_rag": _as_bool(raw.get("allow_rag"), True),
        "allow_urls": _as_bool(raw.get("allow_urls"), True),
        "allow_source_code": _as_bool(raw.get("allow_source_code"), False),
        "allow_internal_details": _as_bool(raw.get("allow_internal_details"), False),
        "allow_sensitive_data": _as_bool(raw.get("allow_sensitive_data"), False),
        "contains_sensitive_data": _as_bool(raw.get("contains_sensitive_data"), False),
        "require_source": _as_bool(raw.get("require_source"), True),
        "blocked_fields": [str(b)[:80] for b in blocked[:20]],
    }


def normalize_hallucination(raw: dict | None) -> dict:
    raw = raw or {}
    try:
        conf = float(raw.get("minimum_confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    try:
        maxc = int(raw.get("max_unsupported_claims", 0))
    except (TypeError, ValueError):
        maxc = 0
    on_ins = raw.get("on_insufficient")
    return {
        "grounded_only": _as_bool(raw.get("grounded_only"), True),
        "minimum_confidence": conf,
        "allow_inference": _as_bool(raw.get("allow_inference"), False),
        "allow_general_fallback": _as_bool(raw.get("allow_general_fallback"), False),
        "require_evidence": _as_bool(raw.get("require_evidence"), True),
        "require_verified_urls": _as_bool(raw.get("require_verified_urls"), True),
        "max_unsupported_claims": max(0, maxc),
        "on_insufficient": on_ins if on_ins in ("fallback", "clarify") else "fallback",
        "fallback_message": str(raw.get("fallback_message")
                                or DEFAULT_HALLUCINATION["fallback_message"])[:2000],
    }


def effective_guardrails(doc: dict | None) -> dict:
    return normalize_guardrails((doc or {}).get("guardrails"))


def effective_hallucination(doc: dict | None) -> dict:
    return normalize_hallucination((doc or {}).get("hallucination_control"))


def _is_code_doc(doc: dict) -> bool:
    fp = (doc.get("file_path") or "").lower()
    if not fp or "." not in fp.rsplit("/", 1)[-1]:
        return False
    return fp.endswith(_CODE_EXTS)


def doc_allowed_for_consumer(doc: dict | None, consumer: str) -> tuple[bool, str]:
    """Server-side gate. Returns (allowed, reason). Unknown consumers denied."""
    if consumer not in CONSUMERS:
        return False, "unknown-consumer"
    doc = doc or {}
    if (doc.get("status") or "active") != "active":
        return False, "inactive"
    g = effective_guardrails(doc)
    if not g["allow_rag"] and consumer in ("public", "rag", "workbench"):
        return False, "rag-disabled"
    if g["contains_sensitive_data"] and not g["allow_sensitive_data"] \
            and consumer in ("public", "rag", "workbench"):
        return False, "sensitive"
    if _is_code_doc(doc) and not g["allow_source_code"] and consumer != "admin":
        return False, "source-code"
    if consumer == "public" and not g["public_access"]:
        return False, "not-public"
    if consumer == "admin" and not g["admin_access"]:
        return False, "not-admin"
    if consumer == "workbench" and not (g["public_access"] or g["admin_access"]):
        return False, "not-workbench"
    return True, "ok"


def strip_blocked_fields(doc: dict) -> dict:
    """Remove admin-blocked keys before content reaches any LLM."""
    g = effective_guardrails(doc)
    blocked = {b.lower() for b in g["blocked_fields"]}
    if not blocked:
        return doc
    return {k: v for k, v in doc.items() if k.lower() not in blocked}


def filter_hits(hits: list[dict], docs_by_id: dict, consumer: str = "public") -> list[dict]:
    """Drop chunks whose parent doc fails the consumer gate. Pure.

    Fail-closed: a hit with no resolvable parent document is dropped —
    orphan vectors must never reach an answer.
    """
    kept = []
    for h in hits or []:
        doc = docs_by_id.get(h.get("document_id") or "")
        if doc is None:
            continue
        ok, _ = doc_allowed_for_consumer(doc, consumer)
        if ok:
            kept.append(h)
    return kept


def _content_words(text: str) -> set[str]:
    return {w.strip(".,;:!?()[]{}\"'").lower() for w in (text or "").split()
            if len(w.strip(".,;:!?()[]{}\"'")) > 3} - _SKIP_WORDS


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def validate_grounding(reply: str, evidence: list[str], policy: dict | None,
                       top_score: float | None = None) -> tuple[bool, str]:
    """Deterministic hallucination gate — no LLM call.

    Returns (ok, reason). Reasons: ok | no-evidence | low-confidence |
    unsupported-claims. Cost rule: pure retrieval-score + overlap math.
    """
    p = normalize_hallucination(policy)
    ev_text = " ".join(e or "" for e in (evidence or []))
    if not ev_text.strip():
        if p["grounded_only"] or p["require_evidence"]:
            return False, "no-evidence"
        return True, "ok"
    if p["minimum_confidence"] > 0 and top_score is not None \
            and top_score < p["minimum_confidence"]:
        return False, "low-confidence"
    if p["grounded_only"] or p["max_unsupported_claims"] is not None:
        ev_words = _content_words(ev_text)
        unsupported = 0
        for sent in _sentences(reply):
            if len(sent.split()) < 6 or sent.rstrip().endswith(("?", ":")):
                continue  # transitions, questions and headers aren't claims
            if len(_content_words(sent) & ev_words) < 2:
                unsupported += 1
        if unsupported > p["max_unsupported_claims"]:
            return False, "unsupported-claims"
    return True, "ok"


def validate_reply_urls(reply: str, allowed: set[str]) -> tuple[str, int]:
    """Strip any URL the tools/RAG didn't return. Returns (cleaned, removed)."""
    removed = 0

    def keep(m):
        nonlocal removed
        url = m.group(0).rstrip(".,)]}'\"")
        if url in (allowed or set()):
            return m.group(0)
        removed += 1
        return ""

    cleaned = re.sub(URL_RE, keep, reply or "")
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip(), removed


def collect_allowed_urls(tool_results: dict) -> set[str]:
    urls: set[str] = {"https://rajiblabs.com"}

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("url", "live_url", "github_url", "demo_url",
                         "product_url", "website") and isinstance(v, str) and v.startswith("http"):
                    urls.add(v.split()[0].rstrip(".,)]}'\""))
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(tool_results or {})
    return urls


def resolve_request_policy(agent_cfg: dict | None, docs: list[dict]) -> dict:
    """Merge agent-level + per-doc hallucination knobs; strictest wins.

    Agent fallback message wins (admin-configured voice); doc fallback used
    only when the agent has none.
    """
    agent_cfg = agent_cfg or {}
    merged = dict(DEFAULT_HALLUCINATION)
    if (agent_cfg.get("hallucination_policy") or "") == "verified-only":
        merged["grounded_only"] = True
        merged["require_evidence"] = True
    for d in docs or []:
        h = (d or {}).get("hallucination_control") or {}
        if not h:
            continue
        hn = normalize_hallucination(h)
        merged["grounded_only"] = merged["grounded_only"] or hn["grounded_only"]
        merged["require_evidence"] = merged["require_evidence"] or hn["require_evidence"]
        merged["allow_inference"] = merged["allow_inference"] and hn["allow_inference"]
        merged["allow_general_fallback"] = merged["allow_general_fallback"] and hn["allow_general_fallback"]
        merged["require_verified_urls"] = merged["require_verified_urls"] or hn["require_verified_urls"]
        merged["minimum_confidence"] = max(merged["minimum_confidence"], hn["minimum_confidence"])
        merged["max_unsupported_claims"] = min(merged["max_unsupported_claims"], hn["max_unsupported_claims"])
        if not agent_cfg.get("fallback_message") and hn.get("fallback_message"):
            merged["fallback_message"] = hn["fallback_message"]
    if agent_cfg.get("fallback_message"):
        merged["fallback_message"] = agent_cfg["fallback_message"]
    return merged
