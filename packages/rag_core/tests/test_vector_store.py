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


class TestResultNormalization:
    def test_normalize_result_returns_only_the_canonical_fields(self):
        from packages.rag_core.vector_store import normalize_result

        result = normalize_result(
            {
                "chunk_id": "c1",
                "text": "  Evidence text.  ",
                "score": "0.75",
                "indicator_code": "R018",
                "extra": "must not cross the boundary",
            }
        )

        assert result == {
            "chunk_id": "c1",
            "text": "Evidence text.",
            "score": 0.75,
            "indicator_code": "R018",
            "indicator_name": None,
            "family": None,
            "page_start": None,
            "page_end": None,
        }
        assert type(result["score"]) is float

    @pytest.mark.parametrize("text", [None, "", "   "])
    def test_normalize_result_rejects_empty_text(self, text):
        from packages.rag_core.vector_store import normalize_result

        with pytest.raises(ValueError, match="text"):
            normalize_result({"text": text})

    def test_normalize_results_excludes_items_with_empty_text(self):
        from packages.rag_core.vector_store import normalize_results

        results = normalize_results(
            [
                {"chunk_id": "bad", "text": ""},
                {"chunk_id": "good", "text": "usable", "score": 1},
                {"chunk_id": "also-bad"},
            ]
        )

        assert [result["chunk_id"] for result in results] == ["good"]
        assert results[0]["score"] == 1.0


class TestFaissVectorStore:
    def test_delegates_to_hybrid_search_and_normalizes_boundary(
        self, monkeypatch, fake_chunks
    ):
        from packages.rag_core import retrievers
        from packages.rag_core.vector_store import FaissVectorStore

        captured = {}

        def fake_hybrid(query, k=10, family=None, chunks=None, **kwargs):
            captured.update(query=query, k=k, family=family)
            return [
                {**fake_chunks[0], "score": "0.8", "backend_only": True},
                {**fake_chunks[1], "text": ""},
            ][:k]

        monkeypatch.setattr(retrievers, "hybrid_search", fake_hybrid)

        store = FaissVectorStore(chunks=fake_chunks)
        out = store.search("single bidder", k=2, family_filter=["competencia"])

        assert captured == {"query": "single bidder", "k": 2, "family": "competencia"}
        assert out == [
            {
                **fake_chunks[0],
                "score": 0.8,
            }
        ]


class TestQdrantVectorStore:
    def _fake_client(
        self,
        fake_chunks,
        captured,
        *,
        exists=True,
        count=2,
        size=768,
        distance="Cosine",
        vector_name=None,
    ):
        def collection_exists(collection_name):
            captured.setdefault("events", []).append("collection_exists")
            captured["preflight_collection"] = collection_name
            return exists

        def count_points(collection_name, exact=True):
            captured.setdefault("events", []).append("count")
            return SimpleNamespace(count=count)

        def get_collection(collection_name):
            captured.setdefault("events", []).append("get_collection")
            vectors = SimpleNamespace(size=size, distance=distance)
            if vector_name is not None:
                vectors = {vector_name: vectors}
            params = SimpleNamespace(vectors=vectors)
            return SimpleNamespace(config=SimpleNamespace(params=params))

        def query_points(
            collection_name, query, limit, query_filter=None, using=None
        ):
            captured.setdefault("events", []).append("query")
            captured.update(
                collection=collection_name,
                limit=limit,
                query_filter=query_filter,
                using=using,
            )
            points = [
                SimpleNamespace(score=0.9 - 0.1 * i, payload=dict(chunk))
                for i, chunk in enumerate(fake_chunks[:limit])
            ]
            return SimpleNamespace(points=points)

        return SimpleNamespace(
            collection_exists=collection_exists,
            count=count_points,
            get_collection=get_collection,
            query_points=query_points,
        )

    def test_search_maps_payload_to_chunk_dict(self, fake_chunks):
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        store = QdrantVectorStore(
            client=self._fake_client(fake_chunks, captured),
            embed_fn=lambda texts: captured.setdefault("events", []).append("embed")
            or [[0.1] * 768 for _ in texts],
        )
        out = store.search("single bidder", k=2)

        assert captured["events"][:4] == [
            "collection_exists",
            "count",
            "get_collection",
            "embed",
        ]
        assert captured["collection"] == "standard_kb"
        assert captured["limit"] == 2
        assert captured["using"] is None
        assert out[0]["chunk_id"] == "c1"
        assert out[0]["indicator_code"] == "R018"
        assert out[0]["score"] == pytest.approx(0.9)
        # El formato debe ser el mismo dict que consume verifier/citations
        for key in ("text", "indicator_name", "page_start", "page_end"):
            assert key in out[0]
        assert set(out[0]) == {
            "chunk_id",
            "text",
            "score",
            "indicator_code",
            "indicator_name",
            "family",
            "page_start",
            "page_end",
        }

    def test_family_filter_builds_qdrant_filter(self, fake_chunks):
        pytest.importorskip("qdrant_client")
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        store = QdrantVectorStore(
            client=self._fake_client(fake_chunks, captured),
            embed_fn=lambda texts: [[0.1] * 768 for _ in texts],
        )
        store.search("q", k=1, family_filter=["competencia"])
        assert captured["query_filter"] is not None

    def test_search_selects_the_single_named_vector(self, fake_chunks):
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        store = QdrantVectorStore(
            client=self._fake_client(
                fake_chunks, captured, vector_name="gemini_embedding"
            ),
            embed_fn=lambda texts: [[0.1] * 768 for _ in texts],
        )

        store.search("q", k=1)

        assert captured["using"] == "gemini_embedding"

    @pytest.mark.parametrize("vector_name", [None, "gemini_embedding"])
    def test_search_with_real_in_memory_qdrant(self, vector_name):
        qdrant_client = pytest.importorskip("qdrant_client")
        from qdrant_client import models

        from packages.rag_core.vector_store import QdrantVectorStore

        client = qdrant_client.QdrantClient(":memory:")
        vector_params = models.VectorParams(
            size=768, distance=models.Distance.COSINE
        )
        vectors_config = (
            vector_params if vector_name is None else {vector_name: vector_params}
        )
        vector = [0.0] * 767 + [1.0]
        point_vector = vector if vector_name is None else {vector_name: vector}
        client.create_collection(
            collection_name="test_collection", vectors_config=vectors_config
        )
        client.upsert(
            collection_name="test_collection",
            points=[
                models.PointStruct(
                    id=1,
                    vector=point_vector,
                    payload={"chunk_id": "c1", "text": "usable evidence"},
                )
            ],
        )
        store = QdrantVectorStore(
            collection="test_collection",
            client=client,
            embed_fn=lambda texts: [vector for _ in texts],
        )

        results = store.search("q", k=1)

        assert results[0]["chunk_id"] == "c1"

    def test_preflight_caches_only_success(self, fake_chunks):
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        store = QdrantVectorStore(
            client=self._fake_client(fake_chunks, captured),
            embed_fn=lambda texts: [[0.1] * 768 for _ in texts],
        )

        store.preflight()
        store.preflight()
        store.search("q")

        assert captured["events"].count("collection_exists") == 1
        assert captured["events"].count("count") == 1
        assert captured["events"].count("get_collection") == 1

    @pytest.mark.parametrize(
        ("client_options", "message"),
        [
            ({"exists": False}, "no existe"),
            ({"count": 0}, "vacía"),
            ({"size": 1536}, "768"),
            ({"distance": "Dot"}, "cosine"),
        ],
    )
    def test_preflight_rejects_invalid_collection(
        self, fake_chunks, client_options, message
    ):
        from packages.rag_core.vector_store import QdrantVectorStore

        captured = {}
        embed_calls = []
        store = QdrantVectorStore(
            client=self._fake_client(fake_chunks, captured, **client_options),
            embed_fn=lambda texts: embed_calls.append(texts) or [[0.1] * 768],
        )

        with pytest.raises(RuntimeError, match=message):
            store.search("must not embed")

        assert embed_calls == []
        assert "query" not in captured.get("events", [])

    def test_preflight_sanitizes_client_failures(self):
        from packages.rag_core.vector_store import QdrantVectorStore

        secret = "super-secret-api-key"

        def fail(_collection):
            raise ConnectionError(f"request failed with api_key={secret}")

        client = SimpleNamespace(collection_exists=fail)
        store = QdrantVectorStore(
            url="https://private-cluster.example",
            api_key=secret,
            client=client,
            embed_fn=lambda texts: pytest.fail("embedding must not run"),
        )

        with pytest.raises(RuntimeError) as error:
            store.search("q")

        message = str(error.value)
        assert secret not in message
        assert "private-cluster" not in message
        assert "api_key" not in message

    def test_missing_url_raises_without_client(self, monkeypatch):
        from packages.rag_core.vector_store import QdrantVectorStore

        monkeypatch.delenv("QDRANT_URL", raising=False)
        monkeypatch.delenv("QDRANT_ENDPOINT", raising=False)
        store = QdrantVectorStore(embed_fn=lambda texts: [[0.0]])
        with pytest.raises(RuntimeError):
            store.search("q")
