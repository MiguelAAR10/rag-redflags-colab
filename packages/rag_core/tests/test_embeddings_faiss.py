"""
GATE de aceptación de la Fase 3 (embeddings + FAISS).

Valida:
- embed_texts devuelve (n, dim) con vectores normalizados.
- build_index + search round-trip.
- mapeo chunk_id ↔ faiss_id correcto.
- persistencia (save/load) de índice y mapping.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[3]
EMB_PATH = REPO_ROOT / "packages" / "rag_core" / "embeddings.py"
IDX_PATH = REPO_ROOT / "packages" / "rag_core" / "indexing.py"

# --------------------------------------------------------------------------- #
# Fixtures deterministas (siempre corren, sin GPU ni modelo)
# --------------------------------------------------------------------------- #

@pytest.fixture
def dummy_vectors():
    """Vectores dummy normalizados para tests unitarios."""
    np.random.seed(42)
    vecs = np.random.randn(20, 384).astype(np.float32)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs


@pytest.fixture
def dummy_chunks():
    """Chunks dummy con chunk_id."""
    return [{"chunk_id": f"chunk_{i:03d}", "text": f"texto {i}"} for i in range(20)]


@pytest.fixture
def dummy_mapping():
    """Mapping dummy faiss_id → chunk_id."""
    return {i: f"chunk_{i:03d}" for i in range(20)}


# --------------------------------------------------------------------------- #
# Tests unitarios deterministas (SIEMPRE corren)
# --------------------------------------------------------------------------- #

class TestIndexingUnit:
    """Tests de lógica de índice con datos dummy (sin modelo)."""

    def test_build_index_flat(self, dummy_vectors):
        from packages.rag_core.indexing import build_index

        index = build_index(dummy_vectors, use_hnsw=False)
        assert index.ntotal == 20
        # No debe tener vectores adicionales
        assert index.ntotal == dummy_vectors.shape[0]

    def test_build_index_hnsw(self, dummy_vectors):
        from packages.rag_core.indexing import build_index

        index = build_index(dummy_vectors, use_hnsw=True)
        assert index.ntotal == 20

    def test_search_returns_top_k(self, dummy_vectors):
        from packages.rag_core.indexing import build_index, search

        index = build_index(dummy_vectors)
        q = np.random.randn(384).astype(np.float32)
        q = q / np.linalg.norm(q)

        scores, ids = search(index, q, k=5)
        assert scores.shape == (1, 5)
        assert ids.shape == (1, 5)
        # Scores deben ser descendientes (IP: mayor = más similar)
        assert all(scores[0][i] >= scores[0][i + 1] for i in range(4))

    def test_search_first_result_is_self(self, dummy_vectors):
        """Buscar con un vector del índice debe devolverlo como top-1."""
        from packages.rag_core.indexing import build_index, search

        index = build_index(dummy_vectors)
        q = dummy_vectors[3]  # vector 3 como query
        scores, ids = search(index, q, k=3)
        # El top-1 debería ser el propio vector (score≈1 por IP con normalizado)
        assert ids[0][0] == 3
        assert scores[0][0] > 0.99

    def test_save_load_index_roundtrip(self, dummy_vectors):
        from packages.rag_core.indexing import build_index, save_index, load_index, search

        index = build_index(dummy_vectors)
        q = np.random.randn(384).astype(np.float32)
        q = q / np.linalg.norm(q)

        with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as f:
            tmp_path = Path(f.name)

        try:
            save_index(index, tmp_path)
            assert tmp_path.exists()

            index2 = load_index(tmp_path)
            assert index2.ntotal == 20

            scores1, ids1 = search(index, q, k=5)
            scores2, ids2 = search(index2, q, k=5)
            assert np.allclose(scores1, scores2)
            assert np.all(ids1 == ids2)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_mapping_roundtrip(self, dummy_mapping):
        from packages.rag_core.indexing import save_mapping, load_mapping

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)

        try:
            save_mapping(dummy_mapping, tmp_path)
            assert tmp_path.exists()

            loaded = load_mapping(tmp_path)
            assert loaded == dummy_mapping
            assert len(loaded) == 20
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_build_mapping(self, dummy_chunks):
        from packages.rag_core.indexing import build_mapping

        mapping = build_mapping(dummy_chunks, start_id=0)
        assert len(mapping) == 20
        assert mapping[0] == "chunk_000"
        assert mapping[19] == "chunk_019"

    def test_build_mapping_with_offset(self, dummy_chunks):
        from packages.rag_core.indexing import build_mapping

        mapping = build_mapping(dummy_chunks, start_id=100)
        assert mapping[100] == "chunk_000"
        assert mapping[119] == "chunk_019"

    def test_resolve_chunk_ids(self, dummy_mapping):
        from packages.rag_core.indexing import resolve_chunk_ids

        faiss_ids = np.array([[0, 3, 7], [1, 5, 9]])
        result = resolve_chunk_ids(dummy_mapping, faiss_ids)
        assert result == [
            ["chunk_000", "chunk_003", "chunk_007"],
            ["chunk_001", "chunk_005", "chunk_009"],
        ]

    def test_resolve_unknown_id(self, dummy_mapping):
        from packages.rag_core.indexing import resolve_chunk_ids

        faiss_ids = np.array([[0, 999]])
        result = resolve_chunk_ids(dummy_mapping, faiss_ids)
        assert result[0][0] == "chunk_000"
        assert result[0][1] == "UNKNOWN"

    def test_invalid_vectors(self):
        from packages.rag_core.indexing import build_index

        with pytest.raises(ValueError):
            build_index(np.array([]))  # vacío
        with pytest.raises(ValueError):
            build_index(np.array([1.0]))  # 1D

    def test_search_multi_query(self, dummy_vectors):
        from packages.rag_core.indexing import build_index, search

        index = build_index(dummy_vectors)
        # 3 queries simultáneas
        q = np.random.randn(3, 384).astype(np.float32)
        q = q / np.linalg.norm(q, axis=1, keepdims=True)

        scores, ids = search(index, q, k=4)
        assert scores.shape == (3, 4)
        assert ids.shape == (3, 4)


# --------------------------------------------------------------------------- #
# Tests de integración con modelo real
# --------------------------------------------------------------------------- #

class TestEmbeddingsIntegration:
    """Tests con modelo real de embeddings (skip si no instalado)."""

    def test_embed_texts_shape_and_norm(self):
        """embed_texts produce matriz normalizada."""
        try:
            from packages.rag_core.embeddings import embed_texts
        except Exception:
            pytest.skip("sentence-transformers no disponible")

        texts = ["Hello world", "Hola mundo", "Bonjour le monde"]
        vecs = embed_texts(texts, batch_size=2, show_progress=False)

        assert vecs.shape == (3, vecs.shape[1])
        assert vecs.shape[1] > 0  # dim > 0
        norms = np.linalg.norm(vecs, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-4), f"Normas: {norms}"

    def test_embed_texts_empty_raises(self):
        try:
            from packages.rag_core.embeddings import embed_texts
        except Exception:
            pytest.skip("sentence-transformers no disponible")

        with pytest.raises(ValueError):
            embed_texts([], show_progress=False)

    def test_get_embedding_dim(self):
        try:
            from packages.rag_core.embeddings import get_embedding_dim
        except Exception:
            pytest.skip("sentence-transformers no disponible")

        dim = get_embedding_dim()
        assert dim > 0
        assert isinstance(dim, int)

    def test_end_to_end_index_search(self):
        """Round-trip completo: embed → index → search → resolve chunk_ids."""
        try:
            from packages.rag_core.embeddings import embed_texts
            from packages.rag_core.indexing import (
                build_index, search, build_mapping, resolve_chunk_ids,
            )
        except Exception:
            pytest.skip("Dependencias no disponibles")

        chunks = [
            {"chunk_id": "c_a", "text": "Red flags in procurement planning."},
            {"chunk_id": "c_b", "text": "Bid rigging detection in tender phase."},
            {"chunk_id": "c_c", "text": "Contract delivery delays signal fraud."},
            {"chunk_id": "c_d", "text": "Low competition in award stage."},
            {"chunk_id": "c_e", "text": "Unanswered questions during tender."},
        ]

        texts = [c["text"] for c in chunks]
        vectors = embed_texts(texts, batch_size=4, show_progress=False)

        index = build_index(vectors)
        mapping = build_mapping(chunks, start_id=0)

        # Query
        q_text = "risks in the tender phase"
        q_vec = embed_texts([q_text], show_progress=False, is_query=True)
        scores, ids = search(index, q_vec, k=3)

        chunk_ids = resolve_chunk_ids(mapping, ids)
        # Los más similares deberían incluir "Bid rigging detection in tender phase"
        top_chunks = chunk_ids[0]
        assert "c_b" in top_chunks, f"Esperado c_b en top results, got {top_chunks}"
        # La query sobre tender debería dar score alto al chunk de tender
        assert len(top_chunks) == 3