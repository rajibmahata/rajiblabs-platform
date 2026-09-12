"""Learning Agent — autonomous mentor for RajibLabs.

Owns the complete lifecycle: Admin defines Topic+Duration(+Goal/Level) → Agent creates
roadmap → daily blocks → validation → MongoDB → RAG. Daily at 06:30 IST.

Principles:
- Human-centric, mentor beside you, not AI article.
- Practical-first: real-world scenario → simple explanation → code → try → exercise → homework → recap.
- Progressive: understands full path before generating a day, Day 5 never assumes unt taught knowledge.
"""
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone, timedelta

from app.config import get_settings
from app.database import get_db, utcnow
from app.services.notify import audit, log_error

log = logging.getLogger("rajiblabs")

def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80] or uuid.uuid4().hex[:8]

def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]

# ---------- Status vocabulary (single source of truth) ----------
PATH_STATUS_SYNONYMS = {
    "live": "active",
    "published": "active",
    "public": "active",
    "active": "active",
    "completed": "completed",
    "planned": "planned",
    "draft": "planned",
    "paused": "paused",
    "archived": "archived",
}

VISIBLE_PATH_STATUSES = ("active", "completed", "live", "published")
VISIBLE_BLOCK_STATUSES = ("published", "completed")

# Block status lifecycle: draft → generating → validating → needs_improvement → ready → published → archived
BLOCK_STATUS_LIFECYCLE = ("draft", "generating", "validating", "needs_improvement", "ready", "published", "completed", "archived")
BLOCK_IMMATURE_STATUSES = ("draft", "generating", "validating", "needs_improvement", "ready")


def normalize_path_status(raw: str) -> str:
    canon = PATH_STATUS_SYNONYMS.get((raw or "").strip().lower())
    if not canon:
        raise ValueError(f"Invalid status: {raw}")
    return canon


def is_path_visible(doc: dict | None) -> bool:
    return bool(doc) and doc.get("status") in VISIBLE_PATH_STATUSES

def _sanitize(text: str) -> str:
    for pat in [r"sk-[A-Za-z0-9]{10,}", r"ghp_[A-Za-z0-9]{10,}", r"Bearer\s+\S+"]:
        text = re.sub(pat, "***", text, flags=re.I)
    return text[:8000]

# ---------- Roadmap generation (intelligent, not hardcoded) ----------
async def _generate_roadmap(topic: str, duration: int, goal: str = "", level: str = "") -> list[dict]:
    """Use LLM to create a day-by-day roadmap, fallback to deterministic template."""
    topic = (topic or "").strip()
    goal = (goal or "").strip()
    level = (level or "beginner").strip() or "beginner"
    # Try LLM first (cheap, via shared orchestrator)
    try:
        from app.services.lead_ai import AIService
        from app.config import get_settings
        s = get_settings()
        if s.openai_api_key and s.openai_enabled:
            svc = AIService()
            if svc.configured:
                prompt = (
                    f"You are a senior mentor designing a {duration}-day learning path for a COMPLETE BEGINNER who knows nothing about '{topic}'.\n"
                    f"Level: {level}. Goal: {goal or 'Be able to practically use '+topic+' in real projects'}.\n"
                    "Design a progressive roadmap where each day builds on the previous:\n"
                    "Understand → Observe → Follow → Practice → Modify → Solve → Build.\n"
                    "Day 1 must be true fundamentals with no assumed knowledge. Day 2 must not assume Day 5 knowledge.\n"
                    "Focus on practical usefulness, not theory. Each day title must be concrete and action-oriented (e.g. 'Your First C# Program — Printing Hello' not 'Introduction to Types').\n"
                    "Return JSON with keys: prerequisites[] (0-3 things truly needed, or empty if none), roadmap: [{day: int, title: string, objective: string, why_matters: string}].\n"
                    "Rules: no generic fluff like 'Advanced Concepts', no invented prerequisites, titles must be specific to the topic.\n"
                    "Return JSON only."
                )
                out = await svc._complete(
                    [{"role": "system", "content": "You are a curriculum designer who creates practical, beginner-friendly roadmaps. Return JSON only."},
                     {"role": "user", "content": prompt[:3800]}],
                    max_tokens=1400, temperature=0.3, tag="learning-roadmap"
                )
                data = out.get("data", {})
                roadmap = data.get("roadmap", [])
                prereqs = data.get("prerequisites", [])
                if isinstance(roadmap, list) and len(roadmap) >= duration:
                    cleaned = []
                    for i, item in enumerate(roadmap[:duration], 1):
                        cleaned.append({
                            "day": i,
                            "title": str(item.get("title", f"Day {i}"))[:120],
                            "objective": str(item.get("objective", ""))[:300],
                            "why_matters": str(item.get("why_matters", ""))[:300],
                        })
                    return {"roadmap": cleaned, "prerequisites": prereqs[:5]}
    except Exception as e:
        log.warning("roadmap LLM failed for %s: %s", topic, e)
    # Deterministic fallback: generic progression, still useful — but topic-aware
    fallback_titles = [
        "First Steps — What is {t} and Why It Matters", "Setting Up — Your First {t} Environment",
        "Your First {t} Program — Seeing It Run", "Variables — Storing Information",
        "Control Flow — Making Decisions", "Functions — Reusing Code",
        "Working with Data — Collections", "Objects — Modeling Real Things",
        "Handling Errors Gracefully", "Putting It Together — Mini Project",
        "Testing Your Code", "Best Practices & Clean Code", "Building Something Real",
        "Next Steps — Where to Go From Here"
    ]
    roadmap = []
    for i in range(1, duration + 1):
        tmpl = fallback_titles[(i - 1) % len(fallback_titles)]
        title = tmpl.format(t=topic)
        if duration <= 7 and i == duration:
            title = f"Capstone — Build a Small {topic} Project"
        roadmap.append({"day": i, "title": title, "objective": f"Understand and practice {title.lower()}", "why_matters": f"Core building block for {topic}"})
    return {"roadmap": roadmap, "prerequisites": []}

# ---------- Daily block generation ----------
async def _generate_daily_block(topic: str, day: int, day_title: str, objective: str, why_matters: str, prev_context: str = "", *, duration: int = 0, full_roadmap: list[dict] | None = None, prev_blocks_summary: str = "") -> dict:
    """Generate a structured daily block via LLM + RAG grounding, fallback deterministic.
    
    This is the HEART of the mentor experience. Every lesson must feel like a patient mentor.
    """
    # RAG grounding: fetch trusted knowledge for this day's topic
    rag_context = ""
    try:
        from app.services import rag_query as _rq
        from app.config import get_settings
        if get_settings().rag_enabled:
            chunks = await _rq.retrieve(f"{topic} {day_title}", top_k=3)
            if chunks:
                rag_context = "\n".join(c.get("content", "")[:400] for c in chunks[:2])
    except Exception:
        pass

    # Build progressive context: full roadmap + previous days
    roadmap_ctx = ""
    if full_roadmap:
        roadmap_ctx = "Full path: " + " → ".join([f"Day {r.get('day')}: {r.get('title')}" for r in full_roadmap[:duration or len(full_roadmap)]])
    prev_ctx_full = prev_blocks_summary or prev_context

    # Try LLM — mentor tone, practical-first
    try:
        from app.services.lead_ai import AIService
        from app.config import get_settings
        s = get_settings()
        if s.openai_api_key and s.openai_enabled:
            svc = AIService()
            if svc.configured:
                is_first_day = day == 1
                is_last_day = duration and day == duration
                level_hint = "COMPLETE BEGINNER — knows nothing, no jargon without explanation" if is_first_day else "beginner who completed previous days"

                system_prompt = (
                    "You are a warm, patient mentor sitting beside a complete beginner. "
                    "You do NOT write textbook articles. You teach by story, example, and doing. "
                    "Your language is simple, friendly, short paragraphs (2-3 sentences each). "
                    "You introduce a technical term only AFTER explaining it in plain words. "
                    "You never jump to advanced concepts. You make the learner DO something every lesson."
                )

                user_prompt = f"""
Topic for the whole path: "{topic}" ({duration or '?'} days)
{roadmap_ctx}
Current lesson: Day {day} — "{day_title}"
Objective for today: {objective}
Why it matters: {why_matters}
Learner level: {level_hint}
{"This is DAY 1 — start from zero, no assumed knowledge, very gentle." if is_first_day else ""}
{"This is the FINAL day — include a small capstone and where to go next." if is_last_day else ""}
Previous lessons already covered (do NOT repeat, build on them):
{prev_ctx_full[:1200] or "(none — this is the start)"}

Verified knowledge (use only if relevant, never invent facts):
{rag_context[:900] if rag_context else "(no verified context — use general accurate knowledge)"}

TASK: Create a complete, practical lesson for Day {day}. Follow this EXACT structure. Keep each section concise and useful. Do not add fluff.

Required JSON keys (all strings unless noted):
{{
  "topic": "Short topic for today (same as Day title)",
  "learning_objective": "One clear sentence: After today you will be able to ...",
  "why_matters": "2-3 sentences, real-world relevance",
  "real_world_example": "A relatable story/scenario BEFORE any theory. For programming: use concrete objects like Customer (name, email), Product (name, price), Shopping Cart. Make it vivid and beginner-friendly.",
  "simple_explanation": "Explain the core idea in plain words as if to a friend, 2-3 short paragraphs max, no jargon-first",
  "concept_explanation": "Slightly deeper but still simple — connect the real-world example to the technical concept. Introduce the term naturally here.",
  "step_by_step": ["3-5 concrete steps the learner can follow, action-oriented, e.g. '1. Create a new variable called customerName'"],
  "practical_example": "Describe the practical example you will code/demo, in one paragraph, connected to the real-world scenario",
  "examples": [
    {{
      "title": "Example title (e.g. Customer class - your first object)",
      "code": "Runnable code. For C# must be complete with using System; class Program {{ static void Main() {{ ... }} }}, for Python must be runnable. Keep beginner-level, no enterprise patterns on Day 1-4.",
      "explanation": "Line-by-line friendly explanation of what the code does, not just what it is",
      "expected_output": "What the learner will see when they run it"
    }}
  ],
  "try_it_yourself": "One small tweak to try immediately (e.g. 'Change the product price to 99 and see what happens')",
  "common_mistakes": ["Mistake 1 with why it happens and how to fix", "Mistake 2..."],
  "exercise": "A hands-on exercise the learner can do in 5-10 minutes, clearly matched to today's level. Must be doable with only knowledge up to Day {day}.",
  "homework": "A slightly bigger take-home task (15-20 min) that reinforces today and previews tomorrow, still within current level",
  "challenge": "Optional stretch goal for curious learners (one sentence)",
  "quick_review": ["3 bullet recap of key takeaways"],
  "what_you_can_do_now": ["2-3 concrete abilities, e.g. 'Create a Customer class with 2 properties'"],
  "questions": ["3 check-yourself questions"],
  "next_preview": "One sentence teaser for Day {day+1} that connects logically"
}}

Rules:
- No textbook tone, no huge paragraphs, no repeating the topic definition.
- No unexplained terminology. If you say 'class', first say 'a class is like a blueprint for creating objects — think of a cookie cutter'.
- Code must be correct, runnable, and use the simplest possible example for this day's level.
- Exercises/homework must be exactly at this day's level — Day 2 must not require Day 5 knowledge.
- If topic is not programming (e.g. design, theory), provide practical example without code or with pseudocode, but still follow the structure.
- Return JSON only, no markdown wrapper.
"""
                out = await svc._complete(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": _sanitize(user_prompt[:6500])}],
                    max_tokens=3000, temperature=0.35, tag="learning-block"
                )
                data = out.get("data", {})
                if data.get("topic") and (data.get("concept_explanation") or data.get("simple_explanation")):
                    # Normalize and validate we got mentor-quality content
                    def _s(v, n): return str(v or "")[:n].strip()
                    def _arr(v, n): return [str(x)[:500] for x in (v or [])][:n] if isinstance(v, list) else []
                    def _ex_arr(v):
                        if not isinstance(v, list): return []
                        out_e=[]
                        for e in v[:2]:
                            if not isinstance(e, dict): continue
                            out_e.append({
                                "title": _s(e.get("title"), 120),
                                "code": _s(e.get("code"), 4000),
                                "explanation": _s(e.get("explanation"), 1000),
                                "expected_output": _s(e.get("expected_output"), 600),
                            })
                        return out_e

                    result = {
                        "topic": _s(data.get("topic", day_title), 120),
                        "learning_objective": _s(data.get("learning_objective", objective), 400),
                        "why_matters": _s(data.get("why_matters", why_matters), 500),
                        "real_world_example": _s(data.get("real_world_example"), 1200),
                        "simple_explanation": _s(data.get("simple_explanation"), 2000),
                        "concept_explanation": _s(data.get("concept_explanation", data.get("simple_explanation")), 3500),
                        "step_by_step": _arr(data.get("step_by_step"), 6),
                        "practical_example": _s(data.get("practical_example"), 1000),
                        "examples": _ex_arr(data.get("examples")),
                        "try_it_yourself": _s(data.get("try_it_yourself"), 600),
                        "common_mistakes": _arr(data.get("common_mistakes"), 5),
                        "exercise": _s(data.get("exercise"), 1200),
                        "homework": _s(data.get("homework"), 1200),
                        "challenge": _s(data.get("challenge"), 800),
                        "quick_review": _arr(data.get("quick_review"), 5),
                        "what_you_can_do_now": _arr(data.get("what_you_can_do_now"), 5),
                        "questions": _arr(data.get("questions"), 5),
                        "next_preview": _s(data.get("next_preview"), 400),
                    }
                    # Ensure at least one example has code if programming topic
                    if not result["examples"]:
                        result["examples"] = [{"title": f"{day_title} example", "code": f"// {topic} Day {day}\nconsole.log('Hello {topic}');", "explanation": "Starter example", "expected_output": "Hello"}]
                    return result
    except Exception as e:
        log.warning("daily block LLM failed day %s %s: %s", day, topic, e)
    # Deterministic fallback — STILL mentor-like, not generic lorem
    # Build a practical fallback based on topic
    is_code_topic = any(k in topic.lower() for k in ["c#", ".net", "asp.net", "python", "javascript", "java", "programming", "react", "angular", "node", "sql", "code","blazor","backend","frontend"])
    if is_code_topic:
        # Use shopping app scenario as anchor for code topics
        real_world = f"Imagine you are building a small shopping app. Today we focus on {day_title}. Think of a Customer who has a name and email, and a Product with name and price — we will model this with {topic}."
        simple = f"Today you will learn {day_title}. {objective} We will start with a tiny, runnable example and then you will tweak it yourself."
        code_title = f"{day_title} — Your first object"
        if "c#" in topic.lower() or "asp.net" in topic.lower() or ".net" in topic.lower():
            code = """using System;

class Product
{
    public string Name { get; set; }
    public decimal Price { get; set; }
}

class Program
{
    static void Main()
    {
        var p = new Product { Name = "Laptop", Price = 999 };
        Console.WriteLine($"{p.Name} costs ${p.Price}");
    }
}"""
            explanation = "We define a Product as a blueprint (class) with two pieces of data. Then we create one product and print it. Try changing the price."
            expected = "Laptop costs 999"
        elif "python" in topic.lower():
            code = """class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

p = Product("Laptop", 999)
print(f"{p.name} costs {p.price}")"""
            explanation = "We create a blueprint for a Product, make one, and print it. Change the values and run again."
            expected = "Laptop costs 999"
        else:
            code = f"// {topic} — {day_title}\nconsole.log('Day {day}: {day_title}');\nconsole.log('Try changing the text and running again');"
            explanation = "A minimal runnable example to see immediate output."
            expected = f"Day {day}: {day_title}"
        return {
            "topic": day_title,
            "learning_objective": objective or f"Understand {day_title} and run your first example",
            "why_matters": why_matters or f"Every {topic} project uses {day_title.lower()} — this is your building block",
            "real_world_example": real_world,
            "simple_explanation": simple,
            "concept_explanation": simple + " " + why_matters,
            "step_by_step": [f"1. Understand what {day_title} means with the shopping example", f"2. Look at the tiny code — read it line by line", f"3. Run it and see '{expected}'", "4. Change one value and run again"],
            "practical_example": f"We model a Product from our shopping story with {topic}.",
            "examples": [{"title": code_title, "code": code, "explanation": explanation, "expected_output": expected}],
            "try_it_yourself": "Change the product name to 'Phone' and price to 499, then run again. What changed?",
            "common_mistakes": ["Forgetting a semicolon or bracket — the error points to the line before", "Mixing up Name vs name (C# is case-sensitive)"],
            "exercise": f"Create a Customer with Name and Email, print it like we did for Product.",
            "homework": f"Add a second product and a method that calculates total price for both. Test it.",
            "challenge": "Can you add a discount: if price > 500, show 10% off?",
            "quick_review": [f"{day_title} lets you model real things", "You ran code and saw {expected}", "Next you will build on this"],
            "what_you_can_do_now": [f"Create a simple {day_title} example", "Explain it to a friend in plain words"],
            "questions": [f"What does {day_title} do?", f"Why do we model a Product this way?", "What happens if you change the price?"],
            "next_preview": f"Tomorrow we will take this {day_title} and use it in a slightly bigger scenario.",
        }
    else:
        # Non-code topic fallback
        return {
            "topic": day_title,
            "learning_objective": objective,
            "why_matters": why_matters or f"Helps you master {topic}",
            "real_world_example": f"Think of a real situation where {day_title.lower()} matters — for example, planning a small project or explaining it to a teammate.",
            "simple_explanation": f"Today we explore {day_title}. {objective} We will use a simple story to make it click.",
            "concept_explanation": f"{day_title} in {topic} helps you solve real problems. We start simple, then connect to practice.",
            "step_by_step": [f"Understand {day_title} with a simple story", "See how it works in practice", "Try a small exercise yourself"],
            "practical_example": f"A practical scenario for {day_title} with {topic}.",
            "examples": [{"title": f"{day_title} example", "code": "", "explanation": "Illustrative example", "expected_output": ""}],
            "try_it_yourself": f"Explain {day_title} to someone using your own example.",
            "common_mistakes": ["Trying to memorize instead of doing", "Skipping the exercise"],
            "exercise": f"Write down your own example for {day_title} with {topic}.",
            "homework": f"Find a real-world case where {day_title.lower()} is used and note what you learned.",
            "challenge": f"Can you teach {day_title} to someone else?",
            "quick_review": [f"Reviewed {day_title}", "Connected to real example"],
            "what_you_can_do_now": [f"Explain {day_title} clearly"],
            "questions": [f"What is {day_title}?", f"Why does it matter?", "Can you give an example?"],
            "next_preview": f"Next: Day {day+1}",
        }

def _is_weak_block(block: dict) -> tuple[bool, str]:
    """Detect weak/generic lessons that should be regenerated."""
    ce = (block.get("concept_explanation") or block.get("simple_explanation") or "")
    ex = block.get("exercise") or ""
    rw = block.get("real_world_example") or ""
    steps = block.get("step_by_step") or []
    examples = block.get("examples") or []
    # Heuristics
    if len(ce) < 200:
        return True, "concept_explanation too short (<200)"
    if "This builds on previous days" in ce and len(ce) < 400:
        return True, "generic fallback phrase"
    if len(steps) < 3 or any("Step 1: Understand" in s and "concept" in s for s in steps):
        # generic steps like "Step 1: Understand X concept 1"
        if len(ce) < 600:
            return True, "generic step_by_step"
    if not rw or len(rw) < 80:
        return True, "missing real_world_example"
    if not examples or not any(e.get("code", "").strip() for e in examples):
        # allow non-code topics to have empty code, but check if topic is code-like
        topic = (block.get("topic") or "").lower()
        if any(k in topic for k in ["c#", "python", "code", "programming", ".net"]):
            return True, "missing code example for code topic"
    if len(ex) < 30 or "Try modifying the example" in ex and len(ex) < 80:
        return True, "generic exercise"
    return False, ""

def _validate_block(block: dict) -> tuple[bool, list[str]]:
    """Mentor-quality validation: required fields, code, exercises, no jargon dump."""
    issues = []
    # Required
    if not block.get("learning_objective") or len(block["learning_objective"]) < 15:
        issues.append("missing learning_objective")
    ce = block.get("concept_explanation") or block.get("simple_explanation") or ""
    if not ce or len(ce) < 80:
        issues.append("concept_explanation too short (<80)")
    if len(ce) > 5000:
        issues.append("concept_explanation too long")
    # Must have practical grounding
    if not block.get("real_world_example") or len(block["real_world_example"]) < 50:
        issues.append("missing real_world_example")
    if not block.get("simple_explanation") and len(ce) < 100:
        issues.append("missing simple_explanation")
    steps = block.get("step_by_step") or []
    if len(steps) < 3:
        issues.append("step_by_step needs 3-5 steps")
    # Check for huge paragraphs (should be short)
    for para in ce.split("\n\n"):
        if len(para) > 800:
            issues.append("paragraph too long (>800 chars) — split for readability")
            break
    # Generic AI language detection
    generic_phrases = ["As an AI", "In conclusion", "In summary, this lesson", "It is important to note"]
    for gp in generic_phrases:
        if gp.lower() in ce.lower():
            issues.append(f"generic AI phrase: {gp}")
    # Code syntax check
    for ex in block.get("examples", [])[:2]:
        code = ex.get("code", "")
        if code.strip():
            # Python
            if "def " in code or "import " in code or "class " in code and "public " not in code:
                # Heuristic: if it looks like Python, try parse
                if "using System" not in code and "Console.WriteLine" not in code:
                    try:
                        import ast
                        # Only try Python parse if not C#
                        if ";" not in code or "python" in (ex.get("title","").lower()):
                            ast.parse(code)
                    except SyntaxError as e:
                        issues.append(f"code syntax: {e.msg}")
            # C# basic check: must have Main if it's C# example
            if "using System" in code and "static void Main" not in code:
                issues.append("C# example missing Main method")
    # Exercises
    if not block.get("exercise") or len(block["exercise"]) < 20:
        issues.append("missing exercise")
    if block.get("exercise") and len(block["exercise"]) < 30:
        issues.append("exercise too short")
    # Homework should be present
    if not block.get("homework") or len(block["homework"]) < 20:
        issues.append("missing homework")
    # Common mistakes
    if not block.get("common_mistakes") or len(block.get("common_mistakes") or []) < 1:
        issues.append("missing common_mistakes")
    # Quick review
    if not block.get("quick_review") or len(block.get("quick_review") or []) < 2:
        issues.append("quick_review needs 2-3 bullets")
    # What you can do now
    if not block.get("what_you_can_do_now") or len(block.get("what_you_can_do_now") or []) < 1:
        issues.append("missing what_you_can_do_now")
    return (len(issues) == 0, issues)


# ---------- Beginner-focused quality validator ----------
_BEGINNER_PHRASES = frozenset({
    "as an ai", "in conclusion", "in summary, this lesson", "it is important to note",
    "it is worth noting", "furthermore", "moreover", "in addition to",
    "it should be noted", "as mentioned earlier", "as we have discussed",
    "this is a complex topic", "advanced concept", "advanced topic",
})

def validate_block_quality(block: dict, day: int = 0, topic: str = "", prev_block: dict | None = None) -> tuple[bool, list[str], list[str]]:
    """Beginner-focused quality validation. Returns (passed, issues, improvements).

    Checks whether a real beginner can understand, practice, and learn from this
    lesson. Goes beyond structural validation to assess pedagogical quality.
    """
    issues: list[str] = []
    improvements: list[str] = []

    ce = (block.get("concept_explanation") or block.get("simple_explanation") or "")
    rw = block.get("real_world_example") or ""
    steps = block.get("step_by_step") or []
    examples = block.get("examples") or []
    exercise = block.get("exercise") or ""
    homework = block.get("homework") or ""
    obj = block.get("learning_objective") or ""
    why = block.get("why_matters") or ""
    try_it = block.get("try_it_yourself") or ""
    mistakes = block.get("common_mistakes") or []
    review = block.get("quick_review") or []
    abilities = block.get("what_you_can_do_now") or []

    # 1. Objective clarity — must state what learner will DO, not just know
    if obj:
        doing_words = {"create", "write", "build", "use", "run", "explain", "identify", "define",
                       "apply", "debug", "read", "modify", "add", "remove", "print", "calculate"}
        obj_words = set(obj.lower().split())
        if not doing_words & obj_words:
            improvements.append("learning_objective should state what the learner will DO (create, write, build, use...)")

    # 2. Real-world example must be concrete, not abstract
    if rw:
        abstract_markers = ["in general", "typically", "often", "usually", "in many cases", "broadly speaking"]
        if any(m in rw.lower() for m in abstract_markers) and len(rw) < 150:
            improvements.append("real_world_example is too abstract — use a concrete story with specific names/numbers")
        if len(rw) < 100:
            issues.append("real_world_example too short (<100 chars) — beginners need vivid scenarios")

    # 3. Simple explanation must avoid jargon-dumping
    if ce:
        # Check if technical terms appear before explanation
        jargon_heavy = len([w for w in ce.split() if len(w) > 12 and w[0].isupper()]) > 5
        if jargon_heavy:
            improvements.append("concept_explanation may have too many unexplained technical terms — explain each before naming it")
        # Check paragraph length — beginners need short paragraphs
        paras = [p for p in ce.split("\n\n") if p.strip()]
        long_paras = [p for p in paras if len(p) > 400]
        if long_paras:
            improvements.append("concept_explanation has paragraphs >400 chars — split into shorter paragraphs for beginners")

    # 4. Steps must be concrete and actionable
    if steps:
        vague_steps = [s for s in steps if any(v in s.lower() for v in ["understand", "learn about", "study", "review"])]
        if vague_steps and len(steps) <= 3:
            improvements.append("step_by_step has vague steps (understand/learn/study) — make each step a concrete action")

    # 5. Code examples must be runnable and explained
    if examples:
        for ex in examples[:2]:
            code = ex.get("code", "")
            explanation = ex.get("explanation", "")
            if code and not explanation:
                issues.append(f"code example '{ex.get('title', '')}' has no explanation — beginners need line-by-line guidance")
            if code and len(code) > 500 and day <= 3:
                improvements.append(f"code example is long ({len(code)} chars) — keep early lessons under 300 chars")

    # 6. Exercise must match today's level and be doable
    if exercise:
        if day > 1 and any(kw in exercise.lower() for kw in ["class ", "interface ", "async ", "await ", "linq"]):
            if day <= 3:
                improvements.append("exercise may be too advanced for early days — ensure it only uses concepts taught so far")
        if len(exercise) < 50:
            issues.append("exercise too short (<50 chars) — needs clear instructions a beginner can follow")

    # 7. Try-it-yourself must be a concrete tweak, not a vague suggestion
    if try_it:
        vague_try = ["try", "experiment", "play around", "explore"]
        if any(v in try_it.lower() for v in vague_try) and len(try_it) < 60:
            improvements.append("try_it_yourself is too vague — give a specific change to make (e.g. 'Change the price to 99 and run again')")

    # 8. Common mistakes must explain WHY, not just WHAT
    if mistakes:
        shallow = [m for m in mistakes if len(m) < 30 or "don't" in m.lower() and "because" not in m.lower()]
        if shallow:
            improvements.append("common_mistakes should explain WHY the mistake happens, not just what to avoid")

    # 9. Quick review must be a real recap, not filler
    if review:
        filler = [r for r in review if len(r) < 15 or "covered" in r.lower() and "today" in r.lower()]
        if filler:
            improvements.append("quick_review has filler items — each bullet should name a specific takeaway")

    # 10. What-you-can-do-now must be concrete abilities
    if abilities:
        vague_abilities = [a for a in abilities if "understand" in a.lower() or "know" in a.lower()]
        if vague_abilities:
            improvements.append("what_you_can_do_now has vague abilities (understand/know) — state concrete things the learner can CREATE or DO")

    # 11. Why-matters must connect to real life, not just say "important"
    if why:
        if len(why) < 40:
            issues.append("why_matters too short — explain real-world relevance in 2-3 sentences")
        generic_why = ["important", "useful", "essential", "fundamental"]
        if any(g in why.lower() for g in generic_why) and len(why) < 80:
            improvements.append("why_matters sounds generic — connect to a specific real scenario the learner cares about")

    # 12. Logical flow from previous day
    if prev_block and day > 1:
        prev_obj = (prev_block.get("learning_objective") or "").lower()
        curr_obj = obj.lower()
        # Check if this lesson repeats the previous one
        if prev_obj and curr_obj:
            prev_words = set(prev_obj.split()) - {"the", "a", "an", "and", "or", "to", "in", "of", "for", "is", "are"}
            curr_words = set(curr_obj.split()) - {"the", "a", "an", "and", "or", "to", "in", "of", "for", "is", "are"}
            overlap = prev_words & curr_words
            if len(overlap) > min(len(prev_words), len(curr_words)) * 0.6:
                improvements.append(f"Day {day} objective overlaps heavily with Day {day-1} — should build on it, not repeat it")

    passed = len(issues) == 0
    return passed, issues, improvements


def validate_path_coherence(path: dict, blocks: list[dict]) -> tuple[bool, list[str]]:
    """Path-level validation: checks coherence across the entire learning path.

    Validates: missing prerequisites, difficulty jumps, repeated topics,
    disconnected lessons, missing practical progression, unrealistic duration.
    """
    issues: list[str] = []
    roadmap = path.get("roadmap", [])
    duration = int(path.get("duration", 0))
    topic = path.get("topic", "")

    if not blocks:
        issues.append("No blocks generated yet")
        return False, issues

    # 1. Check for repeated topics across days
    titles = [b.get("title") or b.get("topic", "") for b in blocks]
    seen_titles: dict[str, int] = {}
    for i, t in enumerate(titles):
        normalized = t.lower().strip()
        if normalized in seen_titles:
            issues.append(f"Day {i+1} title repeats Day {seen_titles[normalized]+1}: '{t}'")
        seen_titles[normalized] = i

    # 2. Check for difficulty jumps (heuristic: day N should not have concepts from day N+3+)
    all_objectives = [(b.get("day_number", 0), (b.get("learning_objective") or "").lower()) for b in blocks]
    for i, (day, obj) in enumerate(all_objectives):
        if i < len(all_objectives) - 1:
            next_obj = all_objectives[i+1][1] if i+1 < len(all_objectives) else ""
            # If next day's objective mentions concepts not introduced yet, flag it
            if day == 1 and any(kw in obj for kw in ["interface", "generic", "async", "linq", "delegate"]):
                issues.append(f"Day {day} objective mentions advanced concepts too early for a beginner path")

    # 3. Check practical progression — later days should have exercises/homework
    published = [b for b in blocks if b.get("status") in ("published", "completed")]
    if len(published) > 2:
        recent = published[-3:]
        for b in recent:
            if not b.get("exercise"):
                issues.append(f"Day {b.get('day_number')} published without exercise — every lesson needs hands-on practice")
            if not b.get("examples"):
                issues.append(f"Day {b.get('day_number')} published without code example")

    # 4. Check duration realism
    if duration > 0 and len(blocks) < duration:
        missing = duration - len(blocks)
        if missing > duration * 0.5:
            issues.append(f"Only {len(blocks)}/{duration} days generated — {missing} days missing")

    # 5. First day must be gentle
    first = next((b for b in blocks if b.get("day_number") == 1), None)
    if first:
        if first.get("day_number") == 1:
            obj_text = (first.get("learning_objective") or "").lower()
            if any(kw in obj_text for kw in ["interface", "generic", "async", "exception", "linq"]):
                issues.append("Day 1 objective mentions advanced concepts — first day must be true fundamentals")

    # 6. Check that prerequisites are reasonable
    prereqs = path.get("prerequisites", [])
    if len(prereqs) > 3:
        issues.append(f"Too many prerequisites ({len(prereqs)}) — aim for 0-3 for a beginner path")

    passed = len(issues) == 0
    return passed, issues

# ---------- Public API used by scheduler and admin ----------
async def create_learning_path(topic: str, duration: int, goal: str = "", level: str = "beginner", created_by: str = "admin") -> dict:
    db = get_db()
    slug = _slug(topic)
    existing_active = await db["learning_paths"].find_one({"slug": slug, "status": "active"})
    if existing_active:
        pass
    roadmap_data = await _generate_roadmap(topic, duration, goal, level)
    now = utcnow()
    doc = {
        "slug": slug,
        "topic": topic.strip(),
        "duration": int(duration),
        "goal": goal.strip(),
        "level": level.strip() or "beginner",
        "status": "planned",
        "prerequisites": roadmap_data.get("prerequisites", []),
        "roadmap": roadmap_data.get("roadmap", []),
        "current_day": 0,
        "progress": 0,
        "content_hash": _hash(topic, str(duration), goal),
        "version": 1,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
        "last_run_at": None,
        "next_run_at": now,
    }
    dup = await db["learning_paths"].find_one({"slug": slug, "content_hash": doc["content_hash"]})
    if dup:
        return dup
    res = await db["learning_paths"].insert_one(doc)
    doc["_id"] = res.inserted_id
    for day in roadmap_data.get("roadmap", []):
        block_doc = {
            "path_id": res.inserted_id,
            "slug": slug,
            "day_number": day["day"],
            "title": day["title"],
            "topic": day["title"],
            "status": "planned",
            "learning_objective": day.get("objective", ""),
            "why_matters": day.get("why_matters", ""),
            "content_hash": "",
            "version": 1,
            "generated_at": None,
            "validated_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await db["learning_blocks"].insert_one(block_doc)
    await audit(created_by, "LEARNING_PATH_CREATE", slug, {"duration": duration})
    return doc

async def run_daily(triggered_by: str = "scheduler") -> dict:
    """Daily 06:30 IST job: inspect active paths, generate/validate next block."""
    db = get_db()
    from app.services import agent_config
    cfg = await agent_config.get_agent(db, "rajiblabs-learning") if "get_agent" in dir(agent_config) else None
    if cfg and not cfg.get("enabled", True):
        return {"status": "no_action", "reason": "agent disabled"}
    now = utcnow()
    cur = db["learning_paths"].find({"status": {"$in": ["active", "live", "published"]}})
    paths = [d async for d in cur]
    if not paths:
        cur2 = db["learning_paths"].find({"status": "planned"}).sort("created_at", 1).limit(1)
        first = [d async for d in cur2]
        if first:
            await db["learning_paths"].update_one({"_id": first[0]["_id"]}, {"$set": {"status": "active", "updated_at": now}})
            paths = first
            paths[0]["status"] = "active"
    results = []
    for path in paths:
        slug = path["slug"]
        duration = int(path.get("duration", 10))
        blocks = [d async for d in db["learning_blocks"].find({"path_id": path["_id"]}).sort("day_number", 1)]
        next_block = None
        for b in blocks:
            if b.get("status") in ("planned", "needs_review"):
                next_block = b
                break
            # Also check if published block is weak — should be improved
            if b.get("status") == "published":
                weak, reason = _is_weak_block(b)
                if weak:
                    log.info("Block %s day %s is weak (%s) — will regenerate", slug, b.get("day_number"), reason)
                    next_block = b
                    break
        if not next_block:
            if all(b.get("status") in ("published", "completed", "archived") for b in blocks) and len(blocks) >= duration:
                await db["learning_paths"].update_one({"_id": path["_id"]}, {"$set": {"status": "completed", "progress": 100, "updated_at": now}})
                results.append({"path": slug, "action": "completed"})
                continue
            else:
                max_day = max([b.get("day_number", 0) for b in blocks] or [0])
                if max_day < duration:
                    roadmap = path.get("roadmap", [])
                    title = roadmap[max_day]["title"] if max_day < len(roadmap) else f"Day {max_day+1}"
                    obj = roadmap[max_day] if max_day < len(roadmap) else {"title": title, "objective": "", "why_matters": ""}
                    nb = {
                        "path_id": path["_id"], "slug": slug, "day_number": max_day+1,
                        "title": title, "topic": title, "status": "planned",
                        "learning_objective": obj.get("objective",""), "why_matters": obj.get("why_matters",""),
                        "content_hash": "", "version": 1, "created_at": now, "updated_at": now,
                    }
                    res = await db["learning_blocks"].insert_one(nb)
                    nb["_id"] = res.inserted_id
                    next_block = nb
        if not next_block:
            results.append({"path": slug, "action": "no_action", "reason": "no planned block"})
            continue
        # Build progressive context: full roadmap + previous blocks summary
        prev_ctx = ""
        prev_summary = ""
        if next_block["day_number"] > 1:
            prev_blocks = [b for b in blocks if b.get("day_number", 0) < next_block["day_number"]]
            # Summarize previous days for the LLM
            parts = []
            for pb in prev_blocks[-3:]:  # last 3 for context window
                parts.append(f"Day {pb.get('day_number')}: {pb.get('title') or pb.get('topic')} — {pb.get('learning_objective','')[:120]}")
            prev_summary = "\n".join(parts)
            prev_ctx = prev_summary
        # Also include full roadmap for global understanding
        full_roadmap = path.get("roadmap", [])
        gen = await _generate_daily_block(
            path["topic"], next_block["day_number"], next_block.get("title",""), 
            next_block.get("learning_objective",""), next_block.get("why_matters",""), 
            prev_ctx, duration=duration, full_roadmap=full_roadmap, prev_blocks_summary=prev_summary
        )
        ok, issues = _validate_block(gen)
        new_hash = _hash(gen.get("concept_explanation",""), gen.get("exercise",""), gen.get("real_world_example",""))
        # If hash matches and not weak, skip
        if next_block.get("content_hash") == new_hash and next_block.get("status") == "published":
            weak, _ = _is_weak_block(next_block)
            if not weak:
                results.append({"path": slug, "day": next_block["day_number"], "action": "unchanged", "hash": new_hash})
                continue
        if not ok:
            await db["learning_blocks"].update_one({"_id": next_block["_id"]}, {"$set": {
                "status": "needs_review", "content_hash": new_hash, "validation_issues": issues, "updated_at": now,
                **gen
            }})
            results.append({"path": slug, "day": next_block["day_number"], "action": "needs_review", "issues": issues})
            continue
        # Structural validation passed — now run beginner-focused quality validation
        prev_block_for_quality = next(
            (b for b in blocks if b.get("day_number", 0) == next_block["day_number"] - 1), None
        )
        q_passed, q_issues, q_improvements = validate_block_quality(
            gen, day=next_block["day_number"], topic=path["topic"], prev_block=prev_block_for_quality
        )
        all_quality = q_issues + q_improvements
        if not q_passed or q_improvements:
            # Quality needs improvement — store feedback but still publish if structurally valid
            # Blocks with quality issues get published with improvement notes for the next regeneration cycle
            update_doc = {
                **gen,
                "status": "published",
                "content_hash": new_hash,
                "version": (next_block.get("version", 1) + 1),
                "generated_at": now,
                "validated_at": now,
                "updated_at": now,
                "validation_issues": q_issues,
                "quality_improvements": q_improvements,
            }
            await db["learning_blocks"].update_one({"_id": next_block["_id"]}, {"$set": update_doc})
            # Run quality validation again on next cycle (will regenerate if issues found)
            results.append({"path": slug, "day": next_block["day_number"], "action": "published_with_notes",
                           "issues": q_issues, "improvements": q_improvements})
        else:
            update_doc = {
                **gen,
                "status": "published",
                "content_hash": new_hash,
                "version": (next_block.get("version", 1) + 1),
                "generated_at": now,
                "validated_at": now,
                "updated_at": now,
                "validation_issues": [],
                "quality_improvements": [],
            }
            await db["learning_blocks"].update_one({"_id": next_block["_id"]}, {"$set": update_doc})
            results.append({"path": slug, "day": next_block["day_number"], "action": "published"})
        published_count = await db["learning_blocks"].count_documents({"path_id": path["_id"], "status": {"$in": ["published", "completed"]}})
        if next_block.get("status") == "planned":
            published_count += 1
        progress = int((published_count / duration) * 100) if duration else 0
        await db["learning_paths"].update_one({"_id": path["_id"]}, {"$set": {"current_day": next_block["day_number"], "progress": min(100, progress), "updated_at": now, "last_run_at": now}})
        try:
            from app.services import rag_ingest
            content_parts = [
                gen.get('topic',''),
                gen.get('learning_objective',''),
                gen.get('real_world_example',''),
                gen.get('simple_explanation',''),
                gen.get('concept_explanation',''),
                gen.get('practical_example',''),
            ]
            # include code as well for RAG
            for ex in gen.get('examples', [])[:1]:
                content_parts.append(ex.get('code',''))
                content_parts.append(ex.get('explanation',''))
            content_parts.extend([gen.get('exercise',''), gen.get('homework','')])
            content = "\n".join([c for c in content_parts if c])
            await rag_ingest.upsert_document(
                "learning", f"learning:{slug}:{next_block['day_number']}",
                f"{path['topic']} — Day {next_block['day_number']}: {gen['topic']}",
                content, tags=["learning", slug], url=f"https://rajiblabs.com/learning/{slug}/day/{next_block['day_number']}"
            )
        except Exception as e:
            log.warning("learning RAG failed %s day %s: %s", slug, next_block["day_number"], e)
        results.append({"path": slug, "day": next_block["day_number"], "action": "published"})
    # Path-level coherence validation after processing all paths
    for path in paths:
        slug = path["slug"]
        all_blocks = [b async for b in db["learning_blocks"].find({"path_id": path["_id"]}).sort("day_number", 1)]
        path_ok, path_issues = validate_path_coherence(path, all_blocks)
        if path_issues:
            await db["learning_paths"].update_one({"_id": path["_id"]}, {"$set": {
                "path_validation_issues": path_issues, "updated_at": utcnow()
            }})
            results.append({"path": slug, "action": "path_review", "issues": path_issues})
    run_doc = {"triggered_by": triggered_by, "results": results, "started_at": now, "finished_at": utcnow(), "status": "success" if results else "no_action"}
    await db["learning_agent_runs"].insert_one(run_doc)
    try:
        await audit(triggered_by, "LEARNING_AGENT_RUN", "daily", {"results": results})
    except: pass
    return {"status": "success", "results": results}

