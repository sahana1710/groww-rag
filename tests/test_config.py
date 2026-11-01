from pathlib import Path

import pytest
import yaml

from app.config import load_settings


def _write_config(root: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "config.yaml"
    (root / "config.yaml").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def test_env_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_config(tmp_path)
    monkeypatch.setenv("EMBEDDING_MODEL", "test-model")
    monkeypatch.setenv("TOP_K", "9")
    settings = load_settings(tmp_path)
    assert settings.embedding_model == "test-model"
    assert settings.top_k == 9
    assert settings.llm_model == "qwen/qwen3.8-27b"


def test_api_key_is_hidden_and_read_from_groq_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_config(tmp_path)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "super-secret-key")
    settings = load_settings(tmp_path)
    assert settings.llm_api_key == "super-secret-key"
    assert "super-secret-key" not in repr(settings)


def test_schemes_and_allow_list(tmp_path: Path) -> None:
    _write_config(tmp_path)
    settings = load_settings(tmp_path)
    names = {scheme.scheme_name for scheme in settings.schemes}
    assert "HDFC Flexi Cap Direct Plan Growth" in names
    flexi = next(scheme for scheme in settings.schemes if scheme.source_id == "hdfc-flexi-cap")
    assert "hdfc equity fund" in flexi.aliases
    assert "hdfcfund.com" in settings.citation_domains
    assert "groww.in/blog" in settings.blocked_path_prefixes


def test_dotenv_does_not_override_existing_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_config(tmp_path)
    (tmp_path / ".env").write_text("LLM_MODEL=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv("LLM_MODEL", "from-process")
    settings = load_settings(tmp_path)
    assert settings.llm_model == "from-process"


def test_config_yaml_is_a_mapping() -> None:
    root = Path(__file__).resolve().parents[1]
    loaded = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    assert loaded["chunk_strategy"] == "scheme_fact_blocks"
    assert len(loaded["schemes"]) == 4
