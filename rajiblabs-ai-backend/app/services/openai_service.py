"""Low-cost OpenAI content engine (compact prompts, hash dedup, graceful degradation)."""
import hashlib
import json
import logging
from app.config import get_settings
from app.schemas import AIContentOut

log = logging.getLogger("rajiblabs")

SYSTEM = ("You are RajibLabs content assistant. Rewrite only from provided evidence. "
          "Never invent customers, revenue, metrics, certifications, performance claims. "
          "If evidence is missing, leave the field empty. Return JSON only.")


def source_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]


async def generate_project_content(name: str, readme: str, meta: dict, existing: dict) -> tuple[AIContentOut, str]:
    s = get_settings()
    h = source_hash(name, readme[:2000], json.dumps(meta, sort_keys=True)[:1000])
    if not s.is_openai_configured():
        # Deterministic fallback: no fabrication, evidence-only summary
        desc = (meta.get("description") or readme[:300] or f"{name} — repository by rajibmahata").strip()
        return AIContentOut(title=name, short_description=desc[:160], description=desc,
                            technology_summary=meta.get("language", ""),
                            seo_title=f"{name} | RajibLabs", seo_description=desc[:160]), h
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=s.openai_api_key)
        prompt = (f"Project: {name}\nDescription: {meta.get('description','')}\n"
                  f"Language: {meta.get('language','')}\nREADME (truncated):\n{readme[:2000]}")
        resp = await client.chat.completions.create(
            model=s.openai_model, max_tokens=700, temperature=0.2,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"})
        data = json.loads(resp.choices[0].message.content or "{}")
        return AIContentOut(**{k: data.get(k, "") if not isinstance(data.get(k), list) else data.get(k, [])
                               for k in AIContentOut.model_fields}), h
    except Exception as e:
        log.warning("OpenAI failed, fallback used: %s", e)
        try:
            from app.services.notify import log_error
            await log_error("openai_content", f"OpenAI enrichment failed for {name}, fallback used",
                            str(e)[:2000], level="warning")
        except Exception:
            pass
        desc = (meta.get("description") or f"{name} — repository by rajibmahata").strip()
        return AIContentOut(title=name, short_description=desc[:160], description=desc,
                            seo_title=f"{name} | RajibLabs", seo_description=desc[:160]), h
