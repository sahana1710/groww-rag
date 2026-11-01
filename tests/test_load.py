from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ingest.load import build_facts, run


def _meta(source_id: str, status: str = "ok", page_type: str = "scheme", error: str | None = None) -> dict:
    meta = {
        "source_id": source_id,
        "url": f"https://groww.in/{source_id}",
        "title": source_id,
        "page_type": page_type,
        "scheme_name": "HDFC Example" if page_type == "scheme" else "",
        "fetched_at": "2026-11-01",
        "status": status,
    }
    if error:
        meta["error"] = error
    return meta


def _write_raw(root: Path, source_id: str, meta: dict, text: str = "Visible page\n", scheme: dict | None = None) -> None:
    folder = root / "data" / "raw" / source_id
    folder.mkdir(parents=True)
    (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    if meta["status"] == "ok":
        (folder / "text.txt").write_text(text, encoding="utf-8")
    if scheme is not None:
        (folder / "next.json").write_text(json.dumps(scheme), encoding="utf-8")


def _pipeline(root: Path, sidecars: list[dict]) -> None:
    canonical = json.dumps(sorted(sidecars, key=lambda item: item["source_id"]), sort_keys=True)
    output_hash = __import__("hashlib").sha256(canonical.encode("utf-8")).hexdigest()
    pipeline = {
        "embedding_model": "",
        "embedding_dim": None,
        "chunk_strategy": "",
        "collection": "",
        "stages": {
            "scrape": {"status": "ok", "output_hash": output_hash},
            "load": {"status": "stale"},
            "chunk": {"status": "missing"},
            "embed": {"status": "missing"},
            "index": {"status": "missing"},
        },
    }
    path = root / "data" / "pipeline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pipeline), encoding="utf-8")


def test_build_facts_keeps_risk_and_drops_returns() -> None:
    facts = build_facts(
        {
            "expense_ratio": "9.99",
            "exit_load": "Nil",
            "min_sip_investment": 100,
            "lock_in": {"years": 3, "months": 0, "days": 0},
            "peerComparison": [{"expense_ratio": "0.10"}],
            "meta_desc": "return of 50",
            "sip_return": {"return1y": 12},
            "alpha": 1.2,
            "return_stats": [{"risk": "Very High", "return1y": 12, "alpha": 0.4}],
            "sid_url": "",
        }
    )
    assert facts["expense_ratio"] == "9.99"
    assert facts["exit_load"] == "Nil"
    assert facts["lock_in"] == {"years": 3, "months": 0, "days": 0}
    assert facts["risk"] == "Very High"
    assert facts["returns"]["1 year"] == 12
    assert "sid_url" not in facts
    blob = json.dumps(facts)
    for banned in ("peerComparison", "meta_desc", "sip_return", "return1y", "alpha", "0.10", "50"):
        assert banned not in blob


def test_missing_fact_is_omitted() -> None:
    facts = build_facts({"lock_in": {"years": None, "months": None, "days": None}})
    assert "expense_ratio" not in facts
    assert facts["lock_in"]["years"] is None


def test_load_writes_documents_and_skips_failures(tmp_path: Path) -> None:
    scheme = _meta("hdfc-large-cap")
    failed = _meta("hdfc-elss", status="failed", error="http_500")
    help_page = _meta("groww-help-capital-gains", page_type="help")
    _write_raw(tmp_path, "hdfc-large-cap", scheme, scheme={"expense_ratio": "1.02", "peerComparison": [{"expense_ratio": "9"}]})
    _write_raw(tmp_path, "hdfc-elss", failed, text="")
    _write_raw(tmp_path, "groww-help-capital-gains", help_page, text="Download steps\n")
    _pipeline(tmp_path, [scheme, failed, help_page])
    (tmp_path / "data" / "chunks").mkdir()
    (tmp_path / "data" / "chunks" / "chunks.jsonl").write_text("old\n", encoding="utf-8")

    assert run(tmp_path) == 0

    lines = (tmp_path / "data" / "documents" / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    documents = [json.loads(line) for line in lines]
    assert [item["source_id"] for item in documents] == ["groww-help-capital-gains", "hdfc-large-cap"]
    by_id = {item["source_id"]: item for item in documents}
    assert by_id["groww-help-capital-gains"]["facts"] == {}
    assert by_id["hdfc-large-cap"]["facts"] == {"expense_ratio": "1.02"}
    assert "9" not in json.dumps(by_id["hdfc-large-cap"]["facts"])
    skipped = json.loads((tmp_path / "data" / "documents" / "skipped.json").read_text(encoding="utf-8"))
    assert skipped == [{"source_id": "hdfc-elss", "reason": "http_500"}]
    assert not (tmp_path / "data" / "chunks").exists()
    pipeline = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert pipeline["stages"]["load"]["status"] == "ok"
    assert pipeline["stages"]["load"]["input_hash"] == pipeline["stages"]["scrape"]["output_hash"]
    assert pipeline["stages"]["chunk"]["status"] == "stale"


def test_load_refuses_when_scrape_is_stale(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "pipeline.json").write_text(
        json.dumps({"stages": {"scrape": {"status": "stale"}}}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="scrape has not finished"):
        run(tmp_path)
