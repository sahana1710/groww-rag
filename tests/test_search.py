from __future__ import annotations

from app.retrieve.search import Stored, rank


def test_rank_returns_the_matching_fact() -> None:
    rows = [
        Stored("a", (1.0, 0.0), "expense_ratio", "Scheme", "https://groww.in/a", "2026-11-01", "expense", ),
        Stored("b", (0.0, 1.0), "benchmark", "Scheme", "https://groww.in/a", "2026-11-01", "benchmark"),
    ]
    hits = rank(rows, [1.0, 0.0], "Scheme", "expense_ratio", 4)
    assert [hit.chunk_id for hit in hits] == ["a"]
    assert hits[0].chroma_distance == 0.0


def test_rank_skips_a_different_scheme() -> None:
    rows = [
        Stored("a", (1.0, 0.0), "expense_ratio", "Other", "https://groww.in/a", "2026-11-01", "expense"),
    ]
    assert rank(rows, [1.0, 0.0], "Scheme", "expense_ratio", 4) == []
