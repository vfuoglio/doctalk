"""Split text into overlapping, paragraph-aware chunks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str  # file name
    location: str  # e.g. "p. 3" or ""
    index: int  # chunk number within the source

    @property
    def id(self) -> str:
        return f"{self.source}::{self.location or 'doc'}::{self.index}"

    @property
    def label(self) -> str:
        return f"{self.source} ({self.location})" if self.location else self.source


def split_text(text: str, max_chars: int = 1000, overlap: int = 150) -> list[str]:
    """Greedy paragraph packing with character overlap between chunks.

    Paragraphs longer than max_chars are hard-split. Overlap keeps context
    that straddles a boundary retrievable from either side.
    """
    if max_chars <= overlap:
        raise ValueError("max_chars must be greater than overlap")

    pieces: list[str] = []
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        while len(para) > max_chars:
            pieces.append(para[:max_chars])
            para = para[max_chars - overlap :]
        pieces.append(para)

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + 2 + len(piece) <= max_chars:
            current += "\n\n" + piece
        else:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = (tail + "\n\n" + piece) if tail else piece
            if len(current) > max_chars:
                current = current[-max_chars:]
    if current:
        chunks.append(current)
    return chunks


def chunk_sections(
    sections: list[tuple[str, str]],
    source: str,
    max_chars: int = 1000,
    overlap: int = 150,
) -> list[Chunk]:
    out: list[Chunk] = []
    n = 0
    for location, text in sections:
        for piece in split_text(text, max_chars, overlap):
            out.append(Chunk(piece, source, location, n))
            n += 1
    return out
