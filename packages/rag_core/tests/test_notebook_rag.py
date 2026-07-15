"""Notebook dual-RAG helpers: deterministic tests with no network access."""

from __future__ import annotations

import time

import pytest


@pytest.fixture
def retrieved_chunks():
    return [
        {
            "chunk_id": "ocp-1",
            "indicator_code": "R003",
            "indicator_name": "Short tender period",
            "text": "A very short tender period can restrict competition.",
        },
        {
            "chunk_id": "ocp-2",
            "indicator_code": "R018",
            "indicator_name": "Single bid received",
            "text": "A single bid received can be a red flag potential requiring review.",
        },
    ]


class TestConfiguration:
    def test_configuration_requires_complete_credentials(self):
        from packages.rag_core.notebook_rag import (
            gemini_configured,
            qdrant_configured,
        )

        assert not qdrant_configured({})
        assert not qdrant_configured({"QDRANT_URL": "https://qdrant.example"})
        assert qdrant_configured(
            {"QDRANT_ENDPOINT": "https://qdrant.example", "QDRANT_API_KEY": "key"}
        )
        assert not gemini_configured({})
        assert gemini_configured({"GEMINI_API_KEY": "key"})
        assert gemini_configured({"GOOGLE_API_KEY": "key"})
        assert gemini_configured(
            {
                "GOOGLE_GENAI_USE_VERTEXAI": "true",
                "GOOGLE_CLOUD_PROJECT": "project",
            }
        )


class TestRetrieve:
    def test_faiss_pass_has_explicit_status_results_and_latency(self, monkeypatch):
        from packages.rag_core import vector_store
        import packages.rag_core.notebook_rag as notebook_rag

        class Store:
            def search(self, query, k):
                assert (query, k) == ("single bidder", 5)
                return [{"indicator_code": "R018", "text": "evidence"}]

        monkeypatch.setattr(
            vector_store, "make_vector_store", lambda kind, **kwargs: Store()
        )

        result = notebook_rag.retrieve("single bidder")

        assert result["status"] == "PASS"
        assert result["backend"] == "faiss"
        assert result["results"][0]["indicator_code"] == "R018"
        assert result["latency_ms"] >= 0
        assert result["error"] is None

    def test_empty_query_is_error_without_constructing_store(self, monkeypatch):
        from packages.rag_core import vector_store
        import packages.rag_core.notebook_rag as notebook_rag

        monkeypatch.setattr(
            vector_store,
            "make_vector_store",
            lambda *a, **k: pytest.fail("store must not be constructed"),
        )

        result = notebook_rag.retrieve("   ")

        assert result["status"] == "ERROR"
        assert result["results"] == []
        assert "vacía" in result["error"]

    def test_missing_qdrant_credentials_skips_without_constructing_client(
        self, monkeypatch
    ):
        from packages.rag_core import vector_store
        import packages.rag_core.notebook_rag as notebook_rag

        for name in (
            "QDRANT_URL",
            "QDRANT_ENDPOINT",
            "QDRANT_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_CLOUD_PROJECT",
        ):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(
            vector_store,
            "make_vector_store",
            lambda *a, **k: pytest.fail("client must not be constructed"),
        )

        result = notebook_rag.retrieve("query", backend="qdrant")

        assert result["status"] == "SKIPPED"
        assert result["results"] == []
        assert "credenciales" in result["error"].lower()

    def test_invalid_backend_and_store_failure_are_explicit_errors(self, monkeypatch):
        from packages.rag_core import vector_store
        import packages.rag_core.notebook_rag as notebook_rag

        invalid = notebook_rag.retrieve("query", backend="pinecone")
        assert invalid["status"] == "ERROR"
        assert "pinecone" in invalid["error"]

        monkeypatch.setattr(
            vector_store,
            "make_vector_store",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline")),
        )
        failed = notebook_rag.retrieve("query", backend="faiss")
        assert failed["status"] == "ERROR"
        assert failed["results"] == []
        assert failed["error"] == "offline"

    def test_timeout_is_error(self, monkeypatch):
        from packages.rag_core import vector_store
        import packages.rag_core.notebook_rag as notebook_rag

        class SlowStore:
            def search(self, query, k):
                time.sleep(0.05)
                return []

        monkeypatch.setattr(
            vector_store, "make_vector_store", lambda *a, **k: SlowStore()
        )

        result = notebook_rag.retrieve("query", timeout_s=0.001)

        assert result["status"] == "ERROR"
        assert "timeout" in result["error"].lower()


class TestCompareBackends:
    def test_uses_recall_at_five_constant(self):
        from packages.rag_core.notebook_rag import RECALL_K, compare_backends

        assert RECALL_K == 5

        calls = []

        def fake_retrieve(query, backend, k, timeout_s):
            calls.append((query, backend, k, timeout_s))
            return {
                "backend": backend,
                "status": "PASS",
                "results": [{"indicator_code": "R001"}],
                "latency_ms": 1.0,
                "error": None,
            }

        compare_backends(
            [{"query": "q", "relevant_indicator_codes": ["R001"]}],
            retrieve_fn=fake_retrieve,
        )

        assert all(call[2] == 5 for call in calls)

    def test_compares_recall_latency_and_codes_without_scores(self):
        from packages.rag_core.notebook_rag import compare_backends

        gold = [
            {
                "query": "single bidder",
                "relevant_indicator_codes": ["R018", "R019"],
            },
            {
                "query": "short deadline",
                "relevant_indicator_codes": ["R003"],
            },
            {
                "query": "cookies",
                "relevant_indicator_codes": [],
                "trap": True,
            },
        ]
        responses = {
            ("faiss", "single bidder"): ["R018", "R999"],
            ("faiss", "short deadline"): ["R003"],
            ("qdrant", "single bidder"): ["R018", "R019"],
            ("qdrant", "short deadline"): ["R777"],
        }
        calls = []

        def fake_retrieve(query, backend, k, timeout_s):
            calls.append((backend, query, k, timeout_s))
            return {
                "backend": backend,
                "status": "PASS",
                "results": [
                    {"indicator_code": code, "score": 0.99}
                    for code in responses[(backend, query)]
                ],
                "latency_ms": 12.5,
                "error": None,
            }

        report = compare_backends(gold, retrieve_fn=fake_retrieve, timeout_s=3)

        assert report["evaluated_items"] == 2
        assert len(calls) == 4
        assert all(call[2:] == (5, 3) for call in calls)
        assert report["backends"]["faiss"]["status"] == "PASS"
        assert report["backends"]["faiss"]["recall_at_5"] == pytest.approx(0.75)
        assert report["backends"]["qdrant"]["recall_at_5"] == pytest.approx(0.5)
        assert report["backends"]["faiss"]["latency_ms"] == pytest.approx(25.0)
        assert report["backends"]["faiss"]["items"][0]["retrieved_codes"] == [
            "R018",
            "R999",
        ]
        assert report["differences"][0] == {
            "query": "single bidder",
            "only_faiss": ["R999"],
            "only_qdrant": ["R019"],
        }
        assert "score" not in repr(report).lower()

    def test_empty_gold_and_backend_errors_remain_explicit(self):
        from packages.rag_core.notebook_rag import compare_backends

        empty = compare_backends([], retrieve_fn=pytest.fail)
        assert empty["status"] == "SKIPPED"
        assert empty["evaluated_items"] == 0

        def failed(query, backend, k, timeout_s):
            return {
                "backend": backend,
                "status": "ERROR",
                "results": [],
                "latency_ms": 1.0,
                "error": "offline",
            }

        report = compare_backends(
            [{"query": "q", "relevant_indicator_codes": ["R001"]}],
            retrieve_fn=failed,
        )
        assert report["status"] == "ERROR"
        assert report["backends"]["faiss"]["status"] == "ERROR"
        assert report["backends"]["qdrant"]["items"][0]["error"] == "offline"

    def test_skipped_backend_makes_dual_status_skipped(self):
        from packages.rag_core.notebook_rag import compare_backends

        def fake_retrieve(query, backend, k, timeout_s):
            if backend == "qdrant":
                return {
                    "backend": "qdrant",
                    "status": "SKIPPED",
                    "results": [],
                    "latency_ms": 0.0,
                    "error": "no creds",
                }
            return {
                "backend": "faiss",
                "status": "PASS",
                "results": [{"indicator_code": "R001"}],
                "latency_ms": 10.0,
                "error": None,
            }

        report = compare_backends(
            [{"query": "q", "relevant_indicator_codes": ["R001"]}],
            retrieve_fn=fake_retrieve,
        )

        assert report["status"] == "SKIPPED"
        assert report["backends"]["faiss"]["status"] == "PASS"
        assert report["backends"]["qdrant"]["status"] == "SKIPPED"

    def test_error_takes_precedence_over_skipped(self):
        from packages.rag_core.notebook_rag import compare_backends

        def fake_retrieve(query, backend, k, timeout_s):
            if backend == "faiss":
                return {
                    "backend": "faiss",
                    "status": "ERROR",
                    "results": [],
                    "latency_ms": 0.0,
                    "error": "offline",
                }
            return {
                "backend": "qdrant",
                "status": "SKIPPED",
                "results": [],
                "latency_ms": 0.0,
                "error": "no creds",
            }

        report = compare_backends(
            [{"query": "q", "relevant_indicator_codes": ["R001"]}],
            retrieve_fn=fake_retrieve,
        )

        assert report["status"] == "ERROR"
        assert report["backends"]["faiss"]["status"] == "ERROR"
        assert report["backends"]["qdrant"]["status"] == "SKIPPED"


class TestValidateDualEvidence:
    def test_accepts_signal_with_literal_contract_and_grounded_ocp_citation(
        self, retrieved_chunks
    ):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "The tender was open for only two days. Only one bid was received."
        answer = """
1. Señal: Short tender period
   - Evidencia del fragmento: "The tender was open for only two days"
   - This indicates a very short tender period.
Requiere revisión humana.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["status"] == "PASS"
        assert result["requires_human_review"] is True
        assert result["accepted_count"] == 1
        signal = result["signals"][0]
        assert signal["accepted"] is True
        assert signal["contract_evidence"]["verified"] is True
        assert signal["standard_evidence"]["verified"] is True
        assert signal["standard_evidence"]["indicator_code"] == "R003"
        assert signal["standard_evidence"]["chunk_id"] == "ocp-1"

    def test_rejects_paraphrased_contract_quote(self, retrieved_chunks):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "The tender was open for only two days."
        answer = """
1. Señal: Paraphrase
   - Evidencia del fragmento: "The submission window was extremely brief"
   - This indicates a very short tender period.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["accepted_count"] == 0
        signal = result["signals"][0]
        assert signal["contract_evidence"]["verified"] is False
        assert signal["accepted"] is False

    def test_rejects_signal_without_ocp_grounding(self, retrieved_chunks):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "The tender was open for only two days."
        answer = """
1. Señal: No OCP grounding
   - Evidencia del fragmento: "The tender was open for only two days"
   - This is about astronomy and planets.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["accepted_count"] == 0
        signal = result["signals"][0]
        assert signal["standard_evidence"]["verified"] is False
        assert signal["accepted"] is False

    def test_rejects_incomplete_signals_without_discarding_valid_ones(
        self, retrieved_chunks
    ):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "The tender was open for only two days. Only one bid was received."
        answer = """
1. Señal: Bad contract quote
   - Evidencia del fragmento: "The submission window was extremely brief"
   - This indicates a very short tender period.
2. Señal: Good signal
   - Evidencia del fragmento: "Only one bid was received"
   - A single bid received can be a red flag potential.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["status"] == "REVIEW_REQUIRED"
        assert [signal["accepted"] for signal in result["signals"]] == [False, True]
        assert result["accepted_count"] == 1
        assert result["rejected_count"] == 1

    def test_preserves_case_and_unicode(self, retrieved_chunks):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "Señal de riesgo en contrato PÚBLICO."
        answer = """
1. Señal: Unicode preserved
   - Evidencia del fragmento: "Señal de riesgo"
   - A very short tender period can restrict competition.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["accepted_count"] == 1
        signal = result["signals"][0]
        assert signal["contract_evidence"]["verified"] is True

    def test_rejects_case_change_in_contract_quote(self, retrieved_chunks):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "The tender was open for only two days."
        answer = """
1. Señal: Wrong case
   - Evidencia del fragmento: "the tender was open for only two days"
   - This indicates a very short tender period.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["accepted_count"] == 0
        signal = result["signals"][0]
        assert signal["contract_evidence"]["verified"] is False

    def test_requires_indicator_code_from_chunk_not_full_text_fallback(
        self, retrieved_chunks, monkeypatch
    ):
        import packages.rag_core.notebook_rag as notebook_rag
        from packages.rag_core.citations import build_citations

        def fake_build_citations(sentence_results, chunks):
            # Simulate a citation with a chunk that lacks indicator_code.
            citations = build_citations(sentence_results, chunks)
            for citation in citations:
                citation["indicator_code"] = None
            return citations

        monkeypatch.setattr(notebook_rag, "build_citations", fake_build_citations)

        from packages.rag_core.notebook_rag import validate_dual_evidence

        contract = "The tender was open for only two days."
        answer = """
1. Señal: Missing indicator code
   - Evidencia del fragmento: "The tender was open for only two days"
   - This indicates a very short tender period.
"""

        result = validate_dual_evidence(
            {"answer": answer, "retrieved": retrieved_chunks}, contract
        )

        assert result["accepted_count"] == 0
        signal = result["signals"][0]
        assert signal["standard_evidence"]["verified"] is False

    @pytest.mark.parametrize(
        "analysis,contract",
        [
            ({"answer": "", "retrieved": []}, "contract"),
            ({"answer": "No hay señales.", "retrieved": []}, ""),
        ],
    )
    def test_empty_input_requires_human_review(self, analysis, contract):
        from packages.rag_core.notebook_rag import validate_dual_evidence

        result = validate_dual_evidence(analysis, contract)

        assert result["status"] == "REVIEW_REQUIRED"
        assert result["signals"] == []
        assert result["requires_human_review"] is True
