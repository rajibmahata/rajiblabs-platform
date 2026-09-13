"""Universal Agentic Learning Content Validation Engine.

Reusable validation pipeline for ANY learning content in RajibLabs.
Content-type aware, rule-based, deterministic-first, LLM-last.

Architecture:
    Content → Normalize → Detect Type → Build Context → Validate Rules →
    Score → Plan Improvements → Improve → Revalidate → Compare → Publish/Rollback

Principles:
- Deterministic validation runs first (zero cost).
- LLM only for semantic analysis, curriculum reasoning, improvement generation.
- Content-hash dedup: unchanged content skips revalidation.
- Configurable scoring weights and publishing gates.
- Version every meaningful change; automatic rollback on regression.
"""
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

from app.config import get_settings
from app.database import get_db, utcnow
from app.services.notify import audit, log_error

log = logging.getLogger("rajiblabs")

# ═══════════════════════════════════════════════════════════════════
# 1. CONTENT TYPES
# ═══════════════════════════════════════════════════════════════════

class ContentType(str, Enum):
    LESSON = "lesson"
    MODULE = "module"
    COURSE = "course"
    LEARNING_PATH = "learning_path"
    TUTORIAL = "tutorial"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"
    PROJECT = "project"
    DOCUMENTATION = "documentation"
    ARTICLE = "article"
    MIXED = "mixed"


class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ContentAction(str, Enum):
    KEEP = "KEEP"
    IMPROVE = "IMPROVE"
    REWRITE = "REWRITE"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    REMOVE = "REMOVE"
    ADD = "ADD"


# ═══════════════════════════════════════════════════════════════════
# 2. NORMALIZED CONTENT MODEL
# ═══════════════════════════════════════════════════════════════════

@dataclass
class NormalizedContent:
    """Universal internal representation for any learning content."""
    content_id: str
    content_type: ContentType
    title: str
    description: str = ""
    language: str = "en"
    difficulty: Difficulty = Difficulty.BEGINNER
    topic: str = ""
    prerequisites: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)
    code_examples: list[dict] = field(default_factory=list)
    exercises: list[str] = field(default_factory=list)
    homework: list[str] = field(default_factory=list)
    quizzes: list[dict] = field(default_factory=list)
    assessment: list[dict] = field(default_factory=list)
    project_tasks: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict = field(default_factory=dict)
    content_hash: str = ""
    version: int = 1


# ═══════════════════════════════════════════════════════════════════
# 3. VALIDATION RULES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ValidationIssue:
    """Single validation finding."""
    rule_id: str
    severity: str
    category: str
    section: str
    problem: str
    recommendation: str
    confidence: float = 0.9


@dataclass
class ValidationResult:
    """Complete validation result for one piece of content."""
    content_id: str
    content_type: str
    content_version: int
    overall_score: float = 0.0
    status: str = "NOT_VALIDATED"
    dimensions: dict = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    improvement_required: bool = False
    actions: list[dict] = field(default_factory=list)
    validation_mode: str = "DETERMINISTIC"
    content_hash: str = ""
    created_at: str = ""


# ═══════════════════════════════════════════════════════════════════
# 4. CONTENT NORMALIZER
# ═══════════════════════════════════════════════════════════════════

def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def normalize_lesson_block(block: dict, path: dict | None = None) -> NormalizedContent:
    """Convert a learning_block document to universal NormalizedContent."""
    topic = block.get("topic") or block.get("title") or ""
    concept = block.get("concept_explanation") or block.get("simple_explanation") or ""
    obj = block.get("learning_objective") or ""

    sections = []
    if concept:
        sections.append({"type": "explanation", "content": concept})
    if block.get("step_by_step"):
        sections.append({"type": "steps", "content": block["step_by_step"]})
    if block.get("real_world_example"):
        sections.append({"type": "real_world", "content": block["real_world_example"]})
    if block.get("why_matters"):
        sections.append({"type": "why_matters", "content": block["why_matters"]})

    examples = block.get("examples") or []
    code_examples = [ex for ex in examples if ex.get("code")]

    exercises = []
    if block.get("exercise"):
        exercises.append(block["exercise"])
    if block.get("challenge"):
        exercises.append(block["challenge"])

    homework = []
    if block.get("homework"):
        homework.append(block["homework"])

    raw = json.dumps(block, sort_keys=True, default=str)
    h = _content_hash(raw)

    difficulty = Difficulty.BEGINNER
    if path:
        lvl = (path.get("level") or "beginner").lower()
        for d in Difficulty:
            if d.value == lvl:
                difficulty = d
                break

    return NormalizedContent(
        content_id=str(block.get("_id", "")),
        content_type=ContentType.LESSON,
        title=block.get("title") or block.get("topic") or "",
        description=obj,
        language=block.get("language", "en"),
        difficulty=difficulty,
        topic=topic,
        prerequisites=path.get("prerequisites", []) if path else [],
        learning_objectives=[obj] if obj else [],
        sections=sections,
        examples=examples,
        code_examples=code_examples,
        exercises=exercises,
        homework=homework,
        summary=block.get("quick_review") or "",
        metadata={
            "day_number": block.get("day_number", 0),
            "slug": block.get("slug", ""),
            "status": block.get("status", ""),
            "version": block.get("version", 1),
            "path_id": block.get("path_id", ""),
        },
        content_hash=h,
        version=block.get("version", 1),
    )


def normalize_path(path: dict, blocks: list[dict]) -> NormalizedContent:
    """Convert a learning_paths document + its blocks to universal NormalizedContent."""
    roadmap = path.get("roadmap") or []
    sections = []
    if roadmap:
        for day in roadmap:
            sections.append({
                "type": "day",
                "day": day.get("day", 0),
                "title": day.get("title", ""),
                "objective": day.get("objective", ""),
            })
    else:
        # Derive sections from blocks
        sorted_blocks = sorted(blocks, key=lambda b: b.get("day_number", 0))
        for b in sorted_blocks:
            sections.append({
                "type": "day",
                "day": b.get("day_number", 0),
                "title": b.get("title") or b.get("topic", ""),
                "objective": b.get("learning_objective", ""),
            })

    all_blocks = sorted(blocks, key=lambda b: b.get("day_number", 0))
    all_exercises = []
    all_homework = []
    all_examples = []
    for b in all_blocks:
        if b.get("exercise"):
            all_exercises.append(b["exercise"])
        if b.get("homework"):
            all_homework.append(b["homework"])
        for ex in (b.get("examples") or []):
            all_examples.append(ex)

    raw = json.dumps({"slug": path.get("slug"), "roadmap": roadmap}, sort_keys=True)
    h = _content_hash(raw)

    return NormalizedContent(
        content_id=str(path.get("_id", "")),
        content_type=ContentType.LEARNING_PATH,
        title=path.get("topic") or path.get("title") or "",
        description=path.get("goal") or "",
        language=path.get("language", "en"),
        difficulty=Difficulty.BEGINNER,
        topic=path.get("topic") or "",
        prerequisites=path.get("prerequisites", []),
        learning_objectives=[d.get("objective", "") for d in roadmap if d.get("objective")],
        sections=sections,
        examples=all_examples,
        exercises=all_exercises,
        homework=all_homework,
        summary=f"{len(roadmap)} days, {len(all_blocks)} blocks published",
        metadata={
            "slug": path.get("slug", ""),
            "status": path.get("status", ""),
            "duration": path.get("duration", 0),
            "current_day": path.get("current_day", 0),
            "progress": path.get("progress", 0),
        },
        content_hash=h,
        version=path.get("version", 1),
    )


# ═══════════════════════════════════════════════════════════════════
# 5. VALIDATION RULES ENGINE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Rule:
    rule_id: str
    name: str
    category: str
    severity: str
    applies_to: list[str]
    description: str = ""
    enabled: bool = True


# Rule registry — single source of truth
RULES: list[Rule] = [
    Rule("STRUCTURAL_OBJECTIVE", "Learning objective present", "structural", "P0",
         ["lesson", "module", "course", "learning_path", "tutorial"],
         "Content must have a clear learning objective"),
    Rule("STRUCTURAL_EXPLANATION", "Concept explanation present", "structural", "P0",
         ["lesson", "tutorial", "module"],
         "Content must have an explanation section"),
    Rule("STRUCTURAL_EXAMPLES", "Has examples", "structural", "P1",
         ["lesson", "tutorial", "exercise"],
         "Content should include at least one example"),
    Rule("STRUCTURAL_EXERCISES", "Has exercises", "structural", "P1",
         ["lesson", "module", "tutorial"],
         "Content should include exercises for practice"),
    Rule("STRUCTURAL_CODE", "Code has explanation", "structural", "P1",
         ["lesson", "tutorial", "exercise"],
         "Every code example must have an explanation"),
    Rule("BEGINNER_OBJECTIVE_CLARITY", "Objective uses doing words", "beginner", "P1",
         ["lesson", "tutorial", "exercise"],
         "Objective should state what the learner will DO"),
    Rule("BEGINNER_JARGON", "No unexplained jargon", "beginner", "P1",
         ["lesson", "tutorial", "module"],
         "Technical terms must be explained before naming"),
    Rule("BEGINNER_REAL_WORLD", "Concrete real-world example", "beginner", "P1",
         ["lesson", "tutorial", "module"],
         "Real-world examples must be concrete, not abstract"),
    Rule("BEGINNER_STEP_ACTIONABILITY", "Steps are actionable", "beginner", "P2",
         ["lesson", "tutorial"],
         "Steps must be concrete actions, not vague suggestions"),
    Rule("BEGINNER_TRY_IT", "Try-it-yourself is specific", "beginner", "P2",
         ["lesson", "tutorial"],
         "Try-it-yourself must be a specific change, not vague"),
    Rule("BEGINNER_MISTAKES", "Mistakes explain WHY", "beginner", "P2",
         ["lesson", "tutorial"],
         "Common mistakes must explain why they happen"),
    Rule("BEGINNER_ABILITIES", "Concrete abilities listed", "beginner", "P2",
         ["lesson", "tutorial"],
         "What-you-can-do-now must list concrete abilities"),
    Rule("BEGINNER_AI_FILLER", "No generic AI phrases", "beginner", "P1",
         ["lesson", "tutorial", "module", "course", "learning_path"],
         "Content must not contain generic AI filler phrases"),
    Rule("TECHNICAL_ACCURACY", "Code is syntactically valid", "technical", "P0",
         ["lesson", "tutorial", "exercise"],
         "Code examples must be syntactically valid"),
    Rule("TECHNICAL_CONSISTENCY", "Code matches topic", "technical", "P0",
         ["lesson", "tutorial"],
         "Code examples must be relevant to the lesson topic"),
    Rule("TECHNICAL_COMPLETENESS", "Setup instructions present", "technical", "P1",
         ["lesson", "tutorial", "exercise"],
         "Technical content should include setup/installation steps"),
    Rule("CURRICULUM_PROGRESSION", "No topic repetition", "curriculum", "P0",
         ["learning_path", "course", "module"],
         "Sequential content must not repeat the same topic"),
    Rule("CURRICULUM_DIFFICULTY", "No sudden difficulty jumps", "curriculum", "P0",
         ["learning_path", "course", "module"],
         "Difficulty must increase gradually across the curriculum"),
    Rule("CURRICULUM_COMPLETENESS", "All planned content exists", "curriculum", "P1",
         ["learning_path", "course"],
         "All planned lessons must have published content"),
    Rule("CURRICULUM_PREREQUISITES", "Prerequisites reasonable", "curriculum", "P1",
         ["learning_path", "course", "module"],
         "Beginner paths should have 0-3 prerequisites"),
    Rule("CURRICULUM_FIRST_DAY", "First day is gentle", "curriculum", "P1",
         ["learning_path", "course"],
         "Day 1 must not introduce advanced concepts"),
    Rule("PRACTICAL_EXERCISE_RELEVANCE", "Exercises match lesson", "practical", "P1",
         ["lesson", "tutorial", "exercise"],
         "Exercises must align with lesson objectives"),
    Rule("PRACTICAL_HOMEWORK_VALUE", "Homework extends learning", "practical", "P2",
         ["lesson", "tutorial"],
         "Homework should extend learning, not just repeat"),
    Rule("PRACTICAL_LEARNING_OUTCOMES", "Clear learning outcomes", "practical", "P1",
         ["lesson", "module", "course", "learning_path"],
         "Content should clearly state what the learner can do after"),
    Rule("QUALITY_EXPLANATION_DEPTH", "Explanation is thorough", "quality", "P2",
         ["lesson", "tutorial", "module"],
         "Explanations should be thorough but not verbose"),
    Rule("QUALITY_PARAGRAPH_LENGTH", "Short paragraphs for beginners", "quality", "P2",
         ["lesson", "tutorial"],
         "Paragraphs should be short (max 400 chars) for beginners"),
    Rule("QUALITY_REVIEW_RECAP", "Quick review is substantive", "quality", "P2",
         ["lesson", "tutorial"],
         "Quick review must contain specific takeaways, not filler"),
    Rule("QUALITY_WHY_MATTERS", "Why-matters is concrete", "quality", "P2",
         ["lesson", "tutorial", "module"],
         "Why-matters must connect to real scenarios"),
    Rule("CONSISTENCY_NO_DUPLICATE_CODE", "No duplicate code across days", "consistency", "P0",
         ["learning_path", "course"],
         "Different lessons must not have identical code examples"),
    Rule("CONSISTENCY_NO_DUPLICATE_EXERCISES", "No duplicate exercises", "consistency", "P1",
         ["learning_path", "course"],
         "Different lessons must not have identical exercises"),
]

# Quick lookup
_RULE_MAP: dict[str, Rule] = {r.rule_id: r for r in RULES}


def _applicable_rules(content_type: str) -> list[Rule]:
    """Return rules that apply to the given content type."""
    return [r for r in RULES if r.enabled and content_type in r.applies_to]


# ═══════════════════════════════════════════════════════════════════
# 6. SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════

DEFAULT_SCORING_WEIGHTS = {
    "beginner_friendliness": 0.15,
    "technical_accuracy": 0.15,
    "learning_objective": 0.10,
    "curriculum_progression": 0.15,
    "practical_learning": 0.15,
    "explanation_quality": 0.10,
    "real_world_relevance": 0.10,
    "examples_code": 0.05,
    "exercises_assessment": 0.05,
}

DEFAULT_THRESHOLDS = {
    "excellent": 90,
    "good": 80,
    "needs_improvement": 70,
    "weak": 60,
    "poor": 0,
}

DEFAULT_PUBLISH_GATE = {
    "min_overall": 70,
    "min_technical": 70,
    "max_p0_issues": 0,
}


def _classify_score(score: float, thresholds: dict | None = None) -> str:
    t = thresholds or DEFAULT_THRESHOLDS
    if score >= t["excellent"]:
        return "Excellent"
    if score >= t["good"]:
        return "Good"
    if score >= t["needs_improvement"]:
        return "Needs Improvement"
    if score >= t["weak"]:
        return "Weak"
    return "Poor"


# ═══════════════════════════════════════════════════════════════════
# 7. DETERMINISTIC VALIDATORS (zero LLM cost)
# ═══════════════════════════════════════════════════════════════════

_BANNED_PHRASES = frozenset([
    "as an ai", "in conclusion", "in summary, this lesson",
    "it is important to note", "it is worth noting",
    "furthermore", "moreover", "in addition to",
    "it should be noted", "as mentioned earlier",
    "as we have discussed", "this is a complex topic",
    "advanced concept", "advanced topic",
    "today you will learn", "in today's digital world",
    "welcome to", "let's dive into",
])

_DOING_WORDS = frozenset({
    "create", "write", "build", "use", "run", "explain", "identify", "define",
    "apply", "debug", "read", "modify", "add", "remove", "print", "calculate",
    "implement", "design", "test", "deploy", "configure", "install", "setup",
    "compare", "analyze", "evaluate", "develop", "construct", "refactor",
})

_ABSTRACT_MARKERS = ["in general", "typically", "often", "usually",
                     "in many cases", "broadly speaking"]


def _validate_structural(nc: NormalizedContent) -> list[ValidationIssue]:
    """Deterministic structural checks."""
    issues = []

    # Objective present
    if not nc.learning_objectives or not any(o.strip() for o in nc.learning_objectives):
        issues.append(ValidationIssue(
            "STRUCTURAL_OBJECTIVE", "P0", "structural", "objective",
            "No learning objective found",
            "Add a clear learning objective stating what the learner will DO"))

    # Explanation present
    has_explanation = any(s.get("content") for s in nc.sections
                         if s.get("type") in ("explanation", "real_world"))
    if not has_explanation and nc.content_type in (ContentType.LESSON, ContentType.TUTORIAL):
        issues.append(ValidationIssue(
            "STRUCTURAL_EXPLANATION", "P0", "structural", "explanation",
            "No concept explanation found",
            "Add a clear explanation of the topic"))

    # Examples present
    if not nc.examples and nc.content_type in (ContentType.LESSON, ContentType.TUTORIAL):
        issues.append(ValidationIssue(
            "STRUCTURAL_EXAMPLES", "P1", "structural", "examples",
            "No examples found",
            "Add at least one worked example"))

    # Code explanation
    for ex in nc.code_examples:
        if ex.get("code") and not ex.get("explanation"):
            issues.append(ValidationIssue(
                "STRUCTURAL_CODE", "P1", "structural", "examples",
                f"Code example '{ex.get('title', '')}' has no explanation",
                "Add line-by-line explanation of what the code does"))

    return issues


def _validate_beginner(nc: NormalizedContent) -> list[ValidationIssue]:
    """Beginner-friendliness checks."""
    issues = []
    ce = ""
    for s in nc.sections:
        if s.get("type") == "explanation":
            ce = s.get("content", "")
            break
    if not ce:
        ce = nc.description

    # AI filler detection
    ce_lower = ce.lower()
    for phrase in _BANNED_PHRASES:
        if phrase in ce_lower:
            issues.append(ValidationIssue(
                "BEGINNER_AI_FILLER", "P1", "beginner", "explanation",
                f"Contains banned AI phrase: '{phrase}'",
                "Remove generic AI phrasing; use direct, teacher-like language"))
            break  # one is enough for this rule

    # Objective clarity — doing words
    for obj in nc.learning_objectives:
        obj_words = set(obj.lower().split())
        if not _DOING_WORDS & obj_words:
            issues.append(ValidationIssue(
                "BEGINNER_OBJECTIVE_CLARITY", "P1", "beginner", "objective",
                "Learning objective does not use doing words (create, build, use...)",
                "Rewrite objective to state what the learner will DO"))
            break

    # Real-world example
    rw = ""
    for s in nc.sections:
        if s.get("type") == "real_world":
            rw = s.get("content", "")
            break
    if rw and len(rw) < 100:
        issues.append(ValidationIssue(
            "BEGINNER_REAL_WORLD", "P1", "beginner", "real_world",
            f"Real-world example too short ({len(rw)} chars, min 100)",
            "Expand with a concrete scenario including specific names/numbers"))
    if rw:
        if any(m in rw.lower() for m in _ABSTRACT_MARKERS) and len(rw) < 150:
            issues.append(ValidationIssue(
                "BEGINNER_REAL_WORLD", "P1", "beginner", "real_world",
                "Real-world example is too abstract",
                "Use a concrete story with specific names/numbers instead of generalizations"))

    # Paragraph length
    if ce:
        paras = [p for p in ce.split("\n\n") if p.strip()]
        long_paras = [p for p in paras if len(p) > 400]
        if long_paras:
            issues.append(ValidationIssue(
                "QUALITY_PARAGRAPH_LENGTH", "P2", "quality", "explanation",
                f"Found {len(long_paras)} paragraphs >400 chars",
                "Split long paragraphs into shorter ones (2-3 sentences each)"))

    # Steps actionability
    for s in nc.sections:
        if s.get("type") == "steps":
            steps = s.get("content", [])
            if isinstance(steps, list):
                vague = [st for st in steps if any(v in st.lower()
                        for v in ["understand", "learn about", "study", "review"])]
                if vague and len(steps) <= 3:
                    issues.append(ValidationIssue(
                        "BEGINNER_STEP_ACTIONABILITY", "P2", "beginner", "steps",
                        "Steps contain vague actions (understand/learn/study)",
                        "Replace with concrete actions: 'Run...', 'Type...', 'Change...'"))
            break

    # Jargon detection
    if ce:
        jargon_words = [w for w in ce.split() if len(w) > 12 and w[0].isupper()]
        if len(jargon_words) > 4:
            issues.append(ValidationIssue(
                "BEGINNER_JARGON", "P1", "beginner", "explanation",
                f"Explanation has {len(jargon_words)} potentially unexplained technical terms",
                "Explain each technical term before naming it"))

    return issues


def _validate_technical(nc: NormalizedContent) -> list[ValidationIssue]:
    """Technical accuracy checks (deterministic)."""
    issues = []
    is_python = any(kw in (nc.topic + " " + nc.title + " " + nc.description).lower()
                    for kw in ("python", "django", "flask", "fastapi", "pytest"))
    for ex in nc.code_examples:
        code = ex.get("code", "")
        title = ex.get("title", "")
        if not code:
            continue

        # Basic Python syntax check
        if is_python:
            if "def " in code or "class " in code or "import " in code or "=" in code:
                try:
                    compile(code, "<validation>", "exec")
                except SyntaxError as e:
                    issues.append(ValidationIssue(
                        "TECHNICAL_ACCURACY", "P0", "technical", "code",
                        f"Python syntax error in '{title}': {e}",
                        "Fix the syntax error"))

        # Check for incomplete code (trailing incomplete lines)
        lines = code.strip().split("\n")
        if lines and lines[-1].rstrip().endswith((":", ",", "(", "[", "{")):
            issues.append(ValidationIssue(
                "TECHNICAL_COMPLETENESS", "P1", "technical", "code",
                f"Code in '{title}' appears incomplete (ends with open bracket/colon)",
                "Complete the code example or mark it as a snippet"))

    return issues


def _validate_consistency(nc: NormalizedContent, siblings: list[NormalizedContent] | None = None) -> list[ValidationIssue]:
    """Cross-content consistency checks."""
    issues = []
    if not siblings:
        return issues

    # Duplicate code detection — pre-seed with current block's code
    seen_codes: dict[str, str] = {}
    for ex in nc.code_examples:
        code = ex.get("code", "").strip()
        if code:
            seen_codes[code] = nc.title
    for sib in siblings:
        for ex in sib.code_examples:
            code = ex.get("code", "").strip()
            if code and code in seen_codes:
                issues.append(ValidationIssue(
                    "CONSISTENCY_NO_DUPLICATE_CODE", "P0", "consistency", "code",
                    f"Code example duplicated from '{seen_codes[code]}'",
                    "Write unique code relevant to this specific lesson"))
            elif code:
                seen_codes[code] = sib.title

    # Duplicate exercise detection — pre-seed with current block's exercises
    seen_ex: dict[str, str] = {}
    for ex_text in nc.exercises:
        if ex_text:
            seen_ex[ex_text] = nc.title
    for sib in siblings:
        for ex_text in sib.exercises:
            if ex_text in seen_ex:
                issues.append(ValidationIssue(
                    "CONSISTENCY_NO_DUPLICATE_EXERCISES", "P1", "consistency", "exercises",
                    f"Exercise duplicated from '{seen_ex[ex_text]}'",
                    "Write a unique exercise relevant to this lesson"))
            elif ex_text:
                seen_ex[ex_text] = sib.title

    return issues


def _validate_curriculum(path_nc: NormalizedContent, block_ncs: list[NormalizedContent]) -> list[ValidationIssue]:
    """Path-level curriculum checks."""
    issues = []

    # Repeated titles
    titles = [nc.title for nc in block_ncs]
    seen = {}
    for t in titles:
        if t in seen:
            issues.append(ValidationIssue(
                "CURRICULUM_PROGRESSION", "P0", "curriculum", "structure",
                f"Title '{t}' appears multiple times",
                "Each lesson must have a unique title"))
        seen[t] = True

    # Day 1 advanced concepts
    if block_ncs:
        first = block_ncs[0]
        advanced_kw = ["async", "linq", "generics", "reflection", "middleware",
                       "microservices", "caching", "authentication", "deployment"]
        first_text = (first.title + " " + first.description).lower()
        hits = [k for k in advanced_kw if k in first_text]
        if hits:
            issues.append(ValidationIssue(
                "CURRICULUM_FIRST_DAY", "P1", "curriculum", "difficulty",
                f"Day 1 contains advanced concepts: {', '.join(hits)}",
                "Day 1 must cover fundamentals only"))

    # Missing blocks (duration vs actual)
    duration = path_nc.metadata.get("duration", 0)
    if duration and len(block_ncs) < duration:
        missing = duration - len(block_ncs)
        issues.append(ValidationIssue(
            "CURRICULUM_COMPLETENESS", "P1", "curriculum", "completeness",
            f"{missing} of {duration} planned days are missing",
            "Generate the missing lesson blocks"))

    # Prerequisites count
    if len(path_nc.prerequisites) > 3:
        issues.append(ValidationIssue(
            "CURRICULUM_PREREQUISITES", "P1", "curriculum", "prerequisites",
            f"{len(path_nc.prerequisites)} prerequisites (max 3 for beginner)",
            "Reduce to 0-3 prerequisites; rephrase or remove non-essential ones"))

    return issues


# ═══════════════════════════════════════════════════════════════════
# 8. SCORING CALCULATOR
# ═══════════════════════════════════════════════════════════════════

def _calculate_scores(
    nc: NormalizedContent,
    issues: list[ValidationIssue],
    weights: dict | None = None,
) -> dict[str, float]:
    """Calculate dimension scores from issues. Each dimension starts at 100, deductions per issue."""
    w = weights or DEFAULT_SCORING_WEIGHTS
    dims = {k: 100.0 for k in w}

    deductions = {
        "beginner": {"beginner_friendliness": 15, "explanation_quality": 10, "real_world_relevance": 8},
        "structural": {"learning_objective": 20, "explanation_quality": 15, "examples_code": 12},
        "technical": {"technical_accuracy": 20},
        "curriculum": {"curriculum_progression": 15},
        "practical": {"practical_learning": 15, "exercises_assessment": 10},
        "quality": {"explanation_quality": 8, "beginner_friendliness": 5},
        "consistency": {"curriculum_progression": 12, "examples_code": 10},
    }

    sev_mult = {"P0": 2.0, "P1": 1.0, "P2": 0.5, "P3": 0.25}

    for issue in issues:
        cat = issue.category
        sev = issue.severity
        mult = sev_mult.get(sev, 0.5)
        ded = deductions.get(cat, {})
        for dim, base_ded in ded.items():
            if dim in dims:
                dims[dim] -= base_ded * mult

    # Content-completeness penalties: missing key elements drag down relevant dimensions
    if not nc.examples:
        dims["examples_code"] -= 25
    if not nc.exercises:
        dims["exercises_assessment"] -= 20
        dims["practical_learning"] -= 15
    if not nc.sections:
        dims["explanation_quality"] -= 30
        dims["beginner_friendliness"] -= 15

    # P0 structural failures penalize all dimensions (content is fundamentally broken)
    p0_count = sum(1 for issue in issues if issue.severity == "P0")
    if p0_count > 0:
        penalty = min(p0_count * 8, 30)
        for dim in dims:
            dims[dim] -= penalty

    for dim in dims:
        dims[dim] = max(0.0, min(100.0, dims[dim]))

    overall = sum(dims[k] * w[k] for k in w) / sum(w.values()) if w else 0
    dims["overall"] = round(overall, 1)
    return dims


# ═══════════════════════════════════════════════════════════════════
# 9. MAIN VALIDATION ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════

def validate_block(block: dict, path: dict | None = None,
                   siblings: list[dict] | None = None,
                   weights: dict | None = None) -> dict:
    """Validate a single learning block. Returns ValidationResult as dict."""
    nc = normalize_lesson_block(block, path)

    # Collect sibling normalized contents for consistency checks
    sib_ncs = []
    if siblings:
        sib_ncs = [normalize_lesson_block(s, path) for s in siblings if s.get("_id") != block.get("_id")]

    # Run all deterministic validators
    all_issues: list[ValidationIssue] = []
    all_issues.extend(_validate_structural(nc))
    all_issues.extend(_validate_beginner(nc))
    all_issues.extend(_validate_technical(nc))
    all_issues.extend(_validate_consistency(nc, sib_ncs if sib_ncs else None))

    # Score
    dims = _calculate_scores(nc, all_issues, weights)
    overall = dims.pop("overall", 0)

    # Classify
    status = "PASS" if overall >= 70 else "FAIL"
    p0_count = sum(1 for i in all_issues if i.severity == "P0")
    if p0_count > 0:
        status = "FAIL"

    # Determine actions
    actions = []
    if overall >= 85 and p0_count == 0:
        actions.append({"action": "KEEP", "reason": "Score above threshold, no critical issues"})
    elif overall >= 60:
        actions.append({"action": "IMPROVE", "reason": f"Score {overall} — improve weak areas"})
    else:
        actions.append({"action": "REWRITE", "reason": f"Score {overall} — significant quality issues"})

    # Strengths
    strengths = []
    if dims.get("technical_accuracy", 0) >= 90:
        strengths.append("Technically accurate content")
    if dims.get("beginner_friendliness", 0) >= 85:
        strengths.append("Good beginner accessibility")
    if dims.get("practical_learning", 0) >= 85:
        strengths.append("Strong practical focus")
    if dims.get("explanation_quality", 0) >= 85:
        strengths.append("Clear, thorough explanations")

    result = ValidationResult(
        content_id=nc.content_id,
        content_type=nc.content_type.value,
        content_version=nc.version,
        overall_score=overall,
        status=status,
        dimensions=dims,
        strengths=strengths,
        issues=[asdict(i) for i in all_issues],
        improvement_required=status == "FAIL",
        actions=actions,
        validation_mode="DETERMINISTIC",
        content_hash=nc.content_hash,
        created_at=str(utcnow()),
    )
    return asdict(result)


def validate_path(path: dict, blocks: list[dict],
                  weights: dict | None = None) -> dict:
    """Validate an entire learning path. Returns combined result."""
    path_nc = normalize_path(path, blocks)
    block_ncs = [normalize_lesson_block(b, path) for b in blocks]

    # Validate each block
    all_block_issues: list[ValidationIssue] = []
    block_results = []
    sorted_blocks = sorted(blocks, key=lambda b: b.get("day_number", 0))

    for i, block in enumerate(sorted_blocks):
        prev = sorted_blocks[i - 1] if i > 0 else None
        siblings = [b for b in sorted_blocks if b.get("day_number") != block.get("day_number")]
        br = validate_block(block, path, siblings, weights)
        block_results.append(br)
        for issue in br.get("issues", []):
            all_block_issues.append(ValidationIssue(
                issue["rule_id"], issue["severity"], issue["category"],
                f"day_{block.get('day_number', '?')}:{issue['section']}",
                issue["problem"], issue["recommendation"],
                issue.get("confidence", 0.9)))

    # Path-level curriculum validation
    curr_issues = _validate_curriculum(path_nc, block_ncs)
    all_block_issues.extend(curr_issues)

    # Score path
    dims = _calculate_scores(path_nc, all_block_issues, weights)
    overall = dims.pop("overall", 0)

    status = "PASS" if overall >= 70 else "FAIL"
    p0_count = sum(1 for i in all_block_issues if i.severity == "P0")
    if p0_count > 0:
        status = "FAIL"

    # Block scores summary
    block_scores = []
    for br in block_results:
        block_scores.append({
            "content_id": br["content_id"],
            "score": br["overall_score"],
            "status": br["status"],
            "issues": len(br["issues"]),
        })

    return {
        "content_id": path_nc.content_id,
        "content_type": "learning_path",
        "content_version": path_nc.version,
        "overall_score": overall,
        "status": status,
        "dimensions": dims,
        "block_scores": block_scores,
        "total_blocks": len(blocks),
        "blocks_passing": sum(1 for bs in block_scores if bs["status"] == "PASS"),
        "total_issues": len(all_block_issues),
        "p0_issues": p0_count,
        "issues": [asdict(i) for i in all_block_issues],
        "improvement_required": status == "FAIL",
        "validation_mode": "DETERMINISTIC",
        "content_hash": path_nc.content_hash,
        "created_at": str(utcnow()),
    }


# ═══════════════════════════════════════════════════════════════════
# 10. IMPROVEMENT PLANNER
# ═══════════════════════════════════════════════════════════════════

def plan_improvements(validation_result: dict) -> list[dict]:
    """Convert validation issues into actionable improvement plans."""
    issues = validation_result.get("issues", [])
    plans = []

    for issue in issues:
        sev = issue.get("severity", "P2")
        action = ContentAction.IMPROVE.value
        if sev == "P0":
            action = ContentAction.REWRITE.value

        plans.append({
            "rule_id": issue.get("rule_id", ""),
            "severity": sev,
            "action": action,
            "category": issue.get("category", ""),
            "section": issue.get("section", ""),
            "problem": issue.get("problem", ""),
            "recommendation": issue.get("recommendation", ""),
            "confidence": issue.get("confidence", 0.9),
            "priority": {"P0": 1, "P1": 2, "P2": 3, "P3": 4}.get(sev, 5),
        })

    plans.sort(key=lambda p: p["priority"])
    return plans


# ═══════════════════════════════════════════════════════════════════
# 11. VERSION MANAGER + ROLLBACK
# ═══════════════════════════════════════════════════════════════════

async def save_validation_result(db, content_type: str, content_id: str,
                                 result: dict) -> str:
    """Persist validation result to MongoDB. Returns the inserted ID."""
    doc = {
        "content_type": content_type,
        "content_id": content_id,
        "content_hash": result.get("content_hash", ""),
        "overall_score": result.get("overall_score", 0),
        "status": result.get("status", ""),
        "dimensions": result.get("dimensions", {}),
        "issues": result.get("issues", []),
        "improvement_required": result.get("improvement_required", False),
        "validation_mode": result.get("validation_mode", "DETERMINISTIC"),
        "created_at": utcnow(),
    }
    res = await db["content_validations"].insert_one(doc)
    return str(res.inserted_id)


async def save_improvement(db, content_type: str, content_id: str,
                           before_score: float, after_score: float,
                           changes: list[dict], content_hash: str) -> str:
    """Record an improvement attempt with before/after scores."""
    doc = {
        "content_type": content_type,
        "content_id": content_id,
        "before_score": before_score,
        "after_score": after_score,
        "improvement": round(after_score - before_score, 1),
        "changes": changes,
        "content_hash": content_hash,
        "successful": after_score >= before_score,
        "created_at": utcnow(),
    }
    res = await db["content_improvements"].insert_one(doc)
    return str(res.inserted_id)


async def get_validation_history(db, content_id: str, limit: int = 20) -> list[dict]:
    """Get validation history for a content item."""
    cursor = db["content_validations"].find(
        {"content_id": content_id}
    ).sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


async def should_skip_revalidation(db, content_id: str, content_hash: str) -> bool:
    """Check if content hasn't changed — skip revalidation."""
    last = await db["content_validations"].find_one(
        {"content_id": content_id},
        sort=[("created_at", -1)]
    )
    if last and last.get("content_hash") == content_hash:
        return True
    return False


async def rollback_content(db, content_type: str, content_id: str) -> dict | None:
    """Find and return the last known-good version for rollback."""
    last_good = await db["content_validations"].find_one(
        {"content_id": content_id, "status": "PASS"},
        sort=[("created_at", -1)]
    )
    if last_good:
        return {
            "content_id": content_id,
            "last_good_score": last_good.get("overall_score", 0),
            "last_good_hash": last_good.get("content_hash", ""),
            "found": True,
        }
    return {"content_id": content_id, "found": False}


# ═══════════════════════════════════════════════════════════════════
# 12. PUBLISHING GATE
# ═══════════════════════════════════════════════════════════════════

def check_publish_gate(validation_result: dict, gate: dict | None = None) -> tuple[bool, list[str]]:
    """Check if content passes the publishing gate. Returns (allowed, reasons)."""
    g = gate or DEFAULT_PUBLISH_GATE
    reasons = []
    score = validation_result.get("overall_score", 0)
    tech = validation_result.get("dimensions", {}).get("technical_accuracy", 0)
    p0 = sum(1 for i in validation_result.get("issues", [])
             if i.get("severity") == "P0")

    if score < g.get("min_overall", 70):
        reasons.append(f"Overall score {score} below minimum {g['min_overall']}")
    if tech < g.get("min_technical", 70):
        reasons.append(f"Technical accuracy {tech} below minimum {g['min_technical']}")
    if p0 > g.get("max_p0_issues", 0):
        reasons.append(f"{p0} P0 issues (max allowed: {g['max_p0_issues']})")

    return (len(reasons) == 0, reasons)


# ═══════════════════════════════════════════════════════════════════
# 13. BATCH VALIDATION
# ═══════════════════════════════════════════════════════════════════

async def validate_all_paths(db, weights: dict | None = None) -> dict:
    """Validate all learning paths. Returns summary."""
    results = []
    async for path in db["learning_paths"].find({}):
        blocks = []
        async for block in db["learning_blocks"].find({"slug": path.get("slug", "")}):
            blocks.append(block)
        if blocks:
            vr = validate_path(path, blocks, weights)
            await save_validation_result(db, "learning_path",
                                         str(path.get("_id", "")), vr)
            results.append(vr)

    total = len(results)
    passing = sum(1 for r in results if r.get("status") == "PASS")
    avg_score = sum(r.get("overall_score", 0) for r in results) / total if total else 0

    return {
        "total_validated": total,
        "passing": passing,
        "failing": total - passing,
        "average_score": round(avg_score, 1),
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════════
# 14. CONVENIENCE: VALIDATE + SAVE IN ONE CALL
# ═══════════════════════════════════════════════════════════════════

async def validate_and_save_block(db, block: dict, path: dict | None = None,
                                  siblings: list[dict] | None = None,
                                  weights: dict | None = None) -> dict:
    """Validate a block, save result, update block with validation metadata."""
    result = validate_block(block, path, siblings, weights)

    # Save validation history
    await save_validation_result(db, "lesson",
                                 str(block.get("_id", "")), result)

    # Update block with validation metadata
    now = utcnow()
    await db["learning_blocks"].update_one(
        {"_id": block["_id"]},
        {"$set": {
            "validation_score": result.get("overall_score", 0),
            "validation_status": result.get("status", ""),
            "validation_dimensions": result.get("dimensions", {}),
            "validation_issues_count": len(result.get("issues", [])),
            "validation_mode": result.get("validation_mode", "DETERMINISTIC"),
            "last_validated_at": now,
            "updated_at": now,
        }}
    )

    await audit("learning_validator", "BLOCK_VALIDATED",
                str(block.get("_id", "")),
                {"score": result.get("overall_score", 0),
                 "status": result.get("status", ""),
                 "issues": len(result.get("issues", []))})

    return result


async def validate_and_save_path(db, path: dict, blocks: list[dict],
                                 weights: dict | None = None) -> dict:
    """Validate a full path, save result, update path with validation metadata."""
    result = validate_path(path, blocks, weights)

    await save_validation_result(db, "learning_path",
                                 str(path.get("_id", "")), result)

    now = utcnow()
    await db["learning_paths"].update_one(
        {"_id": path["_id"]},
        {"$set": {
            "validation_score": result.get("overall_score", 0),
            "validation_status": result.get("status", ""),
            "validation_dimensions": result.get("dimensions", {}),
            "path_validation_issues": [
                i["problem"] for i in result.get("issues", [])
                if i.get("severity") in ("P0", "P1")
            ],
            "last_validated_at": now,
            "updated_at": now,
        }}
    )

    await audit("learning_validator", "PATH_VALIDATED",
                str(path.get("_id", "")),
                {"score": result.get("overall_score", 0),
                 "status": result.get("status", ""),
                 "total_issues": result.get("total_issues", 0),
                 "blocks_passing": result.get("blocks_passing", 0)})

    return result
