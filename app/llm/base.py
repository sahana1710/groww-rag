"""Shared generator interface."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return the visible reply text."""
