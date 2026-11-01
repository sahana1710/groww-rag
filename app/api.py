"""Local page. One question in, one answer out."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.ask import ask
from app.config import load_settings
from app.store.layout import IndexNotReady, assert_ready_for_ask, repo_root


def _warm_encoder() -> None:
    if "pytest" in sys.modules:
        return
    from app.retrieve.search import _model

    _model(load_settings().embedding_model)


app = FastAPI(title="Groww mutual fund facts assistant", on_startup=[_warm_encoder])


class AskBody(BaseModel):
    question: str = ""


def _index_file() -> Path:
    return repo_root() / "web" / "index.html"


@app.get("/")
def home() -> FileResponse:
    return FileResponse(_index_file())


@app.get("/api/health")
def health() -> JSONResponse:
    settings = load_settings()
    try:
        assert_ready_for_ask(settings.embedding_model)
    except IndexNotReady as exc:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "index_not_ready", "stage": exc.reason},
        )
    return JSONResponse(content={"ready": True})


@app.post("/api/ask")
def ask_route(body: AskBody) -> JSONResponse:
    question = " ".join(body.question.split())
    if not question:
        return JSONResponse(status_code=400, content={"reason": "empty_question"})
    if len(question) > 500:
        return JSONResponse(status_code=400, content={"reason": "question_too_long"})
    try:
        result = ask(question)
    except IndexNotReady as exc:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "index_not_ready", "stage": exc.reason},
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"reason": str(exc)})
    return JSONResponse(content=result)
