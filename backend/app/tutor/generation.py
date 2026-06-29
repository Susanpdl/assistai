"""Generation seam: turn a question + retrieved passages into a grounded answer.

The orchestrator depends only on the `Generator` interface, so the model is swappable:

- `LocalGenerator` — deterministic, offline, extractive. Stitches the answer from the
  retrieved passages with no API call. Default for dev/tests: free and reproducible.
- `ClaudeGenerator` — calls the Anthropic API (Claude Sonnet by default) with the tutor
  guardrail system prompt. Used when GENERATION_BACKEND=claude and an API key is set.
"""

from __future__ import annotations

import textwrap
from typing import Protocol

from app.config import settings
from app.tutor.guardrails import TUTOR_SYSTEM_PROMPT
from app.tutor.retrieval import Retrieved


class Generator(Protocol):
    def answer(self, question: str, passages: list[Retrieved]) -> str:
        ...


def _format_context(passages: list[Retrieved]) -> str:
    blocks = []
    for i, p in enumerate(passages, 1):
        blocks.append(f"[{i}] (source: {p.citation})\n{p.text}")
    return "\n\n".join(blocks)


class LocalGenerator:
    """Extractive, offline answer composed from the top passages. No model, no cost."""

    def answer(self, question: str, passages: list[Retrieved]) -> str:
        if not passages:
            return "I couldn't find anything in the course materials about that."
        top = passages[0]
        excerpt = textwrap.shorten(top.text, width=500, placeholder=" …")
        return (
            "Here's what your course material says about that:\n\n"
            f"{excerpt}\n\n"
            "(Want me to go deeper or give a worked example? Just ask.)"
        )


class ClaudeGenerator:
    """Grounded generation via the Anthropic API (Claude Sonnet by default)."""

    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise ValueError("GENERATION_BACKEND=claude requires ANTHROPIC_API_KEY")
        # Imported lazily so the dependency is only needed when this backend is used.
        from anthropic import Anthropic

        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def answer(self, question: str, passages: list[Retrieved]) -> str:
        context = _format_context(passages) if passages else "(no relevant course material found)"
        user_content = (
            f"Course material context:\n\n{context}\n\n"
            f"Student question: {question}\n\n"
            "Answer using only the context above, following your tutor rules."
        )
        resp = self._client.messages.create(
            model=settings.tutor_model,
            max_tokens=settings.tutor_max_tokens,
            system=TUTOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        # Concatenate any text blocks in the response.
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


def get_generator() -> Generator:
    if settings.generation_backend == "local":
        return LocalGenerator()
    if settings.generation_backend == "claude":
        return ClaudeGenerator()
    raise ValueError(f"Unknown generation backend: {settings.generation_backend}")
