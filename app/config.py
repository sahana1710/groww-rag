"""Load config.yaml and overlay .env into one frozen Settings object."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.store.layout import repo_root

_ENV_OVERLAY: dict[str, tuple[str, type]] = {
    "EMBEDDING_MODEL": ("embedding_model", str),
    "EMBEDDING_BATCH_SIZE": ("embedding_batch_size", int),
    "CHROMA_PATH": ("chroma_path", str),
    "CHROMA_COLLECTION": ("chroma_collection", str),
    "CHROMA_SPACE": ("chroma_space", str),
    "CHUNK_STRATEGY": ("chunk_strategy", str),
    "CHUNK_MAX_CHARS": ("chunk_max_chars", int),
    "CHUNK_OVERLAP_CHARS": ("chunk_overlap_chars", int),
    "TOP_K": ("top_k", int),
    "LLM_PROVIDER": ("llm_provider", str),
    "LLM_MODEL": ("llm_model", str),
    "LLM_TEMPERATURE": ("temperature", float),
    "LLM_REASONING_EFFORT": ("reasoning_effort", str),
}


@dataclass(frozen=True)
class Scheme:
    scheme_name: str
    source_id: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class Settings:
    embedding_model: str
    embedding_batch_size: int
    chroma_path: str
    chroma_collection: str
    chroma_space: str
    chunk_strategy: str
    chunk_max_chars: int
    chunk_overlap_chars: int
    top_k: int
    temperature: float
    reasoning_effort: str
    llm_provider: str
    llm_model: str
    citation_domains: tuple[str, ...]
    blocked_path_prefixes: tuple[str, ...]
    schemes: tuple[Scheme, ...]
    llm_api_key: str = field(repr=False, default="")

    def scheme_by_source_id(self, source_id: str) -> Scheme | None:
        for scheme in self.schemes:
            if scheme.source_id == source_id:
                return scheme
        return None


def load_settings(root: Path | None = None) -> Settings:
    root = root or repo_root()
    loaded = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("config.yaml must be a mapping")

    load_dotenv(root / ".env", override=False)
    for env_name, (key, caster) in _ENV_OVERLAY.items():
        raw = os.environ.get(env_name)
        if raw:
            loaded[key] = caster(raw)

    provider = str(loaded.get("llm_provider", "groq"))
    api_key = os.environ.get("LLM_API_KEY", "")
    if provider == "groq" and not api_key:
        api_key = os.environ.get("GROQ_API_KEY", "")

    schemes = tuple(
        Scheme(
            scheme_name=item["scheme_name"],
            source_id=item["source_id"],
            aliases=tuple(item.get("aliases", ())),
        )
        for item in loaded.get("schemes", ())
    )
    return Settings(
        embedding_model=str(loaded["embedding_model"]),
        embedding_batch_size=int(loaded["embedding_batch_size"]),
        chroma_path=str(loaded["chroma_path"]),
        chroma_collection=str(loaded["chroma_collection"]),
        chroma_space=str(loaded.get("chroma_space", "cosine")),
        chunk_strategy=str(loaded["chunk_strategy"]),
        chunk_max_chars=int(loaded["chunk_max_chars"]),
        chunk_overlap_chars=int(loaded["chunk_overlap_chars"]),
        top_k=int(loaded["top_k"]),
        temperature=float(loaded["temperature"]),
        reasoning_effort=str(loaded["reasoning_effort"]),
        llm_provider=provider,
        llm_model=str(loaded["llm_model"]),
        citation_domains=tuple(loaded.get("citation_domains", ())),
        blocked_path_prefixes=tuple(loaded.get("blocked_path_prefixes", ())),
        schemes=schemes,
        llm_api_key=api_key,
    )
