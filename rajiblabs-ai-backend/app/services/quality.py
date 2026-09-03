"""Deterministic quality gate (no hallucination claims pass)."""
import re
from app.config import get_settings
from app.schemas import AIContentOut, QualityScore

RISKY = [r"\bmillions of users", r"99\.99% uptime", r"industry-leading", r"\bbest\b.*platform",
         r"award-winning", r"millions in revenue", r"enterprise production platform"]


def score_content(c: AIContentOut, evidence: str) -> QualityScore:
    flags = []
    text = " ".join([c.title, c.short_description, c.description, c.business_value]).lower()
    for pat in RISKY:
        if re.search(pat, text):
            flags.append(f"unsupported-claim:{pat}")
    ev = (evidence or "").lower()
    accuracy = 95 if not flags else 60
    completeness = 90 if (c.description and c.technology_summary) else 70
    professional = 92 if len(c.short_description) <= 170 else 80
    seo = 90 if (c.seo_title and c.seo_description) else 70
    overall = round((accuracy + completeness + professional + seo) / 4)
    s = get_settings()
    return QualityScore(accuracy=accuracy, completeness=completeness, professional=professional,
                        seo=seo, overall=overall, flags=flags,
                        passed=overall >= s.ai_quality_threshold and not flags)
