from __future__ import annotations

import json
from pathlib import Path

from app.ingest.chunk import lock_in_text, run
from app.ingest.split import split_sections

ROOT = Path(__file__).resolve().parents[1]


def test_lock_in_keeps_only_positive_parts() -> None:
    name = "HDFC ELSS Tax Saver Fund Direct Plan Growth"
    text = lock_in_text({"years": 3, "months": 0, "days": 0}, name)
    assert text == f"Lock-in: 3 years for {name}."
    assert "0 months" not in text
    empty = lock_in_text({"years": None, "months": None, "days": None}, name)
    assert "does not state a lock-in period" in empty


def test_numbered_step_is_not_split_and_overlap_keeps_words() -> None:
    step = "1. " + ("Download the capital-gains statement from Reports. " * 5)
    pieces = split_sections(step, max_chars=40, overlap=10)
    assert pieces == [step.strip()]
    prose = (
        "Alpha beta gamma delta epsilon zeta. "
        "Eta theta iota kappa lambda mu nu xi."
    )
    packed = split_sections(prose, max_chars=28, overlap=12)
    assert len(packed) > 1
    for piece in packed[1:]:
        assert piece.split()[0] in {"Alpha", "beta", "gamma", "delta", "epsilon", "zeta.", "Eta", "theta", "iota"}


def test_chunk_writes_scheme_facts_and_skips_page_returns(tmp_path: Path) -> None:
    _prepare(tmp_path, sid_url="")
    assert run(tmp_path) == 0
    chunks = [
        json.loads(line)
        for line in (tmp_path / "data" / "chunks" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    by_type = {chunk["fact_type"]: chunk for chunk in chunks if chunk["source_id"] == "hdfc-large-cap"}
    assert "9.99%" in by_type["expense_ratio"]["text"]
    assert by_type["exit_load"]["text"] == "Exit load: Nil"
    assert "return of 50" not in json.dumps(by_type)
    assert by_type["expense_ratio"]["chunk_id"] == "hdfc-large-cap:expense_ratio:0"
    assert len(by_type["exit_load"]["text"]) > 0
    help_chunks = [chunk for chunk in chunks if chunk["source_id"] == "groww-help"]
    assert help_chunks
    assert help_chunks[0]["fact_type"] == "statement_download"
    assert help_chunks[0]["scheme_name"] == ""
    help_text = " ".join(chunk["text"] for chunk in help_chunks)
    assert "1. Open Reports and download the capital-gains statement for the financial year." in help_text
    step_chunks = [chunk for chunk in help_chunks if chunk["text"].startswith("1. ")]
    assert len(step_chunks) == 1
    pipeline = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert pipeline["stages"]["chunk"]["status"] == "ok"
    assert pipeline["stages"]["chunk"]["input_hash"] == pipeline["stages"]["load"]["output_hash"]


def test_sid_is_quoted_and_not_added_to_the_source_list(tmp_path: Path) -> None:
    _prepare(tmp_path, sid_url="https://www.hdfcfund.com")
    assert run(tmp_path) == 0
    chunks = [
        json.loads(line)
        for line in (tmp_path / "data" / "chunks" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    factsheet = next(chunk for chunk in chunks if chunk["fact_type"] == "factsheet_link")
    assert factsheet["text"] == "Scheme information document: https://www.hdfcfund.com"
    csv_text = (tmp_path / "sources" / "sources.csv").read_text(encoding="utf-8")
    assert "hdfcfund.com" not in csv_text


def _prepare(tmp_path: Path, sid_url: str) -> None:
    (tmp_path / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    lines = ["id,url,publisher,page_type,scheme_name,why_included"]
    for index in range(15):
        lines.append(f"src-{index},https://groww.in/help/item-{index},Groww,help,,because")
    (source_dir / "sources.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    documents = [
        {
            "source_id": "hdfc-large-cap",
            "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            "title": "HDFC Large Cap Fund Direct Growth",
            "page_type": "scheme",
            "scheme_name": "HDFC Large Cap Fund Direct Growth",
            "fetched_at": "2026-11-01",
            "text": "Visible page mentions return of 50 which must not be chunked.",
            "facts": {
                "expense_ratio": "9.99",
                "exit_load": "Nil",
                "min_sip_investment": 100,
                "lock_in": {"years": None, "months": None, "days": None},
                "risk": "Very High",
                "benchmark_name": "NIFTY 100 Total Return Index",
                "description": "Long-term capital appreciation.",
                "category": "Equity",
                "sub_category": "Large Cap",
                "plan_type": "Direct",
                "scheme_type": "Growth",
                "peerComparison": [{"expense_ratio": "0.10"}],
                "sid_url": sid_url,
            },
        },
        {
            "source_id": "groww-help",
            "url": "https://groww.in/help/capital-gains",
            "title": "Capital gains",
            "page_type": "help",
            "scheme_name": "",
            "fetched_at": "2026-11-01",
            "text": "How to download\n\n1. Open Reports and download the capital-gains statement for the financial year.\n",
            "facts": {},
        },
    ]
    payload = "".join(json.dumps(document, sort_keys=True) + "\n" for document in documents).encode("utf-8")
    doc_path = tmp_path / "data" / "documents" / "documents.jsonl"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_bytes(payload)
    output_hash = __import__("hashlib").sha256(payload).hexdigest()
    pipeline = {
        "stages": {
            "load": {"status": "ok", "output_hash": output_hash},
            "chunk": {"status": "stale"},
            "embed": {"status": "missing"},
            "index": {"status": "missing"},
        }
    }
    (tmp_path / "data" / "pipeline.json").write_text(json.dumps(pipeline), encoding="utf-8")
