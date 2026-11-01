"""Groq chat completions. Thinking text is dropped; the visible reply is returned."""

from __future__ import annotations

from app.config import Settings


def _ipv4_client():
    """Groq's addresses include IPv6, and this machine waits several seconds before falling back."""
    import httpx

    return httpx.Client(
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
        timeout=httpx.Timeout(30.0, connect=5.0),
    )


class GroqClient:
    def __init__(self, settings: Settings) -> None:
        from groq import Groq

        if not settings.llm_api_key:
            raise RuntimeError("GROQ_API_KEY is empty")
        self._http = _ipv4_client()
        self._client = Groq(api_key=settings.llm_api_key, http_client=self._http)
        self._settings = settings

    def complete(self, system: str, user: str) -> str:
        kwargs = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._settings.temperature,
            "max_tokens": 256,
        }
        if self._settings.reasoning_effort:
            kwargs["reasoning_effort"] = self._settings.reasoning_effort
        try:
            response = self._client.chat.completions.create(**kwargs)
        except TypeError:
            kwargs.pop("reasoning_effort", None)
            response = self._client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        return (getattr(message, "content", None) or "").strip()
