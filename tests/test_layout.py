import json
from pathlib import Path

import pytest

from app.store.layout import IndexNotReady, STAGES, assert_ready_for_ask, read_pipeline, write_pipeline


def test_missing_pipeline_is_not_ready(tmp_path: Path) -> None:
    pipeline = read_pipeline(tmp_path)
    assert set(pipeline["stages"]) == set(STAGES)
    with pytest.raises(IndexNotReady) as exc:
        assert_ready_for_ask("sentence-transformers/all-MiniLM-L6-v2", tmp_path)
    assert exc.value.reason == "scrape"


def test_ready_when_every_stage_matches_the_model(tmp_path: Path) -> None:
    pipeline = read_pipeline(tmp_path)
    pipeline["embedding_model"] = "sentence-transformers/all-MiniLM-L6-v2"
    for stage in STAGES:
        pipeline["stages"][stage] = {"status": "ok"}
    write_pipeline(pipeline, tmp_path)
    assert_ready_for_ask("sentence-transformers/all-MiniLM-L6-v2", tmp_path)
    saved = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert saved["stages"]["index"]["status"] == "ok"


def test_model_mismatch_is_not_ready(tmp_path: Path) -> None:
    pipeline = read_pipeline(tmp_path)
    pipeline["embedding_model"] = "other-model"
    for stage in STAGES:
        pipeline["stages"][stage] = {"status": "ok"}
    write_pipeline(pipeline, tmp_path)
    with pytest.raises(IndexNotReady) as exc:
        assert_ready_for_ask("sentence-transformers/all-MiniLM-L6-v2", tmp_path)
    assert exc.value.reason == "embedding_model"
