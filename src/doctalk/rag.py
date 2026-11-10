"""Retrieval-augmented answering with numbered citations."""
from __future__ import annotations

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass

import anthropic

from .store import Hit, Store

MODEL = os.environ.get("DOCTALK_MODEL", "claude-opus-5-5")

SYSTEM = """You answer questions using ONLY the numbered source excerpts provided.

Rules:
- Cite every claim with the number of the excerpt that supports it, like [1] or [2][3].
- If the excerpts do not contain the answer, say you could not find it in the documents. \
Do not use outside knowledge.
- Be concise. Quote sparingly."""


def build_context(hits: list[Hit]) -> str:
    return "\n\n".join(f"[{i}] ({h.label})\n{h.text}" for i, h in enumerate(hits, 1))


def cited_numbers(answer: str, n_sources: int) -> list[int]:
    """Citation numbers actually used in the answer, validated against sources."""
    found = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
    return sorted(n for n in found if 1 <= n <= n_sources)


@dataclass
class Answer:
    text: str
    hits: list[Hit]

    @property
    def cited(self) -> list[int]:
        return cited_numbers(self.text, len(self.hits))


def stream_answer(
    question: str,
    store: Store,
    k: int = 5,
    history: list[dict] | None = None,
    client: anthropic.Anthropic | None = None,
) -> tuple[list[Hit], Iterator[str]]:
    """Retrieve context, then return (hits, token-stream of the answer)."""
    client = client or anthropic.Anthropic()
    hits = store.search(question, k=k)
    user = f"Sources:\n\n{build_context(hits)}\n\nQuestion: {question}"
    messages = (history or []) + [{"role": "user", "content": user}]

    def tokens() -> Iterator[str]:
        with client.messages.stream(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM,
            output_config={"effort": "low"},
            messages=messages,
        ) as stream:
            yield from stream.text_stream

    return hits, tokens()


def answer(question: str, store: Store, k: int = 5, **kw) -> Answer:
    hits, tokens = stream_answer(question, store, k, **kw)
    return Answer("".join(tokens), hits)
