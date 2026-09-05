"""TranslationService + TranslationCache — cost-first multilingual content.

Priority chain (never wait for an LLM on the public path):
  approved record → content cache → valid generated record → English source
  (+ background LLM fill) → explicit LLM only when asked (admin / POST /translate).

Source of truth stays English in the existing collections; translations live in
`translations` (managed records) + `translation_cache` (hash-addressed reuse).
"""
import asyncio
import hashlib
import logging
import re

from app.database import get_db, utcnow
from app.services import lang_service
from app.services.translation_agents import (
    TranslationAgent, TranslationQualityAgent,
)

log = logging.getLogger("rajiblabs")

# collection → reference field + translatable fields (dict/list fields are
# flattened to string leaves; technical leaves are skipped, never translated).
TRANSLATABLE: dict[str, dict] = {
    "homepage_content": {"ref": "section_key", "fields": ["title", "subtitle", "body"],
                         "filter": {"status": "published"}},
    "projects": {"ref": "slug", "fields": ["name", "short_description", "full_description",
                                           "problem", "solution"],
                 "filter": {"published": True}},
    "products": {"ref": "slug", "fields": ["name", "description", "features"],
                 "filter": {"status": "published"}},
    "profiles": {"ref": None, "fields": ["title", "bio"], "filter": {}},
    "experience": {"ref": None, "fields": ["description"], "filter": {"status": "published"}},
}

SKIP_LEAF_KEYS = frozenset({
    "slug", "url", "link", "links", "href", "src", "image", "icon", "logo",
    "email", "phone", "whatsapp", "key", "code", "id", "token", "github",
    "repo", "repository", "video", "file", "path", "date", "dates", "period",
    "created_at", "updated_at", "status", "category", "contenttype",
})
_URL_RE = re.compile(r"^https?://\S+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def source_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def _leaf_ok(segment: str, value: str) -> bool:
    if not isinstance(value, str) or len(value.strip()) < 2:
        return False
    if segment.lower() in SKIP_LEAF_KEYS:
        return False
    v = value.strip()
    if _URL_RE.match(v) or _EMAIL_RE.match(v) or v.replace(" ", "").replace(".", "").isdigit():
        return False
    return True


def flatten_strings(node, prefix: str = "") -> list[tuple[str, str]]:
    """String leaves of nested dicts/lists → [(dotted.path, text)]."""
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.extend(flatten_strings(v, f"{prefix}{k}." if prefix else f"{k}."))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(flatten_strings(v, f"{prefix}{i}."))
    elif _leaf_ok(prefix.rstrip(".").rsplit(".", 1)[-1] if prefix else "", node):
        out.append((prefix.rstrip("."), node))
    return out


def _set_path(node, parts: list[str], value: str) -> None:
    cur = node
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    last = parts[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


class TranslationCache:
    """Hash-addressed reuse across keys. Permanent until source changes."""

    @staticmethod
    async def get(db, h: str, target: str) -> dict | None:
        return await db["translation_cache"].find_one(
            {"source_hash": h, "target_language": target})

    @staticmethod
    async def put(db, h: str, target: str, source: str, text: str, meta: dict) -> None:
        now = utcnow()
        await db["translation_cache"].update_one(
            {"source_hash": h, "target_language": target},
            {"$set": {"translated_text": text, "source_text": source,
                      "provider": meta.get("provider", ""), "model": meta.get("model", ""),
                      "updated_at": now},
             "$setOnInsert": {"created_at": now}}, upsert=True)


class TranslationService:
    @staticmethod
    async def get_text(key: str, source_text: str, target: str,
                       context: str = "", source_lang: str = "en",
                       generate: bool = False, db=None) -> tuple[str, str]:
        """(text, status). Never raises, never bills unless generate=True."""
        target = await lang_service.resolve(target if target != source_lang else source_lang, db)
        if target == source_lang:
            return source_text, "source"
        db = db if db is not None else get_db()
        h = source_hash(source_text)
        try:
            rec = await db["translations"].find_one(
                {"key": key, "target_language": target})
            if rec and rec.get("source_hash") == h \
                    and rec.get("status") in ("approved", "generated"):
                return rec["translated_text"], rec["status"]
            stale = bool(rec)
            hit = await TranslationCache.get(db, h, target)
            if hit:
                # Promote hot cache into a managed record for admin visibility.
                now = utcnow()
                await db["translations"].update_one(
                    {"key": key, "target_language": target},
                    {"$set": {"source_text": source_text, "translated_text": hit["translated_text"],
                              "source_hash": h, "status": "generated",
                              "provider": hit.get("provider", ""), "model": hit.get("model", ""),
                              "updated_at": now,
                              "version": int((rec or {}).get("version", 0)) + 1},
                     "$setOnInsert": {"source_language": source_lang, "created_at": now}},
                    upsert=True)
                return hit["translated_text"], "cached"
            if stale and rec.get("status") == "approved":
                # Source changed: keep serving approved text, flag + refill async.
                await db["translations"].update_one(
                    {"_id": rec["_id"]}, {"$set": {"status": "needs_update"}})
                TranslationService.fill_background(
                    key, source_text, target, context, source_lang)
                return rec["translated_text"], "stale"
            if not generate:
                return source_text, "missing"
            # Explicit path only: bill the orchestrator once, then cache forever.
            translated, meta = await TranslationAgent.translate(
                source_text, target,
                await lang_service.language_name(target, db),
                source=source_lang, context=context)
            quality = TranslationQualityAgent.check(source_text, translated, target)
            status = "generated" if quality["passed"] else "needs_review"
            now = utcnow()
            await db["translations"].update_one(
                {"key": key, "target_language": target},
                {"$set": {"source_text": source_text, "translated_text": translated,
                          "source_language": source_lang, "source_hash": h,
                          "status": status, "quality": quality,
                          "provider": meta.get("provider", ""), "model": meta.get("model", ""),
                          "generated_at": now, "updated_at": now,
                          "version": int((rec or {}).get("version", 0)) + 1},
                 "$setOnInsert": {"created_at": now}}, upsert=True)
            await TranslationCache.put(db, h, target, source_text, translated, meta)
            try:
                from app.services.notify import audit
                await audit("translation", "TRANSLATION_GENERATED", key,
                            {"target": target, "status": status,
                             "model": meta.get("model", "")})
            except Exception:
                pass
            return translated, status
        except Exception as e:
            log.warning("translation fallback to source for %s: %s", key, e)
            return source_text, "missing"

    @staticmethod
    def fill_background(key: str, source_text: str, target: str,
                        context: str = "", source_lang: str = "en") -> None:
        """Fire-and-forget LLM fill so the NEXT visitor hits cache (§perf)."""
        async def _run():
            try:
                await TranslationService.get_text(
                    key, source_text, target, context, source_lang, generate=True)
            except Exception as e:
                log.warning("background translation failed for %s: %s", key, e)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_run())
        except RuntimeError:
            pass  # no loop (tests/CLI): caller decides

    @staticmethod
    async def localize_doc(collection: str, doc: dict, target: str,
                           db=None) -> tuple[dict, dict]:
        """Overlay translations onto a public doc copy. Returns (doc, stats)."""
        from copy import deepcopy
        spec = TRANSLATABLE.get(collection)
        default = await lang_service.default_code(db)
        target = await lang_service.resolve(target, db)
        if not spec or target == default:
            return doc, {"replaced": 0, "pending": 0}
        ref_field = spec["ref"]
        ref = str(doc.get(ref_field)) if ref_field else collection.rstrip("s")
        if not ref or ref == "None":
            ref = str(doc.get("_id", "doc"))
        out = deepcopy(doc)
        stats = {"replaced": 0, "pending": 0}
        for field in spec["fields"]:
            if field not in doc or doc[field] is None:
                continue
            value = doc[field]
            if isinstance(value, str):
                if not _leaf_ok(field, value):
                    continue
                key = f"{collection}.{ref}.{field}"
                text, status = await TranslationService.get_text(
                    key, value, target, context=f"{collection} {field}", db=db)
                if status in ("approved", "generated", "cached", "stale"):
                    out[field] = text
                    stats["replaced"] += 1
                else:
                    stats["pending"] += 1
                    TranslationService.fill_background(
                        key, value, target, context=f"{collection} {field}")
            else:
                for path, leaf in flatten_strings(value):
                    key = f"{collection}.{ref}.{field}.{path}"
                    text, status = await TranslationService.get_text(
                        key, leaf, target, context=f"{collection} {field}", db=db)
                    if status in ("approved", "generated", "cached", "stale"):
                        _set_path(out[field], path.split("."), text)
                        stats["replaced"] += 1
                    else:
                        stats["pending"] += 1
                        TranslationService.fill_background(
                            key, leaf, target, context=f"{collection} {field}")
        out["_lang"] = target
        return out, stats

    @staticmethod
    async def localize_many(collection: str, docs: list[dict],
                            lang: str | None, db=None) -> list[dict]:
        """Overlay translations on list responses. English/no-lang = passthrough."""
        if not lang:
            return docs
        out = []
        for d in docs:
            loc, _ = await TranslationService.localize_doc(collection, d, lang, db)
            out.append(loc)
        return out

    @staticmethod
    async def universe(db=None) -> list[dict]:
        """Every translatable leaf: [{key, collection, ref, field, source_text}]."""
        from app.models import oid_str
        db = db if db is not None else get_db()
        items: list[dict] = []
        for collection, spec in TRANSLATABLE.items():
            try:
                cur = db[collection].find(spec.get("filter", {}))
                async for raw in cur:
                    d = oid_str(raw)
                    ref = str(d.get(spec["ref"])) if spec["ref"] else collection.rstrip("s")
                    for field in spec["fields"]:
                        if field not in d or d[field] is None:
                            continue
                        v = d[field]
                        if isinstance(v, str):
                            if _leaf_ok(field, v):
                                items.append({"key": f"{collection}.{ref}.{field}",
                                              "collection": collection, "ref": ref,
                                              "field": field, "source_text": v})
                        else:
                            for path, leaf in flatten_strings(v):
                                items.append({"key": f"{collection}.{ref}.{field}.{path}",
                                              "collection": collection, "ref": ref,
                                              "field": f"{field}.{path}", "source_text": leaf})
            except Exception as e:
                log.warning("universe scan skipped %s: %s", collection, e)
        return items

    @staticmethod
    async def coverage(target: str, db=None) -> dict:
        """Per-language status counts + missing/stale key lists (admin)."""
        db = db if db is not None else get_db()
        uni = await TranslationService.universe(db)
        recs = {}
        async for r in db["translations"].find({"target_language": target}):
            recs[r["key"]] = r
        by_status: dict[str, int] = {}
        missing: list[str] = []
        stale: list[str] = []
        for item in uni:
            r = recs.get(item["key"])
            if not r:
                missing.append(item["key"])
                continue
            if r.get("source_hash") != source_hash(item["source_text"]):
                stale.append(item["key"])
                by_status["needs_update"] = by_status.get("needs_update", 0) + 1
            else:
                st = r.get("status", "generated")
                by_status[st] = by_status.get(st, 0) + 1
        return {"target": target, "total_keys": len(uni), "by_status": by_status,
                "missing": sorted(missing)[:500], "missing_count": len(missing),
                "stale": sorted(stale)[:200], "stale_count": len(stale)}
