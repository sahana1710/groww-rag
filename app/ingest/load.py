"""Turn scraped raw folders into one document per successful source."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.ingest.html_clean import help_article
from app.store.layout import data_dir, documents_path, read_pipeline, write_pipeline

IST = ZoneInfo("Asia/Kolkata")
SCALAR_FIELDS = (
    "expense_ratio",
    "exit_load",
    "min_sip_investment",
    "min_investment_amount",
    "benchmark_name",
    "description",
    "category",
    "sub_category",
    "sid_url",
    "plan_type",
    "scheme_type",
    "scheme_name",
    "aum",
    "nav",
    "nav_date",
    "launch_date",
    "base_expense_ratio",
    "stamp_duty",
    "portfolio_turnover",
    "min_withdrawal",
    "mini_additional_investment",
    "isin",
    "fund_house",
)
RETURN_LABELS = (
    ("return1d", "1 day"),
    ("return1w", "1 week"),
    ("return1m", "1 month"),
    ("return3m", "3 month"),
    ("return6m", "6 month"),
    ("return1y", "1 year"),
    ("return3y", "3 year"),
    ("return5y", "5 year"),
    ("return10y", "10 year"),
    ("return_since_created", "since launch"),
)
DOWNSTREAM_DIRS = ("chunks", "embeddings", "chroma")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _managers(scheme: dict) -> list[dict]:
    people = []
    for person in scheme.get("fund_manager_details") or []:
        if not isinstance(person, dict) or not _present(person.get("person_name")):
            continue
        people.append(
            {
                "name": person["person_name"],
                "since": str(person.get("date_from") or "")[:10],
                "education": person.get("education") or "",
                "experience": person.get("experience") or "",
            }
        )
    return people


def _holdings(scheme: dict) -> list[dict]:
    rows = []
    for item in scheme.get("holdings") or []:
        if not isinstance(item, dict) or not _present(item.get("company_name")):
            continue
        rows.append(
            {
                "company": item["company_name"],
                "sector": item.get("sector_name") or "",
                "weight": item.get("corpus_per"),
            }
        )
    return rows


def _published_returns(scheme: dict) -> dict:
    stats = scheme.get("return_stats")
    if not isinstance(stats, list) or not stats or not isinstance(stats[0], dict):
        return {}
    row = stats[0]
    published = {}
    for key, label in RETURN_LABELS:
        if _present(row.get(key)):
            published[label] = row[key]
    return published


def build_facts(scheme: dict | None) -> dict:
    """Copy facts the scheme page publishes. Peer funds and return maths stay out."""
    if not scheme:
        return {}
    facts: dict = {}
    for key in SCALAR_FIELDS:
        if key in scheme and _present(scheme[key]):
            facts[key] = scheme[key]
    lock_in = scheme.get("lock_in")
    if isinstance(lock_in, dict):
        facts["lock_in"] = {
            "years": lock_in.get("years"),
            "months": lock_in.get("months"),
            "days": lock_in.get("days"),
        }
    stats = scheme.get("return_stats")
    if isinstance(stats, list) and stats and isinstance(stats[0], dict):
        risk = stats[0].get("risk")
        if _present(risk):
            facts["risk"] = risk
    managers = _managers(scheme)
    if managers:
        facts["fund_managers"] = managers
    holdings = _holdings(scheme)
    if holdings:
        facts["holdings"] = holdings
    returns = _published_returns(scheme)
    if returns:
        facts["returns"] = returns
    category_info = scheme.get("category_info")
    if isinstance(category_info, dict) and _present(category_info.get("tax_impact")):
        facts["tax_note"] = category_info["tax_impact"]
    return facts


def _sidecar_hash(root: Path) -> str:
    sidecars = []
    raw = data_dir(root) / "raw"
    if raw.exists():
        for meta_path in sorted(raw.glob("*/meta.json")):
            sidecars.append(json.loads(meta_path.read_text(encoding="utf-8")))
    canonical = json.dumps(sorted(sidecars, key=lambda item: item["source_id"]), sort_keys=True)
    return _sha256(canonical.encode("utf-8"))


def _clear_downstream(root: Path) -> None:
    base = data_dir(root)
    for name in DOWNSTREAM_DIRS:
        path = base / name
        if path.exists():
            shutil.rmtree(path)
    pipeline = read_pipeline(root)
    for stage in ("chunk", "embed", "index"):
        pipeline["stages"][stage] = {"status": "stale"}
    write_pipeline(pipeline, root)


def run(root: Path | None = None) -> int:
    from app.store.layout import repo_root

    root = root or repo_root()
    pipeline = read_pipeline(root)
    scrape = pipeline.get("stages", {}).get("scrape", {})
    if scrape.get("status") != "ok":
        raise SystemExit("scrape has not finished; run python -m app.cli scrape first")
    current_hash = _sidecar_hash(root)
    if current_hash != scrape.get("output_hash"):
        raise SystemExit("raw pages do not match the scrape watermark; run scrape again")

    _clear_downstream(root)
    raw = data_dir(root) / "raw"
    documents = []
    skipped = []
    for meta_path in sorted(raw.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        source_id = meta.get("source_id") or meta_path.parent.name
        if meta.get("status") != "ok":
            skipped.append({"source_id": source_id, "reason": meta.get("error") or "scrape_failed"})
            print(f"skipped {source_id}: scrape {meta.get('status')}")
            continue
        text_path = meta_path.parent / "text.txt"
        if not text_path.exists():
            skipped.append({"source_id": source_id, "reason": "missing_text"})
            print(f"skipped {source_id}: missing text")
            continue
        scheme = None
        next_path = meta_path.parent / "next.json"
        if next_path.exists():
            scheme = json.loads(next_path.read_text(encoding="utf-8"))
        text = text_path.read_text(encoding="utf-8")
        if meta.get("page_type") == "help":
            text = help_article(text)
        documents.append(
            {
                "source_id": source_id,
                "url": meta.get("url", ""),
                "title": meta.get("title", ""),
                "page_type": meta.get("page_type", ""),
                "scheme_name": meta.get("scheme_name", ""),
                "fetched_at": meta.get("fetched_at", ""),
                "text": text,
                "facts": build_facts(scheme if isinstance(scheme, dict) else None),
            }
        )

    out = documents_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(document, ensure_ascii=False, sort_keys=True) for document in documents]
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    out.write_bytes(payload)
    (out.parent / "skipped.json").write_text(json.dumps(skipped, indent=2) + "\n", encoding="utf-8")

    finished = datetime.now(IST).isoformat(timespec="seconds")
    pipeline = read_pipeline(root)
    pipeline["stages"]["load"] = {
        "status": "ok",
        "finished_at": finished,
        "input_hash": current_hash,
        "output_hash": _sha256(payload),
    }
    write_pipeline(pipeline, root)
    print(f"loaded {len(documents)} documents, skipped {len(skipped)}")
    return 0
