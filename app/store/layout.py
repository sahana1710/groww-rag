"""Filesystem layout for raw pages, documents, chunks, embeddings, Chroma, and traces."""

from __future__ import annotations

import json
from pathlib import Path

STAGES = ("scrape", "load", "chunk", "embed", "index")


class IndexNotReady(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data"


def raw_dir(source_id: str, root: Path | None = None) -> Path:
    return data_dir(root) / "raw" / source_id


def documents_path(root: Path | None = None) -> Path:
    return data_dir(root) / "documents" / "documents.jsonl"


def chunks_path(root: Path | None = None) -> Path:
    return data_dir(root) / "chunks" / "chunks.jsonl"


def embeddings_path(root: Path | None = None) -> Path:
    return data_dir(root) / "embeddings" / "embeddings.jsonl"


def traces_dir(root: Path | None = None) -> Path:
    return data_dir(root) / "traces"


def pipeline_path(root: Path | None = None) -> Path:
    return data_dir(root) / "pipeline.json"


def empty_pipeline() -> dict:
    return {
        "embedding_model": "",
        "embedding_dim": None,
        "chunk_strategy": "",
        "collection": "",
        "stages": {stage: {"status": "missing"} for stage in STAGES},
    }


def read_pipeline(root: Path | None = None) -> dict:
    path = pipeline_path(root)
    if not path.exists():
        return empty_pipeline()
    return json.loads(path.read_text(encoding="utf-8"))


def write_pipeline(pipeline: dict, root: Path | None = None) -> None:
    path = pipeline_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pipeline, indent=2) + "\n", encoding="utf-8")


def assert_ready_for_ask(embedding_model: str, root: Path | None = None) -> None:
    pipeline = read_pipeline(root)
    for stage in STAGES:
        status = pipeline.get("stages", {}).get(stage, {}).get("status")
        if status != "ok":
            raise IndexNotReady(stage)
    if pipeline.get("embedding_model") != embedding_model:
        raise IndexNotReady("embedding_model")
