"""Intelligent document chunking for the RAG knowledge base.

Prefers heading-aware, then paragraph-aware, then code-aware splits so chunks
keep semantic context. Never emits tiny fragments (< min_chars merges up).
"""
import re

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_HEADING_RE = re.compile(r"(?m)^(#{1,4}\s+.+)$")
_MD_HEADING_RE = re.compile(r"(?m)^(.+)\n(=+|-+)$")


def _split_fences(text: str) -> list[tuple[str, bool]]:
    """Split into (segment, is_code) parts, keeping fenced blocks whole."""
    parts: list[tuple[str, bool]] = []
    last = 0
    for m in _FENCE_RE.finditer(text):
        if m.start() > last:
            parts.append((text[last:m.start()], False))
        parts.append((m.group(0), True))
        last = m.end()
    if last < len(text):
        parts.append((text[last:], False))
    return [(seg, code) for seg, code in parts if seg.strip()]


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150,
               min_chars: int = 200, topic: str = "") -> list[dict]:
    """Chunk text into coherent pieces. Returns [{content, topic}]."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [{"content": text, "topic": topic}]

    # 1. heading-aware sections (markdown # or underline headings)
    sections: list[str] = []
    marked = _HEADING_RE.sub(r"\n@@H@@\1", text)
    marked = _MD_HEADING_RE.sub(r"\n@@H@@\1", marked)
    for part in marked.split("@@H@@"):
        part = part.strip()
        if part:
            sections.append(part)
    if len(sections) <= 1:
        sections = [text]

    chunks: list[dict] = []
    current = ""
    current_topic = topic
    for sec in sections:
        m = re.match(r"^(#{1,4}\s+|)(.{1,80})", sec)
        sec_topic = (m.group(2).strip("# \n")[:80] if m else topic) or topic
        if len(sec) > max_chars:
            # 2. oversized section → paragraph splits, then code-aware
            for seg, is_code in _split_fences(sec):
                units = [seg] if is_code else _split_paragraphs(seg)
                for u in units:
                    if len(u) > max_chars:
                        # 3. last resort: hard split on sentence/char boundaries
                        for i in range(0, len(u), max_chars - overlap):
                            piece = u[i:i + max_chars].strip()
                            if piece:
                                _emit(chunks, piece, sec_topic or topic, min_chars)
                        current, current_topic = "", topic
                    elif len(current) + len(u) + 2 > max_chars:
                        _emit(chunks, current, current_topic, min_chars)
                        current, current_topic = u, sec_topic or topic
                    else:
                        current = (current + "\n\n" + u).strip() if current else u
                        current_topic = sec_topic or topic
        elif len(current) + len(sec) + 2 > max_chars and current:
            _emit(chunks, current, current_topic, min_chars)
            current, current_topic = sec, sec_topic
        else:
            current = (current + "\n\n" + sec).strip() if current else sec
            current_topic = sec_topic
    _emit(chunks, current, current_topic, min_chars)
    return chunks


def _emit(chunks: list[dict], content: str, topic: str, min_chars: int) -> None:
    content = (content or "").strip()
    if not content:
        return
    if len(content) < min_chars and chunks:
        # merge tiny fragment into previous chunk instead of isolating it
        chunks[-1]["content"] = (chunks[-1]["content"] + "\n\n" + content).strip()
        return
    chunks.append({"content": content, "topic": topic})
