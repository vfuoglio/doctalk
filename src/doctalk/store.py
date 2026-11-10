"""Vector store wrapper around ChromaDB (local, persistent)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb

from .chunking import Chunk, chunk_sections
from .loaders import find_files, load_file

COLLECTION = "doctalk"


@dataclass(frozen=True)
class Hit:
    text: str
    source: str
    location: str
    distance: float

    @property
    def label(self) -> str:
        return f"{self.source} ({self.location})" if self.location else self.source


class Store:
    def __init__(self, path: str | Path = ".chroma"):
        self._client = chromadb.PersistentClient(path=str(path))
        # Chroma's default embedding function (all-MiniLM-L6-v2, runs locally).
        self._col = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        self._col.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{"source": c.source, "location": c.location} for c in chunks],
        )

    def ingest(self, root: str | Path) -> dict[str, int]:
        """Index every supported file under root. Re-ingesting replaces a file's chunks."""
        counts: dict[str, int] = {}
        for file in find_files(Path(root)):
            self.delete_source(file.name)
            chunks = chunk_sections(load_file(file), source=file.name)
            self.add_chunks(chunks)
            counts[file.name] = len(chunks)
        return counts

    def delete_source(self, source: str) -> None:
        self._col.delete(where={"source": source})

    def sources(self) -> list[str]:
        metas = self._col.get(include=["metadatas"])["metadatas"] or []
        return sorted({m["source"] for m in metas})

    def count(self) -> int:
        return self._col.count()

    def search(self, query: str, k: int = 5) -> list[Hit]:
        if self.count() == 0:
            return []
        res = self._col.query(query_texts=[query], n_results=min(k, self.count()))
        return [
            Hit(doc, meta["source"], meta["location"], dist)
            for doc, meta, dist in zip(
                res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]
