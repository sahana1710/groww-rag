import json
from pathlib import Path

import httpx

from app.ingest.scrape import run

ROOT = Path(__file__).resolve().parents[1]

HTML = """
<html><head><title>Example</title></head>
<body>
<script id="__NEXT_DATA__">{"props":{"pageProps":{"mfServerSideData":{
  "scheme_name":"Example","expense_ratio":"1.25","peerComparison":[{"expense_ratio":"8"}]
}}}}</script>
<p>Visible fact</p>
</body></html>
"""


def _prepare(tmp_path: Path, rows: int = 5) -> None:
    (tmp_path / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    folder = tmp_path / "sources"
    folder.mkdir()
    lines = ["id,url,publisher,page_type,scheme_name,why_included"]
    for index in range(rows):
        lines.append(f"src-{index},https://groww.in/help/item-{index},Groww,help,,because")
    (folder / "sources.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_scrape_writes_raw_and_strips_peers(tmp_path: Path) -> None:
    _prepare(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("item-1"):
            return httpx.Response(404, text="missing")
        return httpx.Response(200, text=HTML)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert run(tmp_path, client) == 0

    ok = json.loads((tmp_path / "data" / "raw" / "src-0" / "meta.json").read_text(encoding="utf-8"))
    assert ok["status"] == "ok"
    assert ok["fetched_at"]
    scheme = json.loads((tmp_path / "data" / "raw" / "src-0" / "next.json").read_text(encoding="utf-8"))
    assert scheme["expense_ratio"] == "1.25"
    assert "peerComparison" not in scheme
    assert "Visible fact" in (tmp_path / "data" / "raw" / "src-0" / "text.txt").read_text(encoding="utf-8")

    failed = json.loads((tmp_path / "data" / "raw" / "src-1" / "meta.json").read_text(encoding="utf-8"))
    assert failed["status"] == "failed"
    assert not (tmp_path / "data" / "raw" / "src-1" / "page.html").exists()

    pipeline = json.loads((tmp_path / "data" / "pipeline.json").read_text(encoding="utf-8"))
    assert pipeline["stages"]["scrape"]["status"] == "ok"
    assert pipeline["stages"]["load"]["status"] == "stale"
    assert not (tmp_path / "data" / "documents").exists()
