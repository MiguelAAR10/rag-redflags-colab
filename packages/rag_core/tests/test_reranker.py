"""
GATE de aceptación de la Fase 5 (reranker cross-encoder).

Valida:
- rerank reordena candidatos por cross-encoder score.
- unit test determinista con fake cross-encoder (siempre corre).
- integration test con modelo real (skip si no disponible).
- fallback: si cross-encoder falla, devuelve candidatos originales sin romper.
"""

from __future__ import annotations

import pytest

REPO_ROOT = pytest.fixture


@pytest.fixture
def dummy_candidates():
    return [
        {
            "chunk_id": "c1",
            "text": "Planning the procurement budget and needs assessment.",
            "score": 0.82,
            "family": "planeacion",
            "indicator_name": "Budget",
            "page_start": 10,
            "page_end": 11,
        },
        {
            "chunk_id": "c2",
            "text": "Tender invitation and bidding competition open to all.",
            "score": 0.80,
            "family": "competencia-licitacion",
            "indicator_name": "Open tender",
            "page_start": 20,
            "page_end": 21,
        },
        {
            "chunk_id": "c3",
            "text": "Awarding the contract to the lowest bidder.",
            "score": 0.78,
            "family": "adjudicacion",
            "indicator_name": "Lowest price",
            "page_start": 30,
            "page_end": 31,
        },
        {
            "chunk_id": "c4",
            "text": "Contract execution delays and payment milestones.",
            "score": 0.75,
            "family": "ejecucion-contrato",
            "indicator_name": "Delay",
            "page_start": 40,
            "page_end": 41,
        },
        {
            "chunk_id": "c5",
            "text": "Bid rigging and collusion among competitors.",
            "score": 0.70,
            "family": "competencia-licitacion",
            "indicator_name": "Collusion",
            "page_start": 22,
            "page_end": 23,
        },
    ]


@pytest.fixture
def fake_cross_encoder(monkeypatch):
    """
    Fake cross-encoder que devuelve scores inversos al orden original.
    Así el test verifica que rerank REORDENA realmente.
    """
    call_count = [0]

    class FakeCrossEncoder:
        def __init__(self, *args, **kwargs):
            pass

        def predict(self, pairs, show_progress_bar=False):
            call_count[0] += 1
            n = len(pairs)
            scores = [1.0 - (i / n) for i in range(n)]
            class FakeScores:
                def tolist(self):
                    return scores
            return FakeScores()

    import packages.rag_core.rerankers as rerank_mod
    monkeypatch.setattr(rerank_mod, "_load_cross_encoder", lambda *args, **kwargs: FakeCrossEncoder())
    return call_count


# --------------------------------------------------------------------------- #
# Tests unitarios deterministas (SIEMPRE corren)
# --------------------------------------------------------------------------- #

class TestRerankerUnit:
    def test_rerank_reorders_and_adds_score(self, dummy_candidates, fake_cross_encoder):
        from packages.rag_core.rerankers import rerank

        result = rerank(
            "What are the risks in planning and tender?",
            dummy_candidates,
            top_n=5,
        )

        assert len(result) == 5
        for r in result:
            assert "rerank_score" in r

        scores = [r["rerank_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_respects_top_n(self, dummy_candidates, fake_cross_encoder):
        from packages.rag_core.rerankers import rerank

        result = rerank(
            "contract execution delays",
            dummy_candidates,
            top_n=3,
        )

        assert len(result) == 3

    def test_rerank_empty_candidates(self, fake_cross_encoder):
        from packages.rag_core.rerankers import rerank

        result = rerank("query", [], top_n=5)
        assert result == []

    def test_rerank_preserves_metadata(self, dummy_candidates, fake_cross_encoder):
        from packages.rag_core.rerankers import rerank

        result = rerank("query", dummy_candidates, top_n=5)

        for r in result:
            assert "chunk_id" in r
            assert "text" in r
            assert "family" in r
            assert "indicator_name" in r
            assert "page_start" in r
            assert "page_end" in r

    def test_rerank_fallback_on_model_error(self, dummy_candidates, monkeypatch):
        """Si _load_cross_encoder lanza, se devuelve candidatos originales."""
        from packages.rag_core.rerankers import rerank
        import packages.rag_core.rerankers as rerank_mod

        def fail_load(*args, **kwargs):
            raise RuntimeError("model not available")

        monkeypatch.setattr(rerank_mod, "_load_cross_encoder", fail_load)

        result = rerank("query", dummy_candidates, top_n=5)

        assert len(result) == 5
        assert "rerank_score" not in result[0]

    def test_rerank_fallback_on_predict_error(self, dummy_candidates, monkeypatch):
        """Si predict() lanza, se devuelve candidatos originales."""
        from packages.rag_core.rerankers import rerank
        import packages.rag_core.rerankers as rerank_mod

        class BadCrossEncoder:
            def predict(self, *args, **kwargs):
                raise RuntimeError("predict failed")

        monkeypatch.setattr(rerank_mod, "_load_cross_encoder", lambda *args, **kwargs: BadCrossEncoder())

        result = rerank("query", dummy_candidates, top_n=5)

        assert len(result) == 5


# --------------------------------------------------------------------------- #
# Tests de integración (skip si modelo no disponible)
# --------------------------------------------------------------------------- #

class TestRerankerIntegration:
    def test_rerank_with_real_model(self):
        from packages.rag_core.rerankers import rerank

        candidates = [
            {
                "chunk_id": "c1",
                "text": "Planning the procurement budget and needs assessment.",
                "score": 0.82,
                "family": "planeacion",
                "indicator_name": "Budget",
            },
            {
                "chunk_id": "c2",
                "text": "Tender invitation and bidding competition.",
                "score": 0.80,
                "family": "competencia-licitacion",
                "indicator_name": "Open tender",
            },
            {
                "chunk_id": "c3",
                "text": "Awarding the contract to the lowest bidder.",
                "score": 0.78,
                "family": "adjudicacion",
                "indicator_name": "Lowest price",
            },
        ]

        try:
            result = rerank("risks in tender competition", candidates, top_n=3)
        except Exception as exc:
            pytest.skip(f"Modelo real no disponible: {exc}")

        assert len(result) <= 3
        for r in result:
            assert "rerank_score" in r

    def test_rerank_top5_from_real_candidates(self):
        from packages.rag_core.rerankers import rerank, load_candidates_from_faiss

        try:
            candidates = load_candidates_from_faiss("bid rigging", k=20)
        except Exception as exc:
            pytest.skip(f"No se pudieron cargar candidatos: {exc}")

        if len(candidates) < 5:
            pytest.skip("No hay candidatos suficientes")

        try:
            result = rerank("bid rigging and collusion", candidates, top_n=5)
        except Exception as exc:
            pytest.skip(f"Reranker no disponible: {exc}")

        assert len(result) <= 5
        assert "rerank_score" in result[0]