from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ingest.embed import output_hash
from app.ingest.index import run

ROOT = Path(__file__).resolve().parents[1]
SCHEMES = [
    "HDFC Large Cap Fund Direct Growth",
    "HDFC Flexi Cap Direct Plan Growth",
    "HDFC ELSS Tax Saver Fund Direct Plan Growth",
    "HDFC Mid Cap Fund Direct Growth",
]


def _prepare(tmp_path: Path, *, missing_scheme: str | None = None) -> None:
    (tmp_path / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    chunks = []
    embeddings = []
    for index, scheme in enumerate(SCHEMES):
        if scheme == missing_scheme:
            continue
        chunk_id = f"scheme-{index}:expense_ratio:0"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "source_id": f"scheme-{index}",
                "source_url": f"https://groww.in/mutual-funds/scheme-{index}",
                "scheme_name": scheme,
                "fact_type": "expense_ratio",
                "fetched_at": "2026-11-01",
                "plan": "Direct",
                "option": "Growth",
                "amc": "HDFC Mutual Fund",
                "title": scheme,
                "text": f"Expense ratio: 1.0{index}% for {scheme}.",
            }
        )
        embeddings.append(
            {
                "chunk_id": chunk_id,
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dim": 2,
                "vector": [float(index), 0.1],
                "metadata": {"source_url": chunks[-1]["source_url"], "scheme_name": scheme, "fact_type": "expense_ratio", "fetched_at": "2026-11-01"},
            }
        )
    chunk_path = tmp_path / "data" / "chunks" / "chunks.jsonl"
    embed_path = tmp_path / "data" / "embeddings" / "embeddings.jsonl"
    chunk_path.parent.mkdir(parents=True)
    embed_path.parent.mkdir(parents=True)
    chunk_path.write_text("".join(json.dumps(row) + "\n" for row in chunks), encoding="utf-8")
    embed_path.write_text("".join(json.dumps(row) + "\n" for row in embeddings), encoding="utf-8")
    ids = [row["chunk_id"] for row in embeddings]
    pipeline = {
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dim": 2,
        "stages": {
            "embed": {"status": "ok", "output_hash": output_hash(ids, "sentence-transformers/all-MiniLM-L6-v2", 2)},
            "index": {"status": "stale"},
        },
    }
    (tmp_path / "data" / "pipeline.json").write_text(json.dumps(pipeline), encoding="utf-8")


def test_index_stores_one_expense_ratio_per_scheme(tmp_path: Path) -> None:
    _prepare(tmp_path)
    assert run(tmp_path) == 0
    assert run(tmp_path) == 0
    import chromadb

    client = chromadb.PersistentClient(path=str(tmp_path / "data" / "chroma"))
    collection = client.get_collection("hdfc_mf_facts")
    assert collection.count() == 4
    assert collection.metadata["hnsw:space"] == "cosine"
    assert collection.metadata["embedding_dim"] == 2
    row = collection.get(where={"scheme_name": SCHEMES[0]}, include=["documents", "metadatas"])
    assert row["documents"] == ["Expense ratio: 1.00% for HDFC Large Cap Fund Direct Growth."]
    assert row["metadatas"][0]["plan"] == "Direct"
    assert row["metadatas"][0]["fact_type"] == "expense_ratio"
    pipeline = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert pipeline["stages"]["index"]["status"] == "ok"
    assert pipeline["stages"]["index"]["input_hash"] == pipeline["stages"]["embed"]["output_hash"]
    assert pipeline["collection"] == "hdfc_mf_facts"


def test_index_fails_when_a_scheme_expense_ratio_is_missing(tmp_path: Path) -> None:
    _prepare(tmp_path, missing_scheme=SCHEMES[3])
    with pytest.raises(SystemExit, match="HDFC Mid Cap Fund Direct Growth"):
        run(tmp_path)
    pipeline = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert pipeline["stages"]["index"]["status"] == "failed"
