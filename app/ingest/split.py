"""Split long prose on headings, steps, then sentences. Fact slabs are not split here."""

from __future__ import annotations

import re

STEP_RE = re.compile(r"^(?:step\s+)?\d+[.)]\s+\S", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _paragraphs(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line.strip())
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def _is_heading(paragraph: str) -> bool:
    if "\n" in paragraph or len(paragraph) > 80:
        return False
    return not paragraph.endswith((".", "!", "?"))


def _word_tail(text: str, overlap: int) -> str:
    if overlap <= 0 or len(text) <= overlap:
        return text.strip()
    start = len(text) - overlap
    if start > 0 and text[start - 1] != " ":
        space = text.rfind(" ", 0, start)
        if space != -1:
            start = space + 1
    return text[start:].strip()


def _pack(parts: list[str], max_chars: int, overlap: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for part in parts:
        if not current:
            current = part
            continue
        joined = f"{current}\n\n{part}"
        if len(joined) <= max_chars:
            current = joined
            continue
        pieces.append(current)
        prefix = _word_tail(current, overlap)
        current = f"{prefix}\n\n{part}" if prefix else part
    if current:
        pieces.append(current)
    return pieces


def _split_long(section: str, max_chars: int, overlap: int) -> list[str]:
    paragraphs = [part for part in section.split("\n\n") if part.strip()]
    if len(paragraphs) > 1 and all(len(part) <= max_chars for part in paragraphs):
        return _pack(paragraphs, max_chars, overlap)
    sentences = [part.strip() for part in SENTENCE_RE.split(section) if part.strip()]
    if not sentences:
        return [section]
    return _pack(sentences, max_chars, overlap)


def split_sections(text: str, max_chars: int, overlap: int) -> list[str]:
    sections: list[str] = []
    bucket: list[str] = []

    def flush() -> None:
        if bucket:
            sections.append("\n\n".join(bucket).strip())
            bucket.clear()

    for paragraph in _paragraphs(text):
        if STEP_RE.match(paragraph):
            flush()
            sections.append(paragraph)
            continue
        if _is_heading(paragraph) and bucket:
            flush()
        bucket.append(paragraph)
    flush()

    pieces: list[str] = []
    for section in sections:
        if len(section) <= max_chars or STEP_RE.match(section):
            pieces.append(section)
        else:
            pieces.extend(_split_long(section, max_chars, overlap))
    return [piece for piece in pieces if piece.strip()]
