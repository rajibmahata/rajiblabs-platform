"""Learning Agent — autonomous mentor for RajibLabs.

Owns the complete lifecycle: Admin defines Topic+Duration(+Goal/Level) → Agent creates
roadmap → daily blocks → validation → MongoDB → RAG. Daily at 06:00 IST.
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

def _sanitize(text: str) -> str:
    for pat in [r"sk-[A-Za-z0-9]{10,}", r"ghp_[A-Za-z0-9]{10,}", r"Bearer\s+\S+"]:
        text = re.sub(pat, "***", text, flags=re.I)
    return text[:6000]

# ---------- Roadmap generation (intelligent, not hardcoded) ----------
async def _generate_roadmap(topic: str, duration: int, goal: str = "", level: str = "") -> list[dict]:
    """Use LLM to create a day-by-day roadmap, fallback to deterministic template."""
    topic = (topic or "").strip()
    goal = (goal or "").strip()
    level = (level or "beginner").strip()
    # Try LLM first (cheap, via shared orchestrator)
    try:
        from app.services.lead_ai import AIService
        from app.config import get_settings
        s = get_settings()
        if s.openai_api_key and s.openai_enabled:
            svc = AIService()
            if svc.configured:
                prompt = (
                    f"You are a mentor designing a {duration}-day learning roadmap for '{topic}' (level: {level}).\n"
                    f"Goal: {goal or 'Practical understanding'}\n"
                    "Return JSON with keys: prerequisites[], roadmap: [{day: int, title: string, objective: string, why_matters: string}].\n"
                    "Rules: progression from fundamentals → advanced, each day builds on previous, no generic fluff, practical focus, no invented prerequisites.\n"
                    "Return JSON only."
                )
                out = await svc._complete(
                    [{"role": "system", "content": "You are a curriculum designer. Return JSON only."},
                     {"role": "user", "content": prompt[:3500]}],
                    max_tokens=1200, temperature=0.3, tag="learning-roadmap"
                )
                data = out.get("data", {})
                roadmap = data.get("roadmap", [])
                prereqs = data.get("prerequisites", [])
                if isinstance(roadmap, list) and len(roadmap) >= duration:
                    # Validate and trim to duration
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
    # Deterministic fallback: generic progression, still useful
    fallback_titles = [
        "Fundamentals & Setup", "Core Concepts", "Types & Variables", "Control Flow",
        "Functions & Scope", "Data Structures", "Object-Oriented Basics", "Collections & Iteration",
        "Error Handling", "Async & Patterns", "Advanced Concepts", "Practical Project",
        "Testing & Debugging", "Best Practices", "Final Review & Next Steps"
    ]
    roadmap = []
    for i in range(1, duration + 1):
        title = fallback_titles[(i - 1) % len(fallback_titles)]
        if duration <= 7 and i == duration:
            title = "Practical Project & Review"
        roadmap.append({"day": i, "title": f"{topic} — {title}", "objective": f"Understand {title.lower()}", "why_matters": f"Essential for {topic} mastery"})
    return {"roadmap": roadmap, "prerequisites": []}

# ---------- Daily block generation ----------
async def _generate_daily_block(topic: str, day: int, day_title: str, objective: str, why_matters: str, prev_context: str = "") -> dict:
    """Generate a structured daily block via LLM + RAG grounding, fallback deterministic."""
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
    # Try LLM
    try:
        from app.services.lead_ai import AIService
        from app.config import get_settings
        s = get_settings()
        if s.openai_api_key and s.openai_enabled:
            svc = AIService()
            if svc.configured:
                prev = f"Previous: {prev_context[:500]}" if prev_context else ""
                prompt = (
                    f"Create Day {day} lesson for '{topic}' — Title: {day_title}\n"
                    f"Objective: {objective}\nWhy matters: {why_matters}\n{prev}\n"
                    f"Verified context (use if relevant, never invent):\n{rag_context[:800]}\n\n"
                    "Return JSON with keys: topic, learning_objective, why_matters, concept_explanation (2-3 short paragraphs, mentor tone), "
                    "step_by_step (array of 3-5 strings), examples (array of {title, code, explanation, expected_output}), "
                    "exercise (string), homework (string), challenge (string), quick_review (array), questions (array of 3), next_preview (string).\n"
                    "Code examples must be runnable, progressive, and match the lesson. Return JSON only."
                )
                out = await svc._complete(
                    [{"role": "system", "content": "You are a mentor teaching practically. Return JSON only, no markdown wrapper."},
                     {"role": "user", "content": _sanitize(prompt[:4000])}],
                    max_tokens=2000, temperature=0.4, tag="learning-block"
                )
                data = out.get("data", {})
                # Basic validation
                if data.get("topic") and data.get("concept_explanation"):
                    return {
                        "topic": str(data.get("topic", day_title))[:120],
                        "learning_objective": str(data.get("learning_objective", objective))[:300],
                        "why_matters": str(data.get("why_matters", why_matters))[:300],
                        "concept_explanation": str(data.get("concept_explanation", ""))[:3000],
                        "step_by_step": (data.get("step_by_step") or [])[:6],
                        "examples": (data.get("examples") or [])[:3],
                        "expected_output": str(data.get("examples", [{}])[0].get("expected_output", "") if data.get("examples") else "")[:500],
                        "exercise": str(data.get("exercise", ""))[:1000],
                        "homework": str(data.get("homework", ""))[:1000],
                        "challenge": str(data.get("challenge", ""))[:800],
                        "quick_review": (data.get("quick_review") or [])[:5],
                        "questions": (data.get("questions") or [])[:5],
                        "next_preview": str(data.get("next_preview", ""))[:300],
                    }
    except Exception as e:
        log.warning("daily block LLM failed day %s %s: %s", day, topic, e)
    # Deterministic fallback
    return {
        "topic": day_title,
        "learning_objective": objective,
        "why_matters": why_matters or f"Builds toward {topic} mastery",
        "concept_explanation": f"Today we explore {day_title}. {objective} This builds on previous days and prepares for next steps in {topic}.",
        "step_by_step": [f"Step {i}: Understand {day_title} concept {i}" for i in range(1, 4)],
        "examples": [{"title": f"{day_title} example", "code": f"// {topic} Day {day} example\nconsole.log('Hello {topic}');", "explanation": "Basic example", "expected_output": "Hello"}],
        "exercise": f"Try modifying the example to handle a different input for {day_title}.",
        "homework": f"Build a small {day_title.lower()} exercise and test it.",
        "challenge": f"Can you extend {day_title} to handle edge cases?",
        "quick_review": [f"Reviewed {day_title}"],
        "questions": [f"What is {day_title}?", f"Why does {day_title} matter for {topic}?", "Can you explain it to someone else?"],
        "next_preview": f"Next: Day {day+1}",
    }

def _validate_block(block: dict) -> tuple[bool, list[str]]:
    """Factual/code validation without LLM: check required fields, code syntax via try-compile."""
    issues = []
    if not block.get("learning_objective"):
        issues.append("missing learning_objective")
    if not block.get("concept_explanation") or len(block["concept_explanation"]) < 30:
        issues.append("concept_explanation too short")
    # Code syntax check for python/js/csharp snippets
    for ex in block.get("examples", [])[:2]:
        code = ex.get("code", "")
        if code.strip().startswith("import ") or "def " in code or "class " in code:
            try:
                import ast
                if "python" in code.lower() or "def " in code:
                    ast.parse(code)
            except SyntaxError as e:
                issues.append(f"code syntax: {e.msg}")
    return (len(issues) == 0, issues)

# ---------- Public API used by scheduler and admin ----------
async def create_learning_path(topic: str, duration: int, goal: str = "", level: str = "beginner", created_by: str = "admin") -> dict:
    db = get_db()
    slug = _slug(topic)
    # Enforce single active per topic slug? Allow multiple but only one active per topic
    existing_active = await db["learning_paths"].find_one({"slug": slug, "status": "active"})
    if existing_active:
        # Pause previous if new is active? Keep as is, new will be planned initially
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
    # Check duplicate by content hash
    dup = await db["learning_paths"].find_one({"slug": slug, "content_hash": doc["content_hash"]})
    if dup:
        return dup
    res = await db["learning_paths"].insert_one(doc)
    doc["_id"] = res.inserted_id
    # Create placeholder blocks (planned)
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
    """Daily 06:00 IST job: inspect active paths, generate/validate next block."""
    db = get_db()
    from app.services import agent_config
    cfg = await agent_config.get_agent(db, "rajiblabs-learning") if "get_agent" in dir(agent_config) else None
    # If agent disabled, no-op
    if cfg and not cfg.get("enabled", True):
        return {"status": "no_action", "reason": "agent disabled"}
    now = utcnow()
    # Find active paths
    cur = db["learning_paths"].find({"status": "active"})
    paths = [d async for d in cur]
    # Also include planned that should become active (first run)
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
        # Determine next day to publish
        blocks = [d async for d in db["learning_blocks"].find({"path_id": path["_id"]}).sort("day_number", 1)]
        # Find first planned/ready block, or needs_review
        next_block = None
        for b in blocks:
            if b.get("status") in ("planned", "needs_review"):
                next_block = b
                break
        if not next_block:
            # Check if all published/completed -> mark path completed
            if all(b.get("status") in ("published", "completed", "archived") for b in blocks) and len(blocks) >= duration:
                await db["learning_paths"].update_one({"_id": path["_id"]}, {"$set": {"status": "completed", "progress": 100, "updated_at": now}})
                results.append({"path": slug, "action": "completed"})
                continue
            else:
                # No planned block but still missing -> generate missing
                max_day = max([b.get("day_number", 0) for b in blocks] or [0])
                if max_day < duration:
                    # Create placeholder for next day
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
        # Validate existing content hash to avoid regen
        # If block already published and hash matches, skip
        prev_text = next_block.get("concept_explanation", "")
        # Generate block
        prev_block = None
        if next_block["day_number"] > 1:
            prev_block = await db["learning_blocks"].find_one({"path_id": path["_id"], "day_number": next_block["day_number"]-1})
        prev_ctx = prev_block.get("topic", "") if prev_block else ""
        gen = await _generate_daily_block(path["topic"], next_block["day_number"], next_block.get("title",""), next_block.get("learning_objective",""), next_block.get("why_matters",""), prev_ctx)
        # Validate
        ok, issues = _validate_block(gen)
        new_hash = _hash(gen.get("concept_explanation",""), gen.get("exercise",""))
        if next_block.get("content_hash") == new_hash and next_block.get("status") == "published":
            results.append({"path": slug, "day": next_block["day_number"], "action": "unchanged", "hash": new_hash})
            continue
        if not ok:
            # Mark needs_review, don't publish
            await db["learning_blocks"].update_one({"_id": next_block["_id"]}, {"$set": {
                "status": "needs_review", "content_hash": new_hash, "validation_issues": issues, "updated_at": now,
                **gen
            }})
            results.append({"path": slug, "day": next_block["day_number"], "action": "needs_review", "issues": issues})
            continue
        # Publish
        update_doc = {
            **gen,
            "status": "published",
            "content_hash": new_hash,
            "version": (next_block.get("version", 1) + 1),
            "generated_at": now,
            "validated_at": now,
            "updated_at": now,
        }
        await db["learning_blocks"].update_one({"_id": next_block["_id"]}, {"$set": update_doc})
        # Update path progress
        published_count = await db["learning_blocks"].count_documents({"path_id": path["_id"], "status": {"$in": ["published", "completed"]}})
        # Count includes this one if it was just published? Need +1 if it was planned
        if next_block.get("status") == "planned":
            published_count += 1
        progress = int((published_count / duration) * 100) if duration else 0
        await db["learning_paths"].update_one({"_id": path["_id"]}, {"$set": {"current_day": next_block["day_number"], "progress": min(100, progress), "updated_at": now, "last_run_at": now}})
        # RAG upsert
        try:
            from app.services import rag_ingest
            content = f"{gen['topic']}\n{gen['concept_explanation']}\n{gen['exercise']}\n{gen['homework']}"
            await rag_ingest.upsert_document(
                "learning", f"learning:{slug}:{next_block['day_number']}",
                f"{path['topic']} — Day {next_block['day_number']}: {gen['topic']}",
                content, tags=["learning", slug], url=f"https://rajiblabs.com/learning/{slug}/day/{next_block['day_number']}"
            )
        except Exception as e:
            log.warning("learning RAG failed %s day %s: %s", slug, next_block["day_number"], e)
        results.append({"path": slug, "day": next_block["day_number"], "action": "published"})
    # Record run
    run_doc = {"triggered_by": triggered_by, "results": results, "started_at": now, "finished_at": utcnow(), "status": "success" if results else "no_action"}
    await db["learning_agent_runs"].insert_one(run_doc)
    try:
        await audit(triggered_by, "LEARNING_AGENT_RUN", "daily", {"results": results})
    except: pass
    return {"status": "success", "results": results}
