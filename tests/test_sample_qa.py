from app.sample_qa import render


def test_sample_markdown_copies_the_api_answer() -> None:
    text = render(
        [
            {
                "question": "What is the expense ratio of HDFC Large Cap Fund Direct Growth?",
                "action": "answer",
                "answer": "The expense ratio is 1.02%.\nSource: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
                "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
                "fetched_at": "2026-11-01",
                "trace_path": "data/traces/example.json",
                "inspector": {"llm_called": True},
            }
        ],
        "2026-11-01",
    )
    assert "not written by hand" in text
    assert "1.02%" in text
    assert "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth" in text
    assert "data/traces/example.json" in text
    assert "LLM called: `True`" in text
