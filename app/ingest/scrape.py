"""Fetch the source list and write one raw folder per URL."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from app.config import load_settings
from app.ingest.html_clean import extract
from app.ingest.sources import Source, host_allowed, load_sources
from app.store.layout import data_dir, raw_dir, read_pipeline, write_pipeline

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
IST = ZoneInfo("Asia/Kolkata")
DOWNSTREAM = ("load", "chunk", "embed", "index")
DROP_DIRS = ("raw", "documents", "chunks", "embeddings", "chroma")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reset(root: Path) -> None:
    base = data_dir(root)
    for name in DROP_DIRS:
        path = base / name
        if path.exists():
            shutil.rmtree(path)
    pipeline = read_pipeline(root)
    pipeline["stages"]["scrape"] = {"status": "running"}
    for stage in DOWNSTREAM:
        pipeline["stages"][stage] = {"status": "stale"}
    write_pipeline(pipeline, root)


def _write_meta(folder: Path, meta: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def _failed(source: Source, *, http_status: int | None, error: str, final_url: str, when: datetime) -> dict:
    return {
        "source_id": source.source_id,
        "url": source.url,
        "final_url": final_url,
        "title": "",
        "page_type": source.page_type,
        "scheme_name": source.scheme_name,
        "fetched_at": when.date().isoformat(),
        "fetched_at_iso": when.isoformat(timespec="seconds"),
        "http_status": http_status,
        "content_hash": "",
        "status": "failed",
        "error": error,
    }


def _save_success(folder: Path, source: Source, response: httpx.Response, when: datetime) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    content_type = response.headers.get("content-type", "")
    is_pdf = "pdf" in content_type.lower() or str(response.url).lower().endswith(".pdf")
    if is_pdf:
        title = source.scheme_name or source.source_id
        text = f"PDF document from {response.url}\n"
        (folder / "page.html").write_bytes(response.content)
        scheme = None
    else:
        title, text, scheme = extract(response.text)
        if not title:
            title = source.scheme_name or source.source_id
        (folder / "page.html").write_text(response.text, encoding="utf-8")
    text_bytes = text.encode("utf-8")
    (folder / "text.txt").write_bytes(text_bytes)
    if scheme is not None:
        (folder / "next.json").write_text(
            json.dumps(scheme, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return {
        "source_id": source.source_id,
        "url": source.url,
        "final_url": str(response.url),
        "title": title,
        "page_type": source.page_type,
        "scheme_name": source.scheme_name,
        "fetched_at": when.date().isoformat(),
        "fetched_at_iso": when.isoformat(timespec="seconds"),
        "http_status": response.status_code,
        "content_hash": _sha256(text_bytes),
        "status": "ok",
    }


def scrape_one(client: httpx.Client, source: Source, root: Path, settings) -> dict:
    folder = raw_dir(source.source_id, root)
    when = datetime.now(IST)
    try:
        response = client.get(source.url)
    except httpx.HTTPError as exc:
        meta = _failed(source, http_status=None, error=type(exc).__name__, final_url=source.url, when=when)
        _write_meta(folder, meta)
        return meta
    finally:
        client.cookies.clear()

    final_url = str(response.url)
    if response.status_code >= 400:
        meta = _failed(
            source,
            http_status=response.status_code,
            error=f"http_{response.status_code}",
            final_url=final_url,
            when=when,
        )
        _write_meta(folder, meta)
        return meta
    if not host_allowed(final_url, settings):
        meta = _failed(
            source,
            http_status=response.status_code,
            error="redirect_left_allowlist",
            final_url=final_url,
            when=when,
        )
        _write_meta(folder, meta)
        return meta
    meta = _save_success(folder, source, response, when)
    _write_meta(folder, meta)
    return meta


def run(root: Path | None = None, client: httpx.Client | None = None) -> int:
    from app.store.layout import repo_root

    root = root or repo_root()
    settings = load_settings(root)
    sources = load_sources(root, settings)
    _reset(root)
    owns_client = client is None
    if client is None:
        client = httpx.Client(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            trust_env=False,
            transport=httpx.HTTPTransport(local_address="0.0.0.0"),
        )
    sidecars: list[dict] = []
    try:
        for source in sources:
            meta = scrape_one(client, source, root, settings)
            sidecars.append(meta)
            print(f"{meta['source_id']}: {meta['status']}")
    finally:
        if owns_client:
            client.close()

    csv_bytes = (root / "sources" / "sources.csv").read_bytes()
    canonical = json.dumps(sorted(sidecars, key=lambda item: item["source_id"]), sort_keys=True)
    finished = datetime.now(IST).isoformat(timespec="seconds")
    pipeline = read_pipeline(root)
    pipeline["stages"]["scrape"] = {
        "status": "ok",
        "finished_at": finished,
        "input_hash": _sha256(csv_bytes),
        "output_hash": _sha256(canonical.encode("utf-8")),
    }
    write_pipeline(pipeline, root)
    failed = [item["source_id"] for item in sidecars if item["status"] != "ok"]
    print(f"scraped {len(sidecars) - len(failed)} ok, {len(failed)} failed")
    return 0
