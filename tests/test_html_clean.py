import json

from app.ingest.html_clean import extract, help_article

PAGE = """
<html>
  <head><title>HDFC Large Cap Fund Direct Growth</title></head>
  <body>
    <nav>Home link</nav>
    <div class="cookie-consent">Accept cookies please</div>
    <script id="__NEXT_DATA__" type="application/json">{
      "props": {"pageProps": {"mfServerSideData": {
        "expense_ratio": "9.99",
        "exit_load": "Exit load of 1% if redeemed within 1 year",
        "peerComparison": [{"expense_ratio": "0.10"}],
        "meta_desc": "return of 50",
        "return_stats": [{"risk": "Very High", "return1y": 12}]
      }}}
    }</script>
    <p>Expense ratio shown on the page</p>
  </body>
</html>
"""


def test_extract_keeps_facts_and_drops_peers() -> None:
    title, text, scheme = extract(PAGE)
    assert title == "HDFC Large Cap Fund Direct Growth"
    assert "Accept cookies please" not in text
    assert "Home link" not in text
    assert "Expense ratio shown on the page" in text
    assert scheme is not None
    assert scheme["expense_ratio"] == "9.99"
    assert "peerComparison" not in scheme
    assert "meta_desc" not in scheme
    assert scheme["return_stats"][0]["risk"] == "Very High"
    json.dumps(scheme)


def test_help_article_keeps_the_steps_and_drops_the_footer() -> None:
    text = (
        "Customer Support\n\n"
        "You can request the statement from Reports.\n"
        "Steps to request your statement:\n"
        "Go to your profile.\n"
        "Was the answer helpful?\n"
        "Top Gainers Stocks\n"
    )
    article = help_article(text)
    assert "Go to your profile." in article
    assert "Top Gainers Stocks" not in article
