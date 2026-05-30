"""
GATE de aceptación de la Fase 7 (evaluación cuantitativa + cualitativa).

Valida:
- recall_at_k y precision_at_k con datos de juguete (determinista).
- Gold set ≥10 items con formato correcto.
- mean_grounding_ratio.
- Integración con pipeline real (skip si deps faltan).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def toy_retrieved():
    return ["R001", "R003", "R005", "R010", "R012", "R018", "R028"]


@pytest.fixture
def toy_relevant():
    return ["R001", "R002", "R005"]


@pytest.fixture
def gold_items():
    from packages.evals.metrics import load_goldset
    return load_goldset()


# --------------------------------------------------------------------------- #
# Tests unitarios deterministas
# --------------------------------------------------------------------------- #


class TestMetricsUnit:
    def test_recall_at_3(self, toy_retrieved, toy_relevant):
        from packages.evals.metrics import recall_at_k

        r = recall_at_k(toy_retrieved, toy_relevant, k=3)
        assert r == pytest.approx(2 / 3, 0.01)

    def test_recall_at_5(self, toy_retrieved, toy_relevant):
        from packages.evals.metrics import recall_at_k

        r = recall_at_k(toy_retrieved, toy_relevant, k=5)
        assert r == pytest.approx(2 / 3, 0.01)

    def test_recall_perfect(self):
        from packages.evals.metrics import recall_at_k

        r = recall_at_k(
            ["R001", "R002", "R005"], ["R001", "R002", "R005"], k=3
        )
        assert r == 1.0

    def test_recall_zero(self, toy_relevant):
        from packages.evals.metrics import recall_at_k

        r = recall_at_k(["R099", "R098"], toy_relevant, k=5)
        assert r == 0.0

    def test_recall_empty_relevant(self):
        from packages.evals.metrics import recall_at_k

        r = recall_at_k(["R001"], [], k=5)
        assert r == 1.0

    def test_precision_at_3(self, toy_retrieved, toy_relevant):
        from packages.evals.metrics import precision_at_k

        p = precision_at_k(toy_retrieved, toy_relevant, k=3)
        assert p == pytest.approx(2 / 3, 0.01)

    def test_precision_at_5(self, toy_retrieved, toy_relevant):
        from packages.evals.metrics import precision_at_k

        p = precision_at_k(toy_retrieved, toy_relevant, k=5)
        assert p == pytest.approx(2 / 5, 0.01)

    def test_precision_perfect(self):
        from packages.evals.metrics import precision_at_k

        p = precision_at_k(
            ["R001", "R002", "R005"], ["R001", "R002", "R005"], k=3
        )
        assert p == 1.0

    def test_precision_zero_k(self, toy_retrieved, toy_relevant):
        from packages.evals.metrics import precision_at_k

        p = precision_at_k(toy_retrieved, toy_relevant, k=0)
        assert p == 0.0

    def test_mean_grounding_ratio(self):
        from packages.evals.metrics import mean_grounding_ratio

        results = [
            {"grounding_ratio": 0.8},
            {"grounding_ratio": 0.6},
            {"grounding_ratio": 0.4},
        ]
        assert mean_grounding_ratio(results) == pytest.approx(0.6, 0.01)

    def test_mean_grounding_ratio_empty(self):
        from packages.evals.metrics import mean_grounding_ratio

        assert mean_grounding_ratio([]) == 0.0


class TestGoldSet:
    def test_goldset_has_min_items(self, gold_items):
        assert len(gold_items) >= 10, (
            f"Gold set debe tener ≥10 items, tiene {len(gold_items)}"
        )

    def test_goldset_format(self, gold_items):
        for item in gold_items:
            assert "query" in item, f"Falta 'query' en {item}"
            assert "relevant_indicator_codes" in item, f"Falta 'relevant_indicator_codes' en {item}"
            assert isinstance(item["relevant_indicator_codes"], list)
            assert len(item["relevant_indicator_codes"]) >= 1

    def test_goldset_indicator_codes_valid(self, gold_items):
        import json
        from pathlib import Path
        all_codes = set()
        chunks_path = Path("data/processed/redflags_chunks.jsonl")
        with open(chunks_path) as f:
            for line in f:
                c = json.loads(line.strip())
                code = c.get("indicator_code")
                if code:
                    all_codes.add(code)

        for item in gold_items:
            for code in item["relevant_indicator_codes"]:
                assert code in all_codes, f"Indicator code {code} not found in dataset"


# --------------------------------------------------------------------------- #
# Tests de integración
# --------------------------------------------------------------------------- #


class TestIntegration:
    def test_evaluate_on_goldset_with_real_retrieval(self, gold_items):
        try:
            from packages.rag_core.retrievers import faiss_search, load_chunks
        except Exception:
            pytest.skip("Retrievers no disponible")

        from packages.evals.metrics import evaluate_on_goldset

        chunks = load_chunks()

        retrieved_items = []
        for item in gold_items[:5]:
            try:
                candidates = faiss_search(item["query"], k=10, chunks=chunks)
                codes = [
                    c.get("indicator_code")
                    for c in candidates
                    if c.get("indicator_code")
                ]
                retrieved_items.append({
                    "retrieved_indicator_codes": codes,
                    "grounding_ratio": 0.5,
                })
            except Exception:
                retrieved_items.append({
                    "retrieved_indicator_codes": [],
                    "grounding_ratio": 0.0,
                })

        report = evaluate_on_goldset(
            gold_items[:5], retrieved_items, ks=[3, 5, 10]
        )
        assert "recall_at_k" in report
        assert "precision_at_k" in report
        assert report["recall_at_k"][3] >= 0.0
        assert report["recall_at_k"][3] <= 1.0
