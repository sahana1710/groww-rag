"""Search the stored MiniLM vectors. Question time does not need Chroma."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.store.layout import IndexNotReady, chunks_path, embeddings_path

_MODELS: dict[str, object] = {}
_ROWS: dict[str, list["Stored"]] = {}


@dataclass(frozen=True)
class Stored:
    chunk_id: str
    vector: tuple[float, ...]
    fact_type: str
    scheme_name: str
    source_url: str
    fetched_at: str
    text: str


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    chroma_distance: float
    fact_type: str
    scheme_name: str
    source_url: str
    fetched_at: str
    text: str


def _onnx_dir(folder: Path) -> Path | None:
    matches = [path for path in folder.rglob("model.onnx") if path.is_file() and path.stat().st_size > 1_000_000]
    return matches[0].parent if matches else None


def cache_dir(root: Path) -> Path:
    """Use the model shipped with the deploy. Downloads go to /tmp, which is writable."""
    home = Path("/tmp/hf-home")
    home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(home)
    os.environ["HF_HUB_CACHE"] = str(home / "hub")
    os.environ["XDG_CACHE_HOME"] = str(home)
    bundled = root / "models" / "fastembed"
    if _onnx_dir(bundled):
        os.environ["FASTEMBED_CACHE_PATH"] = str(bundled)
        return bundled
    path = Path("/tmp/fastembed")
    path.mkdir(parents=True, exist_ok=True)
    os.environ["FASTEMBED_CACHE_PATH"] = str(path)
    return path


def _model(name: str, root: Path):
    if name not in _MODELS:
        from fastembed import TextEmbedding

        folder = cache_dir(root)
        kwargs = {"model_name": name, "cache_dir": str(folder)}
        snapshot = _onnx_dir(folder)
        if snapshot:
            kwargs["specific_model_path"] = str(snapshot)
            kwargs["local_files_only"] = True
        _MODELS[name] = TextEmbedding(**kwargs)
    return _MODELS[name]


def encode_query(model_name: str, question: str, root: Path) -> list[float]:
    vector = list(_model(model_name, root).embed([question]))[0]
    return [float(value) for value in vector]


def load_rows(root: Path) -> list[Stored]:
    key = str(root.resolve())
    if key in _ROWS:
        return _ROWS[key]
    chunk_file = chunks_path(root)
    embed_file = embeddings_path(root)
    if not chunk_file.exists() or not embed_file.exists():
        raise IndexNotReady("index")
    chunks = {}
    for line in chunk_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunk = json.loads(line)
            chunks[chunk["chunk_id"]] = chunk
    rows: list[Stored] = []
    for line in embed_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        chunk = chunks.get(item["chunk_id"])
        if chunk is None:
            continue
        meta = item.get("metadata") or {}
        rows.append(
            Stored(
                chunk_id=item["chunk_id"],
                vector=tuple(float(value) for value in item["vector"]),
                fact_type=str(meta.get("fact_type") or chunk.get("fact_type") or ""),
                scheme_name=str(meta.get("scheme_name") or chunk.get("scheme_name") or ""),
                source_url=str(meta.get("source_url") or chunk.get("source_url") or ""),
                fetched_at=str(meta.get("fetched_at") or chunk.get("fetched_at") or ""),
                text=chunk.get("text") or "",
            )
        )
    if not rows:
        raise IndexNotReady("index")
    _ROWS[key] = rows
    return rows


def rank(rows: list[Stored], vector: list[float], scheme_name: str, fact_type: str, top_k: int) -> list[Hit]:
    scored: list[Hit] = []
    for row in rows:
        if scheme_name and row.scheme_name != scheme_name:
            continue
        if fact_type and row.fact_type != fact_type:
            continue
        dot = sum(left * right for left, right in zip(vector, row.vector))
        scored.append(
            Hit(
                chunk_id=row.chunk_id,
                chroma_distance=1.0 - dot,
                fact_type=row.fact_type,
                scheme_name=row.scheme_name,
                source_url=row.source_url,
                fetched_at=row.fetched_at,
                text=row.text,
            )
        )
    scored.sort(key=lambda hit: hit.chroma_distance)
    return scored[:top_k]


def _merge(groups: list[list[Hit]]) -> list[Hit]:
    best: dict[str, Hit] = {}
    for group in groups:
        for hit in group:
            current = best.get(hit.chunk_id)
            if current is None or hit.chroma_distance < current.chroma_distance:
                best[hit.chunk_id] = hit
    return sorted(best.values(), key=lambda hit: hit.chroma_distance)


def retrieve(question: str, scheme_name: str, fact_types: tuple[str, ...], settings: Settings, root: Path) -> tuple[list[Hit], bool]:
    rows = load_rows(root)
    vector = encode_query(settings.embedding_model, question, root)
    groups = [rank(rows, vector, scheme_name, fact_type, settings.top_k) for fact_type in fact_types or ("",)]
    hits = _merge(groups)
    relaxed = False
    if not hits and scheme_name:
        hits = rank(rows, vector, scheme_name, "", settings.top_k)
        relaxed = True
    if not hits:
        hits = rank(rows, vector, "", "", settings.top_k)
        relaxed = True
    return hits, relaxed and bool(hits)
