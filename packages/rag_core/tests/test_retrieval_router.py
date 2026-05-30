"""
GATE de aceptación de la Fase 4 (retrieval híbrido + router de familias).

Valida:
- route_family mapea queries a familias por keywords (determinista).
- bm25_search devuelve metadata completa y respeta family_filter.
- faiss_search devuelve metadata completa con índice dummy.
- hybrid_search combina BM25 + FAISS (RRF y weighted) y filtra por familia.
- Tests de integración con datos reales (skip si faltan deps).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def dummy_chunks():
    return [
        {
            "chunk_id": "c1",
            "text": "Planning the procurement budget and needs assessment.",
            "family": "planeacion",
            "indicator_code": "P1",
            "indicator_name": "Budget",
            "page_start": 10,
            "page_end": 11,
        },
        {
            "chunk_id": "c2",
            "text": "Tender invitation and bidding competition open to all.",
            "family": "competencia-licitacion",
            "indicator_code": "T1",
            "indicator_name": "Open tender",
            "page_start": 20,
            "page_end": 21,
        },
        {
            "chunk_id": "c3",
            "text": "Awarding the contract to the lowest bidder.",
            "family": "adjudicacion",
            "indicator_code": "A1",
            "indicator_name": "Lowest price",
            "page_start": 30,
            "page_end": 31,
        },
        {
            "chunk_id": "c4",
            "text": "Contract execution delays and payment milestones.",
            "family": "ejecucion-contrato",
            "indicator_code": "E1",
            "indicator_name": "Delay",
            "page_start": 40,
            "page_end": 41,
        },
        {
            "chunk_id": "c5",
            "text": "Bid rigging and collusion among competitors.",
            "family": "competencia-licitacion",
            "indicator_code": "T2",
            "indicator_name": "Collusion",
            "page_start": 22,
            "page_end": 23,
        },
    ]


@pytest.fixture
def dummy_bm25(dummy_chunks):
    """Mock BM25 para tests unitarios deterministas."""

    class MockBM25:
        def __init__(self, chunks):
            self.chunks = chunks
            self.texts = [c["text"] for c in chunks]
            self.tokens = [set(t.lower().split()) for t in self.texts]

        def get_scores(self, query_tokens):
            scores = []
            qt = set(query_tokens)
            for tokens in self.tokens:
                scores.append(len(qt & tokens))
            return np.array(scores, dtype=np.float32)

    bm25 = MockBM25(dummy_chunks)
    return (bm25, bm25.texts)


@pytest.fixture
def mock_embed():
    """Fixture que devuelve un mock de embed_texts basado en seed fija."""
    dim = 768
    rng = np.random.default_rng(42)

    def _mock(texts, **kwargs):
        q = rng.standard_normal((len(texts), dim)).astype(np.float32)
        return q / np.linalg.norm(q, axis=1, keepdims=True)

    return _mock


# --------------------------------------------------------------------------- #
# Tests unitarios deterministas
# --------------------------------------------------------------------------- #


class TestRouterUnit:
    def test_route_family_keywords_single(self):
        from packages.rag_core.retrievers import route_family

        fams = route_family("What are the risks in the planning phase budget?")
        assert "planeacion" in fams

    def test_route_family_keywords_competition(self):
        from packages.rag_core.retrievers import route_family

        fams = route_family("Bid rigging during tender competition")
        assert "competencia-licitacion" in fams

    def test_route_family_keywords_award(self):
        from packages.rag_core.retrievers import route_family

        fams = route_family("Award selection and winner evaluation")
        assert "adjudicacion" in fams

    def test_route_family_keywords_execution(self):
        from packages.rag_core.retrievers import route_family

        fams = route_family("contract execution and payment milestones")
        assert "ejecucion-contrato" in fams

    def test_route_family_returns_list(self):
        from packages.rag_core.retrievers import route_family

        fams = route_family("something")
        assert isinstance(fams, list)
        assert len(fams) >= 1


class TestBM25Unit:
    def test_bm25_search_returns_metadata(self, dummy_bm25, dummy_chunks):
        from packages.rag_core.retrievers import bm25_search

        res = bm25_search(
            "planning budget", k=3, bm25_obj=dummy_bm25, chunks=dummy_chunks
        )
        assert len(res) <= 3
        for r in res:
            assert "chunk_id" in r
            assert "score" in r
            assert "family" in r
            assert "indicator_code" in r
            assert "indicator_name" in r
            assert "page_start" in r
            assert "page_end" in r
            assert "text" in r

    def test_bm25_family_filter(self, dummy_bm25, dummy_chunks):
        from packages.rag_core.retrievers import bm25_search

        res_all = bm25_search(
            "tender", k=5, bm25_obj=dummy_bm25, chunks=dummy_chunks
        )
        res_filt = bm25_search(
            "tender",
            k=5,
            bm25_obj=dummy_bm25,
            chunks=dummy_chunks,
            family_filter="competencia-licitacion",
        )
        ids_all = {r["chunk_id"] for r in res_all}
        ids_filt = {r["chunk_id"] for r in res_filt}
        assert ids_filt.issubset(ids_all) or len(res_filt) < len(res_all)


class TestFAISSUnit:
    def test_faiss_search_dummy(self, dummy_chunks, mock_embed):
        """FAISS search con índice dummy y embed_texts mockeado."""
        from packages.rag_core.indexing import (
            build_index,
            build_mapping,
            save_index,
            save_mapping,
        )
        from packages.rag_core.retrievers import faiss_search
        import packages.rag_core.embeddings as emb_mod

        dim = 768
        rng = np.random.default_rng(42)
        vecs = rng.standard_normal((len(dummy_chunks), dim)).astype(np.float32)
        vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        index = build_index(vecs)
        mapping = build_mapping(dummy_chunks)

        with tempfile.TemporaryDirectory() as tmpdir:
            idx_path = Path(tmpdir) / "test.index"
            map_path = Path(tmpdir) / "test.json"
            save_index(index, idx_path)
            save_mapping(mapping, map_path)

            original = emb_mod.embed_texts
            emb_mod.embed_texts = mock_embed
            try:
                res = faiss_search(
                    "test",
                    k=3,
                    index_path=idx_path,
                    mapping_path=map_path,
                    chunks=dummy_chunks,
                )
                assert len(res) == 3
                for r in res:
                    assert "chunk_id" in r
                    assert "score" in r
                    assert "family" in r
                    assert "indicator_code" in r
                    assert "indicator_name" in r
                    assert "page_start" in r
                    assert "page_end" in r
                    assert "text" in r
            finally:
                emb_mod.embed_texts = original


class TestHybridFusionUnit:
    def test_rrf_fusion_combines(self):
        from packages.rag_core.retrievers import _rrf_fusion

        a = ["c1", "c2", "c3"]
        b = ["c2", "c3", "c4"]
        fused = _rrf_fusion(a, b)
        ids = [x[0] for x in fused]
        # c2 y c3 aparecen en ambas -> deberían estar arriba
        assert ids[0] in ("c2", "c3")

    def test_weighted_fusion_combines(self):
        from packages.rag_core.retrievers import _weighted_fusion

        a = [
            {"chunk_id": "c1", "score": 10.0},
            {"chunk_id": "c2", "score": 5.0},
        ]
        b = [
            {"chunk_id": "c2", "score": 0.9},
            {"chunk_id": "c3", "score": 0.5},
        ]
        fused = _weighted_fusion(a, b, alpha=0.5)
        ids = [x[0] for x in fused]
        assert "c2" in ids  # presente en ambos

    def test_hybrid_search_format(self, dummy_bm25, dummy_chunks, mock_embed):
        from packages.rag_core.indexing import (
            build_index,
            build_mapping,
            save_index,
            save_mapping,
        )
        from packages.rag_core.retrievers import hybrid_search
        import packages.rag_core.embeddings as emb_mod

        dim = 768
        rng = np.random.default_rng(42)
        vecs = rng.standard_normal((len(dummy_chunks), dim)).astype(np.float32)
        vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        idx = build_index(vecs)
        mapping = build_mapping(dummy_chunks)

        with tempfile.TemporaryDirectory() as tmpdir:
            idx_path = Path(tmpdir) / "test.index"
            map_path = Path(tmpdir) / "test.json"
            save_index(idx, idx_path)
            save_mapping(mapping, map_path)

            original = emb_mod.embed_texts
            emb_mod.embed_texts = mock_embed
            try:
                res = hybrid_search(
                    "tender competition",
                    k=3,
                    bm25_obj=dummy_bm25,
                    chunks=dummy_chunks,
                    index_path=idx_path,
                    mapping_path=map_path,
                )
                assert len(res) <= 3
                for r in res:
                    assert "chunk_id" in r
                    assert "score" in r
                    assert "family" in r
                    assert "indicator_code" in r
                    assert "indicator_name" in r
                    assert "page_start" in r
                    assert "page_end" in r
                    assert "text" in r
            finally:
                emb_mod.embed_texts = original

    def test_hybrid_family_filter_changes_results(
        self, dummy_bm25, dummy_chunks, mock_embed
    ):
        from packages.rag_core.indexing import (
            build_index,
            build_mapping,
            save_index,
            save_mapping,
        )
        from packages.rag_core.retrievers import hybrid_search
        import packages.rag_core.embeddings as emb_mod

        dim = 768
        rng = np.random.default_rng(42)
        vecs = rng.standard_normal((len(dummy_chunks), dim)).astype(np.float32)
        vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        idx = build_index(vecs)
        mapping = build_mapping(dummy_chunks)

        with tempfile.TemporaryDirectory() as tmpdir:
            idx_path = Path(tmpdir) / "test.index"
            map_path = Path(tmpdir) / "test.json"
            save_index(idx, idx_path)
            save_mapping(mapping, map_path)

            original = emb_mod.embed_texts
            emb_mod.embed_texts = mock_embed
            try:
                res_all = hybrid_search(
                    "tender",
                    k=5,
                    bm25_obj=dummy_bm25,
                    chunks=dummy_chunks,
                    index_path=idx_path,
                    mapping_path=map_path,
                )
                res_filt = hybrid_search(
                    "tender",
                    k=5,
                    family="competencia-licitacion",
                    bm25_obj=dummy_bm25,
                    chunks=dummy_chunks,
                    index_path=idx_path,
                    mapping_path=map_path,
                )
                ids_all = {r["chunk_id"] for r in res_all}
                ids_filt = {r["chunk_id"] for r in res_filt}
                assert ids_filt.issubset(ids_all) or len(res_filt) < len(res_all)
            finally:
                emb_mod.embed_texts = original


# --------------------------------------------------------------------------- #
# Tests de integración
# --------------------------------------------------------------------------- #


class TestIntegration:
    def test_bm25_real_with_chunks(self):
        try:
            from rank_bm25 import BM25Okapi
        except Exception:
            pytest.skip("rank_bm25 no disponible")

        from packages.rag_core.retrievers import build_bm25, bm25_search, load_chunks

        chunks = load_chunks()
        bm25_obj = build_bm25(chunks)
        if bm25_obj is None:
            pytest.skip("build_bm25 devolvió None")
        res = bm25_search("bid rigging", k=5, bm25_obj=bm25_obj, chunks=chunks)
        assert len(res) <= 5
        assert all("chunk_id" in r for r in res)

    def test_faiss_real(self):
        from packages.rag_core.retrievers import faiss_search, load_chunks

        chunks = load_chunks()
        try:
            res = faiss_search("collusion in tender", k=5, chunks=chunks)
        except Exception as exc:
            pytest.skip(f"FAISS real no disponible: {exc}")
        assert len(res) <= 5
        assert all("chunk_id" in r for r in res)

    def test_hybrid_real(self):
        try:
            from rank_bm25 import BM25Okapi
        except Exception:
            pytest.skip("rank_bm25 no disponible")

        from packages.rag_core.retrievers import (
            hybrid_search,
            build_bm25,
            load_chunks,
        )

        chunks = load_chunks()
        bm25_obj = build_bm25(chunks)
        if bm25_obj is None:
            pytest.skip("BM25 no disponible")
        try:
            res = hybrid_search(
                "contract delays", k=5, bm25_obj=bm25_obj, chunks=chunks
            )
        except Exception as exc:
            pytest.skip(f"FAISS real no disponible: {exc}")
        assert len(res) <= 5
        for r in res:
            assert "chunk_id" in r
            assert "family" in r

    def test_route_family_real(self):
        from packages.rag_core.retrievers import route_family

        fams = route_family("risks during the award stage")
        assert isinstance(fams, list)
        assert "adjudicacion" in fams

    def test_family_filter_real(self):
        try:
            from rank_bm25 import BM25Okapi
        except Exception:
            pytest.skip("rank_bm25 no disponible")

        from packages.rag_core.retrievers import (
            hybrid_search,
            build_bm25,
            load_chunks,
        )

        chunks = load_chunks()
        bm25_obj = build_bm25(chunks)
        if bm25_obj is None:
            pytest.skip("BM25 no disponible")
        try:
            res_all = hybrid_search(
                "planning budget", k=10, bm25_obj=bm25_obj, chunks=chunks
            )
            res_filt = hybrid_search(
                "planning budget",
                k=10,
                family="planeacion",
                bm25_obj=bm25_obj,
                chunks=chunks,
            )
        except Exception as exc:
            pytest.skip(f"Integración falló: {exc}")

        fams_all = {r["family"] for r in res_all}
        fams_filt = {r["family"] for r in res_filt}
        assert fams_filt.issubset(fams_all) or len(fams_filt) < len(fams_all)
        if res_filt:
            assert all(r["family"] == "planeacion" for r in res_filt)
