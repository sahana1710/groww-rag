from pathlib import Path

import pytest

from app.config import load_settings
from app.ingest.sources import host_allowed, load_sources

ROOT = Path(__file__).resolve().parents[1]


def _settings(tmp_path: Path):
    (tmp_path / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    return load_settings(tmp_path)


def _write_csv(tmp_path: Path, rows: list[tuple[str, str, str]]) -> None:
    folder = tmp_path / "sources"
    folder.mkdir()
    lines = ["id,url,publisher,page_type,scheme_name,why_included"]
    for source_id, url, page_type in rows:
        lines.append(f"{source_id},{url},Groww,{page_type},,because")
    (folder / "sources.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _five(host_path: str = "https://groww.in/mutual-funds/example") -> list[tuple[str, str, str]]:
    return [(f"src-{index}", f"{host_path}-{index}", "scheme") for index in range(5)]


def test_blog_url_is_rejected(tmp_path: Path) -> None:
    rows = _five()
    rows[0] = ("blog", "https://groww.in/blog/how-to-pick-a-fund", "help")
    _write_csv(tmp_path, rows)
    with pytest.raises(SystemExit, match="not an allowed URL"):
        load_sources(tmp_path, _settings(tmp_path))


def test_count_other_than_five_is_rejected(tmp_path: Path) -> None:
    _write_csv(tmp_path, _five()[:4])
    with pytest.raises(SystemExit, match="4 rows"):
        load_sources(tmp_path, _settings(tmp_path))


def test_real_source_list_is_the_five_pages() -> None:
    sources = load_sources(ROOT, load_settings(ROOT))
    assert [source.source_id for source in sources] == [
        "hdfc-amc",
        "hdfc-large-cap",
        "hdfc-flexi-cap",
        "hdfc-elss",
        "hdfc-mid-cap",
        "groww-help-capital-gains",
    ]
    scheme_urls = [source.url for source in sources if source.page_type != "help"]
    assert all(url.startswith("https://groww.in/mutual-funds/") for url in scheme_urls)
    help_pages = [source for source in sources if source.page_type == "help"]
    assert len(help_pages) == 1
    assert "where-can-i-get-the-tax-proof-for-section-80c" in help_pages[0].url
    assert not any("hdfcfund.com" in source.url for source in sources)


def test_www_subdomain_is_allowed(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    assert host_allowed("https://www.amfiindia.com/investor", settings)
    assert host_allowed("https://investor.sebi.gov.in/understanding_mf.html", settings)
    assert not host_allowed("https://example.com/fund", settings)
