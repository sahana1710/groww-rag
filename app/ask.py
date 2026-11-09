"""One question in, one answer out. Refusals never call the model."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.config import load_settings
from app.generate.prompt import system_prompt, user_message
from app.llm.factory import build
from app.policy.checker import check_draft
from app.policy.classify import FACT_LABELS, Decision, classify
from app.retrieve.search import Hit, retrieve
from app.store.layout import IndexNotReady, assert_ready_for_ask, chunks_path, read_pipeline, traces_dir

LOGGER = logging.getLogger(__name__)
STEP_RE = re.compile(r"^Step\s+(\d+)\.\s*(.+)$", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
OVERVIEW_SKIP = ("why invest", "sign up", "expert recommendation", "zero fees", "how to invest", "looking to invest")
TEMPLATES = {
    "pii": "pii",
    "jailbreak": "advice",
    "out_of_corpus": "out_of_corpus",
    "performance": "performance",
    "advice": "advice",
    "portfolio": "advice",
}


def _templates(root: Path) -> dict[str, str]:
    loaded = yaml.safe_load((root / "prompts" / "templates.yaml").read_text(encoding="utf-8"))
    return {key: str(value).strip() for key, value in loaded.items()}


def _pages(root: Path) -> tuple[dict[str, tuple[str, str]], tuple[str, str]]:
    schemes: dict[str, tuple[str, str]] = {}
    amc = ("", "")
    for line in chunks_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        chunk = json.loads(line)
        url = chunk.get("source_url") or ""
        fetched = chunk.get("fetched_at") or ""
        name = chunk.get("scheme_name") or ""
        if name and name not in schemes:
            schemes[name] = (url, fetched)
        if chunk.get("source_id") == "hdfc-amc" and url:
            amc = (url, fetched)
    return schemes, amc


def _invest_steps(root: Path) -> tuple[str, str, str, list[dict]]:
    found: list[tuple[int, str, dict]] = []
    url = ""
    fetched = ""
    for line in chunks_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        chunk = json.loads(line)
        if chunk.get("source_id") != "hdfc-amc":
            continue
        text = re.sub(r"\s+([.,])", r"\1", " ".join(str(chunk.get("text") or "").split()))
        match = STEP_RE.match(text)
        if not match:
            continue
        found.append((int(match.group(1)), match.group(2).strip(), chunk))
        url = chunk.get("source_url") or url
        fetched = chunk.get("fetched_at") or fetched
    found.sort(key=lambda item: item[0])
    body = "\n".join(f"Step {number}. {text}" for number, text, _chunk in found)
    final = f"{body}\nSource: {url}\nLast updated from sources: {fetched}."
    hits = [
        {
            "chunk_id": chunk.get("chunk_id") or "",
            "chroma_distance": None,
            "fact_type": "amc_overview",
            "source_url": url,
            "text": f"Step {number}. {text}",
        }
        for number, text, chunk in found
    ]
    return final, url, fetched, hits


def _is_overview(question: str) -> bool:
    text = question.lower()
    return any(phrase in text for phrase in ("about hdfc", "overview of hdfc", "hdfc amc overview", "what is hdfc mutual fund", "tell me about hdfc"))


def _overview_sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text).strip()
    flat = flat.replace("Company Ltd., or HDFC Mutual Fund, is currently", "HDFC Mutual Fund is currently")
    kept = []
    for part in SENTENCE_RE.split(flat):
        sentence = part.strip()
        if len(sentence) < 40 or any(phrase in sentence.lower() for phrase in OVERVIEW_SKIP):
            continue
        kept.append(sentence if sentence.endswith(".") else sentence + ".")
    return kept[:3]


def _fund_house_overview(root: Path) -> tuple[str, str, str, list[dict]]:
    url = ""
    fetched = ""
    sentences: list[str] = []
    hits: list[dict] = []
    for line in chunks_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        chunk = json.loads(line)
        if chunk.get("source_id") != "hdfc-amc" or "received approval to act as an AMC" not in str(chunk.get("text") or ""):
            continue
        sentences = _overview_sentences(str(chunk.get("text") or ""))
        url = chunk.get("source_url") or ""
        fetched = chunk.get("fetched_at") or ""
        hits = [
            {
                "chunk_id": chunk.get("chunk_id") or "",
                "chroma_distance": None,
                "fact_type": "amc_overview",
                "source_url": url,
                "text": " ".join(sentences),
            }
        ]
        break
    body = " ".join(sentences)
    final = f"{body}\nSource: {url}\nLast updated from sources: {fetched}."
    return final, url, fetched, hits


def _fill(template: str, url: str, fetched_at: str) -> str:
    return template.format(source_url=url, fetched_at=fetched_at).strip()


def _evidence(hits: list[Hit], fact_types: tuple[str, ...], relaxed: bool) -> list[Hit]:
    if not fact_types:
        return list(hits)
    kept = []
    for hit in hits:
        if hit.fact_type in fact_types:
            kept.append(hit)
            continue
        if relaxed and any(FACT_LABELS.get(fact_type, "").lower() in hit.text.lower() for fact_type in fact_types):
            kept.append(hit)
    return kept


def _trace(root: Path, payload: dict) -> str:
    folder = traces_dir(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{stamp}-{uuid.uuid4().hex[:4]}.json"
    body = json.dumps(payload, indent=2) + "\n"
    for candidate in (folder, Path("/tmp/traces")):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            (candidate / name).write_text(body, encoding="utf-8")
        except OSError:
            continue
        if candidate == folder:
            return f"data/traces/{name}"
        return ""
    return ""


def _response(payload: dict, trace_path: str) -> dict:
    hits = [
        {
            "chunk_id": hit["chunk_id"],
            "chroma_distance": hit["chroma_distance"],
            "fact_type": hit["fact_type"],
            "source_url": hit["source_url"],
        }
        for hit in payload["hits"]
    ]
    show_source = not payload.get("provider_error")
    return {
        "action": payload["action"],
        "answer": payload["final_text"],
        "source_url": payload["source_url"] if show_source else "",
        "fetched_at": payload["fetched_at"] if show_source else "",
        "trace_path": trace_path,
        "inspector": {
            "action": payload["action"],
            "llm_called": payload["llm_called"],
            "fact_types": payload["fact_types"],
            "filters": payload["filters"],
            "hits": hits,
        },
    }


def ask(question: str, root: Path | None = None, search=None, complete=None) -> dict:
    from app.store.layout import repo_root

    root = root or repo_root()
    settings = load_settings(root)
    pipeline = read_pipeline(root)
    assert_ready_for_ask(settings.embedding_model, root)
    if pipeline.get("embedding_dim") is None:
        raise IndexNotReady("embedding_dim")

    question = " ".join(question.split())
    if not question:
        raise ValueError("question is empty")
    if len(question) > 500:
        raise ValueError("question is too long")

    decision = classify(question, settings)
    templates = _templates(root)
    schemes, amc = _pages(root)
    page = schemes.get(decision.scheme_name) or amc
    source_url, fetched_at = page

    payload = {
        "action": decision.action if decision.action != "refuse" else "refuse",
        "refusal_reason": decision.reason if decision.action == "refuse" else None,
        "question_redacted": decision.question_redacted,
        "scheme_name": decision.scheme_name,
        "fact_types": list(decision.fact_types),
        "filters": {},
        "filter_relaxed": False,
        "top_k": settings.top_k,
        "hits": [],
        "llm_called": False,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "draft": "",
        "checker": {"passed": True, "failures": []},
        "final_text": "",
        "source_url": source_url,
        "fetched_at": fetched_at,
        "provider_error": False,
    }
    if decision.reason == "pii":
        payload["event"] = "pii_refused"

    if decision.action == "refuse":
        kind = TEMPLATES[decision.reason]
        payload["final_text"] = _fill(templates[kind], source_url, fetched_at)
        return _response(payload, _trace(root, payload))

    if decision.action == "narrow":
        payload["final_text"] = _fill(templates["narrow"], amc[0], amc[1])
        payload["source_url"], payload["fetched_at"] = amc
        return _response(payload, _trace(root, payload))

    if decision.reason == "invest_steps":
        final, url, fetched, hits = _invest_steps(root)
        payload["filters"] = {"fact_type": ["amc_overview"], "steps": True}
        payload["hits"] = hits
        payload["source_url"] = url
        payload["fetched_at"] = fetched
        payload["draft"] = final
        payload["final_text"] = final
        return _response(payload, _trace(root, payload))

    if decision.reason == "amc_overview" and _is_overview(decision.question_redacted):
        final, url, fetched, hits = _fund_house_overview(root)
        payload["filters"] = {"fact_type": ["amc_overview"], "overview": True}
        payload["hits"] = hits
        payload["source_url"] = url
        payload["fetched_at"] = fetched
        payload["draft"] = final
        payload["final_text"] = final
        return _response(payload, _trace(root, payload))

    filters = {"fact_type": list(decision.fact_types)}
    if decision.scheme_name:
        filters["scheme_name"] = decision.scheme_name
    payload["filters"] = filters
    hits, relaxed = (search or retrieve)(decision.question_redacted, decision.scheme_name, decision.fact_types, settings, root)
    payload["filter_relaxed"] = relaxed
    payload["hits"] = [hit.__dict__ if isinstance(hit, Hit) else hit for hit in hits]
    evidence = _evidence(hits, decision.fact_types, relaxed)
    if not evidence:
        url, fetched = (schemes.get(decision.scheme_name) or amc)
        payload["action"] = "insufficient_evidence"
        payload["source_url"], payload["fetched_at"] = url, fetched
        payload["final_text"] = _fill(templates["insufficient_evidence"], url, fetched)
        return _response(payload, _trace(root, payload))

    cited_url = evidence[0].source_url
    cited_date = evidence[0].fetched_at
    passages: dict[str, str] = {}
    for hit in evidence:
        passages[hit.source_url] = passages.get(hit.source_url, "") + "\n" + hit.text
    payload["source_url"] = cited_url
    payload["fetched_at"] = cited_date
    try:
        reply = (complete or build(settings).complete)(
            system_prompt(root),
            user_message(decision.question_redacted, decision.action, evidence, relaxed),
        )
        payload["llm_called"] = True
        payload["draft"] = reply
    except Exception as exc:
        payload["llm_called"] = True
        payload["provider_error"] = True
        payload["final_text"] = templates["provider_error"]
        secret = settings.llm_api_key
        message = str(exc)
        if secret:
            message = message.replace(secret, "[redacted]")
        LOGGER.warning("provider error: %s", message)
        return _response(payload, _trace(root, payload))

    allowed = {cited_url, *(url for url, _fetched in schemes.values()), amc[0]}
    result = check_draft(
        reply,
        action=decision.action,
        allowed_urls=allowed,
        passages=passages,
        fetched_at=cited_date,
        settings=settings,
    )
    payload["checker"] = {"passed": result.passed, "failures": list(result.failures)}
    if result.passed:
        payload["final_text"] = result.text
    else:
        payload["action"] = "insufficient_evidence"
        payload["final_text"] = _fill(templates["insufficient_evidence"], cited_url, cited_date)
    return _response(payload, _trace(root, payload))
