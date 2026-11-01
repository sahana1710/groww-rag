"""Read and validate sources.csv. The scraper fetches nothing else."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.config import Settings

PAGE_TYPES = frozenset({"amc", "scheme", "help", "factsheet", "regulator"})
MIN_SOURCES = 5
MAX_SOURCES = 6


@dataclass(frozen=True)
class Source:
    source_id: str
    url: str
    publisher: str
    page_type: str
    scheme_name: str
    why_included: str


def sources_path(root: Path) -> Path:
    return root / "sources" / "sources.csv"


def _host_and_path(url: str) -> tuple[str, str]:
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path or "/"
    return host, path


def host_allowed(url: str, settings: Settings) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    host, path = _host_and_path(url)
    if not host:
        return False
    for prefix in settings.blocked_path_prefixes:
        blocked_host, _, blocked_rest = prefix.lower().partition("/")
        if blocked_host.startswith("www."):
            blocked_host = blocked_host[4:]
        blocked_path = "/" + blocked_rest if blocked_rest else "/"
        host_matches = host == blocked_host or host.endswith("." + blocked_host)
        path_matches = path == blocked_path or path.startswith(blocked_path.rstrip("/") + "/")
        if host_matches and path_matches:
            return False
    for domain in settings.citation_domains:
        allowed = domain.lower()
        if allowed.startswith("www."):
            allowed = allowed[4:]
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def load_sources(root: Path, settings: Settings) -> list[Source]:
    path = sources_path(root)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or rows[0].keys() < {
        "id",
        "url",
        "publisher",
        "page_type",
        "scheme_name",
        "why_included",
    }:
        raise SystemExit(f"{path} is missing required columns")

    count = len(rows)
    if count < MIN_SOURCES or count > MAX_SOURCES:
        raise SystemExit(f"sources.csv has {count} rows; expected {MIN_SOURCES}–{MAX_SOURCES}")

    sources: list[Source] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for row in rows:
        source = Source(
            source_id=(row.get("id") or "").strip(),
            url=(row.get("url") or "").strip(),
            publisher=(row.get("publisher") or "").strip(),
            page_type=(row.get("page_type") or "").strip(),
            scheme_name=(row.get("scheme_name") or "").strip(),
            why_included=(row.get("why_included") or "").strip(),
        )
        if not source.source_id or not source.url:
            raise SystemExit("every source row needs an id and a url")
        if source.source_id in seen_ids:
            raise SystemExit(f"duplicate source id: {source.source_id}")
        if source.url in seen_urls:
            raise SystemExit(f"duplicate source url: {source.url}")
        if source.page_type not in PAGE_TYPES:
            raise SystemExit(f"{source.source_id} has page_type {source.page_type!r}")
        if not host_allowed(source.url, settings):
            raise SystemExit(f"{source.source_id} is not an allowed URL: {source.url}")
        seen_ids.add(source.source_id)
        seen_urls.add(source.url)
        sources.append(source)
    return sources
