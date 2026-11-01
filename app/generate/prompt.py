"""Assemble the system prompt and the passage block sent to the provider."""

from __future__ import annotations

from pathlib import Path

from app.retrieve.search import Hit
from app.store.layout import repo_root


def system_prompt(root: Path | None = None) -> str:
    path = (root or repo_root()) / "prompts" / "system.md"
    return path.read_text(encoding="utf-8").strip()


def user_message(question: str, action: str, hits: list[Hit], filter_relaxed: bool) -> str:
    lines = [
        f"Question: {question}",
        f"Action: {action}",
        f"Filter relaxed: {str(filter_relaxed).lower()}",
        "",
        "Passages:",
    ]
    for index, hit in enumerate(hits, start=1):
        lines.append(
            f"[{index}] url={hit.source_url} scheme={hit.scheme_name} fact_type={hit.fact_type} fetched_at={hit.fetched_at}"
        )
        lines.append(hit.text)
    if filter_relaxed:
        lines.append("The filter was relaxed. Name the page the passage actually came from.")
    return "\n".join(lines)
