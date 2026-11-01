"""Store chunk vectors in a persistent Chroma collection."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings, load_settings
from app.ingest.embed import output_hash
from app.store.layout import chunks_path, embeddings_path, read_pipeline, write_pipeline

IST = ZoneInfo("Asia/Kolkata")
METADATA_FIELDS = (
    "source_id",
    "source_url",
    "scheme_name",
    "fact_type",
    "fetched_at",
    "plan",
    "option",
    "amc",
    "title",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def index_output_hash(chunk_ids: list[str], model: str, dim: int, collection: str, space: str) -> str:
    body = "\n".join([collection, space, model, str(dim), *chunk_ids]).encode("utf-8")
    return _sha256(body)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _read_jsonl(path: Path, label: str) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"{label} is missing")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise SystemExit(f"{label} is empty")
    return rows


def _chroma_dir(root: Path, settings: Settings) -> Path:
    path = Path(settings.chroma_path)
    if not path.is_absolute():
        path = root / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _collection(client: object, settings: Settings, dim: int):
    name = settings.chroma_collection
    metadata = {
        "hnsw:space": settings.chroma_space,
        "embedding_model": settings.embedding_model,
        "embedding_dim": dim,
    }
    try:
        current = client.get_collection(name)
    except Exception:
        current = None
    if current is not None:
        stored = current.metadata or {}
        mismatch = (
            stored.get("hnsw:space") != settings.chroma_space
            or stored.get("embedding_model") != settings.embedding_model
            or stored.get("embedding_dim") != dim
        )
        if mismatch:
            client.delete_collection(name)
            current = None
    if current is None:
        return client.create_collection(name=name, metadata=metadata)
    return current


def _mark(root: Path, status: str, **fields: object) -> None:
    pipeline = read_pipeline(root)
    stage = {"status": status, "finished_at": datetime.now(IST).isoformat(timespec="seconds")}
    stage.update(fields)
    pipeline["stages"]["index"] = stage
    write_pipeline(pipeline, root)


def run(root: Path | None = None) -> int:
    from app.store.layout import repo_root

    root = root or repo_root()
    settings = load_settings(root)
    pipeline = read_pipeline(root)
    embed_stage = pipeline.get("stages", {}).get("embed", {})
    if embed_stage.get("status") != "ok":
        raise SystemExit("embed has not finished; run python -m app.cli embed first")

    embeddings = _read_jsonl(embeddings_path(root), "embeddings.jsonl")
    chunks = {row["chunk_id"]: row for row in _read_jsonl(chunks_path(root), "chunks.jsonl")}
    ids = [row["chunk_id"] for row in embeddings]
    if len(ids) != len(set(ids)):
        raise SystemExit("embedding chunk ids are not unique")
    if set(ids) != set(chunks):
        raise SystemExit("embeddings.jsonl does not match chunks.jsonl")

    dim = embeddings[0]["dim"]
    model = embeddings[0]["model"]
    if model != settings.embedding_model:
        raise SystemExit(f"embedding model is {model}; config expects {settings.embedding_model}")
    if any(row["dim"] != dim or row["model"] != model for row in embeddings):
        raise SystemExit("embedding rows disagree on model or dimension")
    expected = output_hash(ids, model, dim)
    if expected != embed_stage.get("output_hash") or pipeline.get("embedding_dim") != dim:
        raise SystemExit("embeddings.jsonl does not match the embed watermark; run embed again")

    vectors = [row["vector"] for row in embeddings]
    documents = [chunks[chunk_id].get("text") or "" for chunk_id in ids]
    metadatas = []
    for chunk_id in ids:
        chunk = chunks[chunk_id]
        metadatas.append({field: _text(chunk.get(field)) for field in METADATA_FIELDS})

    import chromadb

    client = chromadb.PersistentClient(path=str(_chroma_dir(root, settings)))
    collection = _collection(client, settings, dim)
    existing = collection.get(include=[])
    stale = [chunk_id for chunk_id in existing.get("ids", []) if chunk_id not in set(ids)]
    if stale:
        collection.delete(ids=stale)
    collection.upsert(ids=ids, embeddings=vectors, documents=documents, metadatas=metadatas)

    for scheme in settings.schemes:
        found = collection.get(
            where={"$and": [{"fact_type": "expense_ratio"}, {"scheme_name": scheme.scheme_name}]},
            include=[],
        )
        hits = found.get("ids") or []
        if len(hits) != 1:
            _mark(root, "failed")
            raise SystemExit(
                f"expense ratio check failed for {scheme.scheme_name}: expected 1 chunk, found {len(hits)}"
            )

    if collection.count() != len(ids):
        _mark(root, "failed")
        raise SystemExit(f"collection has {collection.count()} rows for {len(ids)} embeddings")

    pipeline = read_pipeline(root)
    pipeline["collection"] = settings.chroma_collection
    pipeline["stages"]["index"] = {
        "status": "ok",
        "finished_at": datetime.now(IST).isoformat(timespec="seconds"),
        "input_hash": embed_stage.get("output_hash"),
        "output_hash": index_output_hash(ids, model, dim, settings.chroma_collection, settings.chroma_space),
    }
    write_pipeline(pipeline, root)
    print(f"indexed {len(ids)} chunks in {settings.chroma_collection}")
    return 0
