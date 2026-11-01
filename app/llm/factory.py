"""Select a provider. A missing key or a rejected model id is not swapped for another provider."""

from __future__ import annotations

from app.config import Settings
from app.llm.base import LLMClient

_PROVIDERS = ("groq", "openai", "gemini", "anthropic", "mistral")


def build(settings: Settings) -> LLMClient:
    if settings.llm_provider == "groq":
        from app.llm.groq_client import GroqClient

        return GroqClient(settings)
    if settings.llm_provider not in _PROVIDERS:
        raise RuntimeError(f"provider not implemented: {settings.llm_provider}")
    raise RuntimeError(f"{settings.llm_provider} client is not configured for this run")
