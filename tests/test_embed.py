from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.ingest.embed import encode_texts, output_hash, run

ROOT = Path(__file__).resolve().parents[1]


def _encode(texts: list[str]) -> list[list[float]]:
    return [[float(len(text)), 0.5] for text in texts]


def _prepare(tmp_path: Path) -> list[dict]:
    (tmp_path / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    chunks = [
        {
            "chunk_id": "hdfc-large-cap:expense_ratio:0",
            "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            "scheme_name": "HDFC Large Cap Fund Direct Growth",
            "fact_type": "expense_ratio",
            "fetched_at": "2026-11-01",
            "text": "Expense ratio: 1.02% for HDFC Large Cap Fund Direct Growth, Direct Plan Growth.",
        },
        {
            "chunk_id": "hdfc-amc:amc_overview:0",
            "source_url": "https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
            "scheme_name": "",
            "fact_type": "amc_overview",
            "fetched_at": "2026-11-01",
            "text": "HDFC Mutual Fund overview.",
        },
    ]
    payload = "".join(json.dumps(chunk) + "\n" for chunk in chunks).encode("utf-8")
    path = tmp_path / "data" / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    (tmp_path / "data" / "chroma").mkdir(parents=True)
    (tmp_path / "data" / "chroma" / "old.txt").write_text("stale", encoding="utf-8")
    pipeline = {
        "embedding_model": "",
        "embedding_dim": None,
        "stages": {
            "chunk": {"status": "ok", "output_hash": hashlib.sha256(payload).hexdigest()},
            "embed": {"status": "missing"},
            "index": {"status": "ok"},
        },
    }
    (tmp_path / "data" / "pipeline.json").write_text(json.dumps(pipeline), encoding="utf-8")
    return chunks


def test_embed_writes_one_normalized_vector_per_chunk(tmp_path: Path) -> None:
    chunks = _prepare(tmp_path)
    assert run(tmp_path, encode=_encode) == 0
    rows = [
        json.loads(line)
        for line in (tmp_path / "data" / "embeddings" / "embeddings.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["chunk_id"] for row in rows] == [chunk["chunk_id"] for chunk in chunks]
    assert rows[0]["model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert rows[0]["dim"] == 2
    assert rows[0]["vector"] == [float(len(chunks[0]["text"])), 0.5]
    assert rows[0]["metadata"] == {
        "source_url": chunks[0]["source_url"],
        "scheme_name": chunks[0]["scheme_name"],
        "fact_type": "expense_ratio",
        "fetched_at": "2026-11-01",
    }
    assert "text" not in rows[0]
    pipeline = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert pipeline["stages"]["embed"]["status"] == "ok"
    assert pipeline["stages"]["embed"]["input_hash"] == pipeline["stages"]["chunk"]["output_hash"]
    assert pipeline["embedding_dim"] == 2
    assert pipeline["stages"]["embed"]["output_hash"] == output_hash(
        [chunk["chunk_id"] for chunk in chunks],
        "sentence-transformers/all-MiniLM-L6-v2",
        2,
    )
    assert pipeline["stages"]["index"]["status"] == "stale"
    assert not (tmp_path / "data" / "chroma").exists()


def test_embed_refuses_a_stale_chunk_file(tmp_path: Path) -> None:
    _prepare(tmp_path)
    path = tmp_path / "data" / "chunks" / "chunks.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="does not match the chunk watermark"):
        run(tmp_path, encode=_encode)


def test_encode_texts_requests_normalized_batches() -> None:
    class Model:
        def encode(self, texts, batch_size, normalize_embeddings, show_progress_bar):
            assert batch_size == 64
            assert normalize_embeddings is True
            assert show_progress_bar is False
            return [[0.1, 0.2] for _ in texts]

    assert encode_texts(Model(), ["one", "two"], 64) == [[0.1, 0.2], [0.1, 0.2]]
