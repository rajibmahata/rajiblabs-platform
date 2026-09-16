"""Quality scoring engine with configurable dimensions."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.models import QualityDimension, QualityResult, QualityGrade

logger = logging.getLogger(__name__)

GENERIC_PATTERNS = [
    r"(?i)\b(powerful|innovative|cutting.edge|seamless|robust|scalable|state.of.the.art|world.class|best.in.class|next.generation)\b",
    r"(?i)\b(leverages?|utilizes?|employs?|harnesses?)\s+(modern|advanced|powerful|innovative)\b",
    r"(?i)\b(comprehensive|holistic|end.to.end|full.stack|enterprise.grade)\b",
]

QUALITY_DIMENSIONS = [
    "factual_accuracy",
    "evidence_coverage",
    "completeness",
    "specificity",
    "readability",
    "technical_depth",
    "business_relevance",
    "uniqueness",
    "seo_quality",
    "relationship_integrity",
]


def _detect_generic_content(text: str) -> list[str]:
    issues = []
    for pattern in GENERIC_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            issues.append(f"Generic language detected: '{m}'")
    return issues


def _check_specificity(text: str) -> list[str]:
    issues = []
    if len(text) < 50:
        issues.append("Content too short for meaningful specificity")
    sentences = re.split(r'[.!?]+', text)
    short_count = sum(1 for s in sentences if 0 < len(s.strip()) < 20)
    if len(sentences) > 3 and short_count > len(sentences) * 0.3:
        issues.append("Too many short/generic sentences")
    return issues


def _check_technical_depth(text: str, skills: list[str] | None = None) -> list[str]:
    issues = []
    tech_indicators = [
        r"(?i)(architecture|api|database|cache|deploy|docker|kubernetes|microservice)",
        r"(?i)(implementation|integration|pipeline|workflow|algorithm)",
        r"(?i)(pattern|design|testing|monitoring|logging)",
    ]
    has_tech = any(re.search(p, text) for p in tech_indicators)
    if not has_tech and len(text) > 100:
        issues.append("No technical depth indicators found")
    return issues


def _check_business_relevance(text: str) -> list[str]:
    issues = []
    business_indicators = [
        r"(?i)(customer|client|user|business|revenue|cost|efficiency|productivity)",
        r"(?i)(requirement|stakeholder|workflow|process|operation)",
    ]
    has_biz = any(re.search(p, text) for p in business_indicators)
    if not has_biz and len(text) > 100:
        issues.append("No business relevance indicators found")
    return issues


def score_factual_accuracy(content: dict, evidence: list[dict]) -> QualityDimension:
    score = 10.0
    issues = []
    if not evidence:
        score -= 5
        issues.append("No evidence sources provided")
    unverified = [k for k, v in content.items() if v and k not in ("_id", "created_at", "updated_at")]
    if len(unverified) > 5:
        score -= 2
        issues.append(f"{len(unverified)} fields without evidence verification")
    return QualityDimension(
        dimension="factual_accuracy",
        score=max(0, score),
        issues=issues,
    )


def score_evidence_coverage(content: dict, evidence: list[dict]) -> QualityDimension:
    score = min(10.0, len(evidence) * 2.0)
    issues = []
    if len(evidence) == 0:
        issues.append("No evidence linked")
    elif len(evidence) < 3:
        issues.append("Limited evidence coverage")
    return QualityDimension(dimension="evidence_coverage", score=score, issues=issues)


def score_completeness(content: dict, required_fields: list[str]) -> QualityDimension:
    filled = sum(1 for f in required_fields if content.get(f))
    ratio = filled / max(len(required_fields), 1)
    score = ratio * 10.0
    missing = [f for f in required_fields if not content.get(f)]
    issues = [f"Missing: {f}" for f in missing[:5]]
    return QualityDimension(dimension="completeness", score=round(score, 1), issues=issues)


def score_specificity(text: str) -> QualityDimension:
    generic = _detect_generic_content(text)
    specific = _check_specificity(text)
    score = 10.0 - min(5.0, len(generic) * 1.0) - min(3.0, len(specific) * 0.5)
    return QualityDimension(
        dimension="specificity",
        score=max(0, round(score, 1)),
        issues=generic + specific,
    )


def score_readability(text: str) -> QualityDimension:
    if not text:
        return QualityDimension(dimension="readability", score=0.0, issues=["No content"])
    sentences = re.split(r'[.!?]+', text)
    words = text.split()
    avg_sentence_len = len(words) / max(len(sentences), 1)
    score = 10.0
    issues = []
    if avg_sentence_len > 30:
        score -= 3
        issues.append("Sentences too long (avg > 30 words)")
    elif avg_sentence_len < 5:
        score -= 2
        issues.append("Sentences too short (avg < 5 words)")
    if len(text) > 2000:
        score -= 2
        issues.append("Content may be too verbose")
    return QualityDimension(dimension="readability", score=max(0, round(score, 1)), issues=issues)


def score_technical_depth(text: str, skills: list[str] | None = None) -> QualityDimension:
    issues = _check_technical_depth(text, skills)
    score = 10.0 - min(5.0, len(issues) * 2.5)
    return QualityDimension(dimension="technical_depth", score=max(0, round(score, 1)), issues=issues)


def score_business_relevance(text: str) -> QualityDimension:
    issues = _check_business_relevance(text)
    score = 10.0 - min(5.0, len(issues) * 2.5)
    return QualityDimension(dimension="business_relevance", score=max(0, round(score, 1)), issues=issues)


def score_uniqueness(text: str, existing_texts: list[str] | None = None) -> QualityDimension:
    issues = []
    score = 10.0
    if existing_texts:
        for existing in existing_texts:
            overlap = len(set(text.lower().split()) & set(existing.lower().split()))
            total = max(len(set(text.lower().split()) | set(existing.lower().split())), 1)
            if overlap / total > 0.7:
                score -= 4
                issues.append("High content overlap with existing text")
                break
    return QualityDimension(dimension="uniqueness", score=max(0, round(score, 1)), issues=issues)


def score_seo_quality(content: dict) -> QualityDimension:
    score = 10.0
    issues = []
    if not content.get("meta_title"):
        score -= 3
        issues.append("Missing meta_title")
    if not content.get("meta_description"):
        score -= 3
        issues.append("Missing meta_description")
    if not content.get("slug"):
        score -= 2
        issues.append("Missing slug")
    return QualityDimension(dimension="seo_quality", score=max(0, round(score, 1)), issues=issues)


def score_relationship_integrity(relationships: list[dict]) -> QualityDimension:
    score = min(10.0, len(relationships) * 2.0)
    issues = []
    if len(relationships) == 0:
        issues.append("No relationships defined")
    return QualityDimension(dimension="relationship_integrity", score=max(0, round(score, 1)), issues=issues)


def compute_quality(
    content: dict,
    evidence: list[dict] | None = None,
    required_fields: list[str] | None = None,
    text_fields: list[str] | None = None,
    skills: list[str] | None = None,
    existing_texts: list[str] | None = None,
    relationships: list[dict] | None = None,
) -> QualityResult:
    evidence = evidence or []
    required_fields = required_fields or ["title", "description"]
    text_fields = text_fields or ["description", "about"]

    all_text = " ".join(str(content.get(f, "")) for f in text_fields if content.get(f))

    dimensions = [
        score_factual_accuracy(content, evidence),
        score_evidence_coverage(content, evidence),
        score_completeness(content, required_fields),
        score_specificity(all_text),
        score_readability(all_text),
        score_technical_depth(all_text, skills),
        score_business_relevance(all_text),
        score_uniqueness(all_text, existing_texts),
        score_seo_quality(content),
        score_relationship_integrity(relationships or []),
    ]

    total = sum(d.score for d in dimensions)
    max_total = sum(d.max_score for d in dimensions)
    pct = (total / max_total * 100) if max_total > 0 else 0

    if pct >= 90:
        grade = QualityGrade.PUBLISH
    elif pct >= 75:
        grade = QualityGrade.ACCEPTABLE
    elif pct >= 60:
        grade = QualityGrade.NEEDS_IMPROVEMENT
    else:
        grade = QualityGrade.REJECT

    return QualityResult(
        total_score=round(pct, 1),
        grade=grade,
        dimensions=dimensions,
        passed=grade in (QualityGrade.ACCEPTABLE, QualityGrade.PUBLISH),
        publishable=grade == QualityGrade.PUBLISH,
    )
