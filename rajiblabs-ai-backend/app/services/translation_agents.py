"""Translation agents — agentic multilingual layer (no duplicate AI/RAG/auth).

TranslationAgent: invoked ONLY on cache miss. Uses the existing AI
orchestrator (lead_ai.AIService); never touches providers directly.
TranslationQualityAgent: rule-based validation, zero LLM cost.
"""
import logging
import re

log = logging.getLogger("rajiblabs")

TRANSLATION_SYSTEM = """You are a precise website translator for RajibLabs.
Translate the source text into the target language. Rules:
- Preserve meaning, tone and formatting (line breaks, lists, emphasis).
- NEVER translate, alter or drop protected tokens like ⟦0⟧ — copy them verbatim.
- NEVER translate URLs, emails, code, placeholders, brand names (RajibLabs, Rajib Mahata),
  technology names (.NET, React, Azure, SQL Server) or person names.
- Do not add explanations, quotes or commentary. Output ONLY the translation.
- Never include secrets or anything outside the given source text.
Return JSON with exactly one key: "text"."""

# Script ranges to detect "answered in the wrong script" (language mismatch).
SCRIPT_RANGES = {
    "bn": [("\\u0980", "\\u09FF")],
    "hi": [("\\u0900", "\\u097F")],
    "ja": [("\\u3040", "\\u309F"), ("\\u30A0", "\\u30FF"), ("\\u4E00", "\\u9FAF")],
    "zh-CN": [("\\u4E00", "\\u9FFF")],
    "ko": [("\\uAC00", "\\uD7AF"), ("\\u1100", "\\u11FF")],
    "ar": [("\\u0600", "\\u06FF")],
}

_PROTECT_PATTERNS = (
    ("url", re.compile(r"https?://[^\s)>\]]+")),
    ("email", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("code", re.compile(r"`[^`]+`")),
    ("placeholder", re.compile(r"\{[a-zA-Z0-9_.]+\}|\{\{[^}]+\}\}")),
    ("html", re.compile(r"</?[a-zA-Z][^>]*>")),
)


def protect_segments(text: str) -> tuple[str, list[str]]:
    """Replace no-translate spans with ⟦N⟧ tokens. Returns (masked, originals)."""
    originals: list[str] = []

    def _swap(m: re.Match) -> str:
        originals.append(m.group(0))
        return f"⟦{len(originals) - 1}⟧"

    masked = text or ""
    for _, pat in _PROTECT_PATTERNS:
        masked = pat.sub(_swap, masked)
    return masked, originals


def restore_segments(text: str, originals: list[str]) -> str:
    def _back(m: re.Match) -> str:
        try:
            return originals[int(m.group(1))]
        except (IndexError, ValueError):
            return m.group(0)
    return re.sub(r"⟦(\d+)⟧", _back, text or "")


def extract_urls(text: str) -> set[str]:
    return set(re.findall(r"https?://[^\s)>\]]+", text or ""))


def extract_placeholders(text: str) -> set[str]:
    return set(re.findall(r"\{[a-zA-Z0-9_.]+\}|\{\{[^}]+\}\}|⟦\d+⟧", text or ""))


class TranslationAgent:
    """LLM translation via the existing orchestrator. Count every call."""

    calls = 0

    # Conservative refusal: never send secrets/credentials to the LLM.
    _SECRET_RE = re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
        r"\b(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16}|xox[bpas]-[A-Za-z0-9-]+)\b|"
        r"(password|passwd|secret|api[_-]?key)\s*[:=]\s*\S{4,}",
        re.IGNORECASE)

    @classmethod
    async def translate(cls, text: str, target: str, target_name: str,
                        source: str = "en", context: str = "",
                        max_tokens: int = 1200) -> tuple[str, dict]:
        """Returns (translated_text, meta{provider, model}). Raises AIError."""
        if cls._SECRET_RE.search(text or ""):
            raise ValueError("Refusing to translate text that looks like a secret/credential")
        from app.services import lead_ai
        svc = lead_ai.AIService()
        if not svc.configured:
            raise lead_ai.AIError("AI not configured")
        masked, originals = protect_segments(text)
        user = (f"Source language: {source}\nTarget language: {target_name} ({target})\n"
                + (f"Context: {context[:400]}\n" if context else "")
                + f"Text to translate:\n{masked[:4000]}")
        out = await svc._complete(
            [{"role": "system", "content": TRANSLATION_SYSTEM},
             {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=0.2, tag=f"translate-{target}")
        data = out.get("data") or {}
        result = restore_segments(str(data.get("text", "")).strip(), originals)
        if not result:
            raise lead_ai.AIError("Empty translation")
        cls.calls += 1
        return result, {"provider": out.get("provider", ""), "model": out.get("model", "")}


class TranslationQualityAgent:
    """Zero-cost validation of a translation. Returns {passed, issues[]}."""

    @staticmethod
    def check(source: str, translated: str, target: str) -> dict:
        issues: list[str] = []
        src, out = source or "", translated or ""
        if not out.strip():
            return {"passed": False, "issues": ["missing_content"]}
        if set(extract_urls(out)) != set(extract_urls(src)):
            issues.append("broken_urls")
        if extract_placeholders(src) - extract_placeholders(out):
            issues.append("incorrect_placeholders")
        if "⟦" in out or "⟧" in out:
            issues.append("incorrect_formatting")
        # Language mismatch: expected script absent from a non-trivial output.
        ranges = SCRIPT_RANGES.get(target)
        if ranges and len(re.sub(r"\s|⟦\d+⟧|https?://\S+", "", out)) >= 20:
            body = re.sub(r"https?://\S+|`[^`]+`", "", out)
            if not any(re.search(f"[{a}-{b}]", body) for a, b in ranges):
                issues.append("language_mismatch")
        # Suspicious echo: translation identical to source for real prose.
        if len(src) > 40 and src.strip() == out.strip():
            issues.append("untranslated_text")
        # Runaway length (likely hallucinated padding).
        if len(src) > 0 and not (0.3 <= len(out) / max(1, len(src)) <= 4.0):
            issues.append("incorrect_formatting")
        issues = sorted(set(issues))
        return {"passed": not issues, "issues": issues}
