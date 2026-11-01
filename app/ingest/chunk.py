"""Build fact chunks from loaded documents. Scheme facts stay one chunk each."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import load_settings
from app.ingest.split import split_sections
from app.store.layout import chunks_path, data_dir, documents_path, read_pipeline, write_pipeline

IST = ZoneInfo("Asia/Kolkata")
PAGE_FACT = {
    "amc": "amc_overview",
    "help": "statement_download",
    "regulator": "investor_education",
    "factsheet": "factsheet",
}
EXPECTED = (
    "expense_ratio",
    "exit_load",
    "minimum_sip",
    "minimum_lumpsum",
    "lock_in",
    "riskometer",
    "benchmark",
    "investment_objective",
    "category",
    "factsheet_link",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _flat(value: object) -> str:
    return " ".join(str(value).split())


def _percent(value: object) -> str:
    text = _flat(value)
    return text if text.endswith("%") else f"{text}%"


def _present_fact(value: object) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _managers_text(people: list, scheme_name: str) -> str:
    parts = []
    for person in people:
        detail = person["name"]
        if person.get("since"):
            detail += f", managing since {person['since']}"
        if person.get("education"):
            detail += f". Education: {_flat(person['education'])}"
        if person.get("experience"):
            detail += f". Experience: {_flat(person['experience'])}"
        parts.append(detail)
    return f"Fund managers for {scheme_name}: " + " ".join(parts)


def _holdings_text(rows: list, scheme_name: str) -> str:
    parts = []
    for row in rows:
        weight = row.get("weight")
        sector = f", {row['sector']}" if row.get("sector") else ""
        share = f" {weight}%" if _present_fact(weight) else ""
        parts.append(f"{row['company']}{share}{sector}")
    return f"Holdings for {scheme_name}: " + "; ".join(parts) + "."


def _returns_text(returns: dict, scheme_name: str) -> str:
    parts = [f"{label} {value}%" for label, value in returns.items()]
    return f"Published returns for {scheme_name}: " + ", ".join(parts) + "."


def lock_in_text(lock: dict, scheme_name: str) -> str:
    parts = []
    for unit in ("years", "months", "days"):
        value = lock.get(unit)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            continue
        number = int(value) if float(value).is_integer() else value
        parts.append(f"{number} {unit}")
    if not parts:
        return f"Lock-in: the scheme page does not state a lock-in period for {scheme_name}."
    return f"Lock-in: {', '.join(parts)} for {scheme_name}."


def scheme_chunks(document: dict, params: dict) -> tuple[list[dict], list[str]]:
    facts = document.get("facts") or {}
    name = document.get("scheme_name") or facts.get("scheme_name") or document["source_id"]
    plan = _flat(facts.get("plan_type") or "")
    option = _flat(facts.get("scheme_type") or "")
    notes: list[str] = []
    if plan and plan.lower() != "direct":
        notes.append("plan_mismatch")
    if option and option.lower() != "growth":
        notes.append("plan_mismatch")

    texts: dict[str, str] = {}
    if "expense_ratio" in facts:
        plan_label = "Direct Plan Growth" if not plan or plan.lower() == "direct" else plan
        texts["expense_ratio"] = f"Expense ratio: {_percent(facts['expense_ratio'])} for {name}, {plan_label}."
    if "exit_load" in facts:
        texts["exit_load"] = f"Exit load: {_flat(facts['exit_load'])}"
    if "min_sip_investment" in facts:
        texts["minimum_sip"] = f"Minimum SIP: ₹{facts['min_sip_investment']} for {name}."
    if "min_investment_amount" in facts:
        texts["minimum_lumpsum"] = f"Minimum lump sum: ₹{facts['min_investment_amount']} for {name}."
    if isinstance(facts.get("lock_in"), dict):
        texts["lock_in"] = lock_in_text(facts["lock_in"], name)
    if facts.get("risk"):
        texts["riskometer"] = f"Riskometer: {_flat(facts['risk'])} for {name}."
    if facts.get("benchmark_name"):
        texts["benchmark"] = f"Benchmark: {_flat(facts['benchmark_name'])} for {name}."
    if facts.get("description"):
        texts["investment_objective"] = f"Investment objective: {_flat(facts['description'])}"
    if facts.get("category") and facts.get("sub_category"):
        texts["category"] = (
            f"Category: {_flat(facts['category'])}, sub-category {_flat(facts['sub_category'])}, for {name}."
        )
    elif facts.get("category"):
        texts["category"] = f"Category: {_flat(facts['category'])} for {name}."
    elif facts.get("sub_category"):
        texts["category"] = f"Sub-category: {_flat(facts['sub_category'])} for {name}."
    if facts.get("sid_url"):
        texts["factsheet_link"] = f"Scheme information document: {_flat(facts['sid_url'])}"
    if facts.get("fund_managers"):
        texts["fund_manager"] = _managers_text(facts["fund_managers"], name)
    if facts.get("holdings"):
        texts["holdings"] = _holdings_text(facts["holdings"], name)
    if facts.get("returns"):
        texts["returns"] = _returns_text(facts["returns"], name)
    if _present_fact(facts.get("aum")):
        texts["aum"] = f"AUM: ₹{facts['aum']} crore for {name}."
    if _present_fact(facts.get("nav")):
        as_of = f" as of {facts['nav_date']}" if facts.get("nav_date") else ""
        texts["nav"] = f"NAV: ₹{facts['nav']}{as_of} for {name}."
    if facts.get("launch_date"):
        texts["launch_date"] = f"Launch date: {_flat(facts['launch_date'])} for {name}."
    if _present_fact(facts.get("base_expense_ratio")):
        texts["base_expense_ratio"] = f"Base expense ratio: {_percent(facts['base_expense_ratio'])} for {name}."
    if facts.get("stamp_duty"):
        texts["stamp_duty"] = f"Stamp duty: {_flat(facts['stamp_duty'])} for {name}."
    if _present_fact(facts.get("portfolio_turnover")):
        texts["portfolio_turnover"] = f"Portfolio turnover: {facts['portfolio_turnover']} for {name}."
    if _present_fact(facts.get("min_withdrawal")):
        texts["min_withdrawal"] = f"Minimum withdrawal: ₹{facts['min_withdrawal']} for {name}."
    if _present_fact(facts.get("mini_additional_investment")):
        texts["additional_investment"] = f"Minimum additional investment: ₹{facts['mini_additional_investment']} for {name}."
    if facts.get("isin"):
        texts["isin"] = f"ISIN: {_flat(facts['isin'])} for {name}."
    if facts.get("tax_note"):
        texts["tax_note"] = f"Tax note for {name}: {_flat(facts['tax_note'])}"

    missing = [fact_type for fact_type in EXPECTED if fact_type not in texts]
    chunks = [
        _record(
            document,
            fact_type=fact_type,
            text=text,
            index=0,
            strategy="scheme_fact_blocks",
            params=params,
            scheme_name=name,
            plan=plan,
            option=option,
            amc="HDFC Mutual Fund",
        )
        for fact_type, text in texts.items()
    ]
    return chunks, missing + notes


def prose_chunks(document: dict, params: dict, strategy: str) -> list[dict]:
    fact_type = PAGE_FACT.get(document.get("page_type", ""), "investor_education")
    pieces = split_sections(
        document.get("text") or "",
        params["chunk_max_chars"],
        params["chunk_overlap_chars"],
    )
    amc = "HDFC Mutual Fund" if document.get("page_type") == "amc" else ""
    return [
        _record(
            document,
            fact_type=fact_type,
            text=piece,
            index=index,
            strategy=strategy,
            params=params,
            scheme_name="",
            plan="",
            option="",
            amc=amc,
        )
        for index, piece in enumerate(pieces)
    ]


def _record(
    document: dict,
    *,
    fact_type: str,
    text: str,
    index: int,
    strategy: str,
    params: dict,
    scheme_name: str,
    plan: str,
    option: str,
    amc: str,
) -> dict:
    source_id = document["source_id"]
    return {
        "chunk_id": f"{source_id}:{fact_type}:{index}",
        "source_id": source_id,
        "source_url": document.get("url", ""),
        "title": document.get("title", ""),
        "amc": amc,
        "scheme_name": scheme_name,
        "plan": plan,
        "option": option,
        "fact_type": fact_type,
        "text": text,
        "fetched_at": document.get("fetched_at", ""),
        "strategy": strategy,
        "strategy_params": params,
    }


def _read_documents(root: Path) -> list[dict]:
    path = documents_path(root)
    if not path.exists():
        raise SystemExit("documents.jsonl is missing; run python -m app.cli load first")
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def run(root: Path | None = None) -> int:
    from app.store.layout import repo_root

    root = root or repo_root()
    settings = load_settings(root)
    if settings.chunk_strategy != "scheme_fact_blocks":
        raise SystemExit(f"chunk strategy must be scheme_fact_blocks, got {settings.chunk_strategy}")
    pipeline = read_pipeline(root)
    load_stage = pipeline.get("stages", {}).get("load", {})
    if load_stage.get("status") != "ok":
        raise SystemExit("load has not finished; run python -m app.cli load first")
    document_bytes = documents_path(root).read_bytes()
    if _sha256(document_bytes) != load_stage.get("output_hash"):
        raise SystemExit("documents.jsonl does not match the load watermark; run load again")

    documents = _read_documents(root)

    for name in ("embeddings", "chroma"):
        path = data_dir(root) / name
        if path.exists():
            shutil.rmtree(path)
    pipeline = read_pipeline(root)
    for stage in ("embed", "index"):
        pipeline["stages"][stage] = {"status": "stale"}
    write_pipeline(pipeline, root)

    params = {
        "chunk_max_chars": settings.chunk_max_chars,
        "chunk_overlap_chars": settings.chunk_overlap_chars,
    }
    chunks: list[dict] = []
    missing: dict[str, list[str]] = {}
    for document in documents:
        if document.get("page_type") == "scheme" and document.get("facts"):
            scheme_rows, skipped = scheme_chunks(document, params)
            chunks.extend(scheme_rows)
            if skipped:
                missing[document["source_id"]] = skipped
            continue
        strategy = "scheme_fact_blocks"
        if document.get("page_type") == "scheme":
            strategy = "scheme_fact_blocks+headings"
            missing.setdefault(document["source_id"], []).append("next_data_missing")
            print(f"{document['source_id']}: no facts, split headings instead")
        chunks.extend(prose_chunks(document, params, strategy))

    payload = "".join(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n" for chunk in chunks).encode("utf-8")
    out = chunks_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    (out.parent / "missing.json").write_text(json.dumps(missing, indent=2) + "\n", encoding="utf-8")

    finished = datetime.now(IST).isoformat(timespec="seconds")
    pipeline = read_pipeline(root)
    pipeline["chunk_strategy"] = settings.chunk_strategy
    pipeline["stages"]["chunk"] = {
        "status": "ok",
        "finished_at": finished,
        "input_hash": load_stage.get("output_hash"),
        "output_hash": _sha256(payload),
    }
    write_pipeline(pipeline, root)
    print(f"wrote {len(chunks)} chunks")
    return 0
