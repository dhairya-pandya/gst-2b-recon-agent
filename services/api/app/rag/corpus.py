"""Legal corpus retrieval. Hash embedder for tests and CI; Vertex embeddings in production."""

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

CORPUS_PATH = Path(__file__).resolve().parents[4] / "corpus" / "chunks.json"
DIM = 256


@dataclass(frozen=True)
class Chunk:
    citation: str
    source: str
    body: str


@dataclass(frozen=True)
class Hit:
    citation: str
    body: str
    score: float


class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    """Bag-of-words hashing into a fixed-size unit vector. Deterministic, no network."""

    async def embed(self, text: str) -> list[float]:
        vec = [0.0] * DIM
        for word in re.findall(r"[a-z0-9()]+", text.lower()):
            vec[hash(word) % DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def load_chunks(path: Path = CORPUS_PATH) -> list[Chunk]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Chunk(citation=r["citation"], source=r["source"], body=r["body"]) for r in raw]


class Corpus:
    def __init__(self, chunks: list[Chunk], embedder: Embedder) -> None:
        self._chunks = chunks
        self._embedder = embedder
        self._names = {c.citation for c in chunks}
        self._vectors: list[list[float]] | None = None

    def citation_exists(self, citation: str) -> bool:
        return citation in self._names

    async def _index(self) -> list[list[float]]:
        if self._vectors is None:
            self._vectors = [await self._embedder.embed(c.body) for c in self._chunks]
        return self._vectors

    async def retrieve(self, query: str, k: int = 5) -> list[Hit]:
        q = await self._embedder.embed(query)
        vectors = await self._index()
        scored = [
            Hit(
                citation=c.citation,
                body=c.body,
                score=sum(a * b for a, b in zip(q, v, strict=True)),
            )
            for c, v in zip(self._chunks, vectors, strict=True)
        ]
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]
