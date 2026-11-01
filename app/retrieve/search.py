"""Query the local Chroma collection with the same MiniLM model used at ingest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.ingest.embed import encode_texts
from app.store.layout import IndexNotReady

_MODELS: dict[str, object] = {}


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    chroma_distance: float
    fact_type: str
    scheme_name: str
    source_url: str
    fetched_at: str
    text: str


def _model(name: str):
    if name not in _MODELS:
        from sentence_transformers import SentenceTransformer

        _MODELS[name] = SentenceTransformer(name)
    return _MODELS[name]


def _where(scheme_name: str, fact_type: str) -> dict | None:
    filters = []
    if scheme_name:
        filters.append({"scheme_name": scheme_name})
    if fact_type:
        filters.append({"fact_type": fact_type})
    if not filters:
        return None
    if len(filters) == 1:
        return filters[0]
    return {"$and": filters}


def _query(collection, vector: list[float], top_k: int, where: dict | None) -> list[Hit]:
    result = collection.query(query_embeddings=[vector], n_results=top_k, where=where, include=["documents", "metadatas", "distances"])
    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    hits = []
    for chunk_id, doc, meta, distance in zip(ids, docs, metas, distances):
        meta = meta or {}
        hits.append(
            Hit(
                chunk_id=chunk_id,
                chroma_distance=float(distance),
                fact_type=str(meta.get("fact_type") or ""),
                scheme_name=str(meta.get("scheme_name") or ""),
                source_url=str(meta.get("source_url") or ""),
                fetched_at=str(meta.get("fetched_at") or ""),
                text=doc or "",
            )
        )
    return hits


def retrieve(question: str, scheme_name: str, fact_types: tuple[str, ...], settings: Settings, root: Path) -> tuple[list[Hit], bool]:
    import chromadb

    from app.ingest.index import _chroma_dir

    client = chromadb.PersistentClient(path=str(_chroma_dir(root, settings)))
    try:
        collection = client.get_collection(settings.chroma_collection)
    except Exception as exc:
        raise IndexNotReady("index") from exc
    stored = collection.metadata or {}
    if stored.get("embedding_model") != settings.embedding_model:
        raise IndexNotReady("embedding_model")

    vector = encode_texts(_model(settings.embedding_model), [question], settings.embedding_batch_size)[0]
    groups = []
    for fact_type in fact_types or ("",):
        groups.append(_query(collection, vector, settings.top_k, _where(scheme_name, fact_type)))
    hits = _merge(groups)
    relaxed = False
    if not hits and scheme_name:
        hits = _query(collection, vector, settings.top_k, _where(scheme_name, ""))
        relaxed = True
    if not hits:
        hits = _query(collection, vector, settings.top_k, None)
        relaxed = True
    return hits, relaxed and bool(hits)


def _merge(groups: list[list[Hit]]) -> list[Hit]:
    best: dict[str, Hit] = {}
    for group in groups:
        for hit in group:
            current = best.get(hit.chunk_id)
            if current is None or hit.chroma_distance < current.chroma_distance:
                best[hit.chunk_id] = hit
    return sorted(best.values(), key=lambda hit: hit.chroma_distance)
