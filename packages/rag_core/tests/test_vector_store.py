"""GATE F18 — VectorStore: interfaz + Faiss (wrapper) + Qdrant (inyectable).

Deterministas, sin red: el cliente Qdrant y el embed_fn se inyectan como
fakes; el camino Faiss se monkeypatchea sobre hybrid_search.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture
def fake_chunks():
    return [
        {
            "chunk_id": "c1",
            "text": "Single bid received for the tender.",
            "indicator_code": "R018",
            "indicator_name": "Single bid received",
            "family": "competencia",
            "page_start": 41,
            "page_end": 41,
        },
        {
            "chunk_id": "c2",
            "text": "Short bidding period before submission deadline.",
            "indicator_code": "R010",
            "indicator_name": "Bidding period too short",
            "family": "planeacion",
            "page_start": 10,
            "page_end": 12,
        },
    ]


class TestFactory:
    def test_make_faiss_default(self):
        from packages.rag_core.vector_store import FaissVectorStore, make_vector_store

        assert isinstance(make_vector_store(), FaissVectorStore)
        assert isinstance(make_vector_store("faiss"), FaissVectorStore)

    def test_make_qdrant(self):
        from packages.rag_core.vector_store import QdrantVectorStore, make_vector_store

        store = make_vector_store("qdrant", url="http://x", api_key="k")
        assert isinstance(store, QdrantVectorStore)

    def test_unknown_kind_raises(self):
        from packages.rag_core.vector_store import make_vector_store

        with pytest.raises(ValueError):
            make_vector_store("pinecone")


class TestFaissVectorStore:
    def test_delegates_to_hybrid_search(self, monkeypatch, fake_chunks):
        from packages.rag_core import retrievers
        from packages.rag_core.vector_store import FaissVectorStore

        captured = {}

        def fake_hybrid(query, k=10, family=None, chunks=None, **kwargs):
            captured.update(query=query, k=k, family=family)
            return fake_chunks[:k]

        monkeypatch.setattr(retrievers, "hybrid_search", fake_hybrid)

        store = FaissVectorStore(chunks=fake_chunks)
        out = store.search("single bidder", k=2, family_filter=["competencia"])

        assert captured == {"query": "single bidder", "k": 2, "family": "competencia"}
        assert out[0]["chunk_id"] == "c1"


class TestQdrantVectorStore:
    def _fake_client(self, fake_chunks, captured):
        def query_points(collection_name, query, limit, query_filter=None):
            captured.update(
                collection=collection_name, limit=limit, query_filter=query_filter
            )
            points = [
                SimpleNamespace(score=0.9 - 0.1 * i, payload=dict(chunk))
                for i, chunk in enumerate(fake_chunks[:limit])
            ]
            return SimpleNamespace(points=points)

        return SimpleNamespace(query_points=query_points)

    def test_search_maps_payload_to_chunk_dict(self, fake_chunks):
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        store = QdrantVectorStore(
            client=self._fake_client(fake_chunks, captured),
            embed_fn=lambda texts: [[0.1] * 4 for _ in texts],
        )
        out = store.search("single bidder", k=2)

        assert captured["collection"] == "standard_kb"
        assert captured["limit"] == 2
        assert out[0]["chunk_id"] == "c1"
        assert out[0]["indicator_code"] == "R018"
        assert out[0]["score"] == pytest.approx(0.9)
        # El formato debe ser el mismo dict que consume verifier/citations
        for key in ("text", "indicator_name", "page_start", "page_end"):
            assert key in out[0]

    def test_family_filter_builds_qdrant_filter(self, fake_chunks):
        pytest.importorskip("qdrant_client")
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        store = QdrantVectorStore(
            client=self._fake_client(fake_chunks, captured),
            embed_fn=lambda texts: [[0.1] * 4 for _ in texts],
        )
        store.search("q", k=1, family_filter=["competencia"])
        assert captured["query_filter"] is not None

    def test_missing_url_raises_without_client(self, monkeypatch):
        from packages.rag_core.vector_store import QdrantVectorStore

        monkeypatch.delenv("QDRANT_URL", raising=False)
        monkeypatch.delenv("QDRANT_ENDPOINT", raising=False)
        store = QdrantVectorStore(embed_fn=lambda texts: [[0.0]])
        with pytest.raises(RuntimeError):
            store.search("q")
