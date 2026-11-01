"""Accept a draft only when it quotes one allowed page and the numbers in that chunk."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.ingest.sources import host_allowed

URL_RE = re.compile(r"https?://[^\s)>\]]+")
DATE_RE = re.compile(r"^Last updated from sources: (\d{4}-\d{2}-\d{2})\.?$")
NUMBER_RE = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?%?")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Check:
    passed: bool
    failures: tuple[str, ...]
    text: str


def _urls(text: str) -> list[str]:
    return [url.rstrip(".,") for url in URL_RE.findall(text)]


def _body(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("Source:") and not line.startswith("Last updated from sources:")]
    return "\n".join(lines)


def check_draft(
    draft: str,
    *,
    action: str,
    allowed_urls: set[str],
    passages: dict[str, str],
    fetched_at: str,
    settings,
) -> Check:
    failures: list[str] = []
    urls = _urls(draft)
    if len(urls) != 1:
        failures.append("link_count")
    url = urls[0] if len(urls) == 1 else ""
    allowed = {item.rstrip("/") for item in allowed_urls}
    if url and (not host_allowed(url, settings) or "/blog" in url or url.rstrip("/") not in allowed):
        failures.append("link_not_allowed")
    cited_text = passages.get(url, passages.get(url.rstrip("/"), ""))

    lines = [line.strip() for line in draft.splitlines() if line.strip()]
    date_line = lines[-1] if lines else ""
    match = DATE_RE.match(date_line)
    if not match:
        failures.append("date_line")
    elif match.group(1) != fetched_at:
        failures.append("date_truth")

    sentences = [part for part in SENTENCE_RE.split(_body(draft).strip()) if part.strip()]
    if len(sentences) > 3:
        failures.append("too_long")

    numbers = NUMBER_RE.findall(_body(draft))
    for number in numbers:
        token = number.replace(",", "")
        plain = token[:-1] if token.endswith("%") else token
        if plain not in cited_text and token not in cited_text:
            failures.append("ungrounded_number")
            break

    if action == "answer_with_refusal":
        if "facts only." not in draft.lower():
            failures.append("missing_facts_only")
        if any(re.search(rf"\b{word}\b", draft, re.IGNORECASE) for word in ("buy", "sell", "hold")):
            failures.append("recommendation_word")

    if failures == ["date_truth"] and match:
        fixed = "\n".join(lines[:-1] + [f"Last updated from sources: {fetched_at}."])
        return Check(True, ("date_corrected",), fixed)
    return Check(not failures, tuple(failures), draft)
