import asyncio

from app.rag.corpus import Corpus, HashEmbedder, load_chunks

CHUNKS = load_chunks()


def test_chunker_assigns_citations() -> None:
    citations = {c.citation for c in CHUNKS}
    assert "CGST Act s.17(5)(b)" in citations
    assert "CGST Rules 36(4)" in citations


def test_citation_exists_true_false() -> None:
    corpus = Corpus(CHUNKS, HashEmbedder())
    assert corpus.citation_exists("CGST Act s.17(5)(b)") is True
    assert corpus.citation_exists("CGST Act s.99") is False


def test_retrieve_returns_relevant_first() -> None:
    corpus = Corpus(CHUNKS, HashEmbedder())
    hits = asyncio.run(corpus.retrieve("blocked personal consumption credit", k=2))
    assert hits[0].citation == "CGST Act s.17(5)(b)"
