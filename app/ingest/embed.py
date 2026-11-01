"""Embed chunk text with the local MiniLM model. Questions are not encoded here."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings, load_settings
from app.store.layout import chunks_path, data_dir, embeddings_path, read_pipeline, write_pipeline

IST = ZoneInfo("Asia/Kolkata")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def output_hash(chunk_ids: list[str], model: str, dim: int) -> str:
    body = "\n".join([*chunk_ids, model, str(dim)]).encode("utf-8")
    return _sha256(body)


def _read_chunks(root: Path) -> list[dict]:
    path = chunks_path(root)
    if not path.exists():
        raise SystemExit("chunks.jsonl is missing; run python -m app.cli chunk first")
    lines = path.read_text(encoding="utf-8").splitlines()
    chunks = [json.loads(line) for line in lines if line.strip()]
    if not chunks:
        raise SystemExit("chunks.jsonl is empty; run python -m app.cli chunk first")
    ids = [chunk["chunk_id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise SystemExit("chunk ids are not unique")
    return chunks


def encode_texts(model: object, texts: list[str], batch_size: int) -> list[list[float]]:
    array = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [[float(value) for value in row] for row in array]


def _load_encoder(settings: Settings):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings.embedding_model)

    def encode(texts: list[str]) -> list[list[float]]:
        return encode_texts(model, texts, settings.embedding_batch_size)

    return encode


def _record(chunk: dict, vector: list[float], model: str) -> dict:
    return {
        "chunk_id": chunk["chunk_id"],
        "model": model,
        "dim": len(vector),
        "vector": vector,
        "metadata": {
            "source_url": chunk.get("source_url") or "",
            "scheme_name": chunk.get("scheme_name") or "",
            "fact_type": chunk.get("fact_type") or "",
            "fetched_at": chunk.get("fetched_at") or "",
        },
    }


def run(root: Path | None = None, encode=None) -> int:
    from app.store.layout import repo_root

    root = root or repo_root()
    settings = load_settings(root)
    pipeline = read_pipeline(root)
    chunk_stage = pipeline.get("stages", {}).get("chunk", {})
    if chunk_stage.get("status") != "ok":
        raise SystemExit("chunk has not finished; run python -m app.cli chunk first")
    chunk_bytes = chunks_path(root).read_bytes()
    if _sha256(chunk_bytes) != chunk_stage.get("output_hash"):
        raise SystemExit("chunks.jsonl does not match the chunk watermark; run chunk again")

    chunks = _read_chunks(root)
    chroma = data_dir(root) / "chroma"
    if chroma.exists():
        shutil.rmtree(chroma)
    pipeline = read_pipeline(root)
    pipeline["stages"]["index"] = {"status": "stale"}
    write_pipeline(pipeline, root)

    vectors = (encode or _load_encoder(settings))([chunk.get("text") or "" for chunk in chunks])
    if len(vectors) != len(chunks):
        raise SystemExit(f"encoder returned {len(vectors)} vectors for {len(chunks)} chunks")
    dims = {len(vector) for vector in vectors}
    if len(dims) != 1:
        raise SystemExit(f"embedding dimensions differ: {sorted(dims)}")
    dim = dims.pop()
    if dim < 1:
        raise SystemExit("embedding dimension is empty")

    rows = [_record(chunk, vector, settings.embedding_model) for chunk, vector in zip(chunks, vectors)]
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8")
    path = embeddings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".jsonl.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    if sum(1 for line in payload.splitlines() if line) != len(chunks):
        raise SystemExit("embedding line count does not match the chunk count")

    finished = datetime.now(IST).isoformat(timespec="seconds")
    pipeline = read_pipeline(root)
    pipeline["embedding_model"] = settings.embedding_model
    pipeline["embedding_dim"] = dim
    pipeline["stages"]["embed"] = {
        "status": "ok",
        "finished_at": finished,
        "input_hash": chunk_stage.get("output_hash"),
        "output_hash": output_hash([chunk["chunk_id"] for chunk in chunks], settings.embedding_model, dim),
    }
    pipeline["stages"]["index"] = {"status": "stale"}
    write_pipeline(pipeline, root)
    print(f"wrote {len(rows)} embeddings, dim {dim}")
    return 0
