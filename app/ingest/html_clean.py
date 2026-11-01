"""Turn a fetched page into visible text and, when present, the scheme object."""

from __future__ import annotations

import json

from bs4 import BeautifulSoup

# Other funds, old series, and return copy. return_stats stays so load can read the risk label.
DROP_KEYS = (
    "peerComparison",
    "historic_fund_expense",
    "sip_return",
    "simple_return",
    "meta_desc",
    "nfo_risk",
    "historic_exit_loads",
)


def _collapse(text: str) -> str:
    collapsed: list[str] = []
    blank = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if not blank and collapsed:
                collapsed.append("")
            blank = True
            continue
        collapsed.append(line)
        blank = False
    body = "\n".join(collapsed).strip()
    return f"{body}\n" if body else ""


def help_article(text: str) -> str:
    """Keep the help answer and drop the site chrome around it."""
    step_at = text.lower().find("steps to")
    if step_at == -1:
        return text
    end = text.find("Was the answer helpful?", step_at)
    if end == -1:
        end = len(text)
    start = text.rfind("\n\n", 0, step_at)
    start = 0 if start == -1 else start
    body = text[start:end].strip()
    return f"{body}\n" if body else text


def extract(html: str) -> tuple[str, str, dict | None]:
    """Return title, visible text, and the scheme object with disallowed keys removed."""
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    scheme: dict | None = None
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            payload = None
        candidate = {}
        if isinstance(payload, dict):
            candidate = (
                payload.get("props", {}).get("pageProps", {}).get("mfServerSideData")
            )
        if isinstance(candidate, dict):
            for key in DROP_KEYS:
                candidate.pop(key, None)
            scheme = candidate

    for tag in soup.find_all(["script", "style", "nav", "footer"]):
        tag.decompose()
    cookie_tags = []
    for tag in soup.find_all(True):
        classes = tag.get("class") or []
        if isinstance(classes, str):
            classes = [classes]
        ident = f"{tag.get('id') or ''} {' '.join(classes)}"
        if "cookie" in ident.lower():
            cookie_tags.append(tag)
    for tag in cookie_tags:
        tag.decompose()

    return title, _collapse(soup.get_text("\n")), scheme
