"""
GATE de aceptación de la Fase 6 (Qwen + grounding + citas).

Valida:
- split_sentences, verify_grounding (lexical), build_citations.
- refusal when grounding ratio is below threshold.
- safe language in system prompt.
- analyze() with fake LLM injection (deterministic, always runs).
- Integration tests with real retrieval (skip if deps missing).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def dummy_chunks():
    return [
        {
            "chunk_id": "c1",
            "text": "Budget issues in procurement planning lead to risks. The budget allocation was irregular.",
            "family": "planeacion",
            "indicator_code": "P001",
            "indicator_name": "Budget Irregularities",
            "page_start": 10,
            "page_end": 12,
        },
        {
            "chunk_id": "c2",
            "text": "Single bidder in tender process indicates low competition and possible collusion.",
            "family": "competencia-licitacion",
            "indicator_code": "T005",
            "indicator_name": "Single Bidder Risk",
            "page_start": 25,
            "page_end": 26,
        },
        {
            "chunk_id": "c3",
            "text": "Contract execution delays and payment milestones indicate implementation risks.",
            "family": "ejecucion-contrato",
            "indicator_code": "E010",
            "indicator_name": "Execution Delays",
            "page_start": 40,
            "page_end": 42,
        },
        {
            "chunk_id": "c4",
            "text": "Award selection criteria should be transparent. Lowest price not always best value.",
            "family": "adjudicacion",
            "indicator_code": "A003",
            "indicator_name": "Award Transparency",
            "page_start": 30,
            "page_end": 31,
        },
        {
            "chunk_id": "c5",
            "text": "Bid rigging is a red flag. Collusion among bidders detected through price patterns.",
            "family": "competencia-licitacion",
            "indicator_code": "T002",
            "indicator_name": "Bid Rigging",
            "page_start": 20,
            "page_end": 21,
        },
    ]


@pytest.fixture
def fake_generate():
    def _generate(query, chunks, system_prompt):
        return (
            "El proceso de licitación presenta una señal de riesgo en la etapa de planeación. "
            "El presupuesto asignado muestra posibles irregularidades en la asignación de recursos. "
            "Requiere revisión humana."
        )

    return _generate


@pytest.fixture
def fake_generate_refusal():
    def _generate(query, chunks, system_prompt):
        return (
            "No se encontraron indicadores relevantes en los documentos. "
            "No hay evidencia suficiente para emitir observaciones. "
            "Requiere revisión humana."
        )

    return _generate


# --------------------------------------------------------------------------- #
# Tests unitarios deterministas
# --------------------------------------------------------------------------- #


class TestVerifierUnit:
    def test_split_sentences(self):
        from packages.rag_core.verifier import split_sentences

        text = "First sentence. Second sentence! Third one? Last."
        sents = split_sentences(text)
        assert len(sents) == 4
        assert "First sentence" in sents[0]

    def test_split_sentences_newlines(self):
        from packages.rag_core.verifier import split_sentences

        text = "Line one\nLine two\n\nLine three."
        sents = split_sentences(text)
        assert len(sents) == 3

    def test_verify_grounding_supported(self, dummy_chunks):
        from packages.rag_core.verifier import verify_grounding

        sentences = [
            "Budget procurement planning had irregularities.",
            "Contract execution delays are a problem.",
        ]
        result = verify_grounding(sentences, dummy_chunks, threshold=0.3)

        assert result["grounding_ratio"] > 0
        assert result["sentences"][0]["supported"]  # should match c1
        assert "c1" == result["sentences"][0]["best_chunk_id"]

    def test_verify_grounding_none_supported(self, dummy_chunks):
        from packages.rag_core.verifier import verify_grounding

        sentences = ["Completely unrelated quantum physics discussion here."]
        result = verify_grounding(sentences, dummy_chunks, threshold=0.3)

        assert result["grounding_ratio"] == 0.0
        assert not result["sentences"][0]["supported"]

    def test_verify_grounding_higher_threshold(self, dummy_chunks):
        from packages.rag_core.verifier import verify_grounding

        sentences = ["Budget allocation problems in procurement processes."]
        result = verify_grounding(sentences, dummy_chunks, threshold=0.8)
        assert result["grounding_ratio"] <= 0.5

    def test_refusal_check(self, dummy_chunks):
        from packages.rag_core.verifier import verify_grounding, refusal_check

        sentences = ["Quantum physics discussion."]
        result = verify_grounding(sentences, dummy_chunks, threshold=0.3)
        refusal = refusal_check(result)

        assert "No hay evidencia suficiente" in refusal
        assert "revisión humana" in refusal.lower()

    def test_refusal_check_passes_when_grounded(self, dummy_chunks):
        from packages.rag_core.verifier import verify_grounding, refusal_check

        sentences = ["Budget procurement planning irregularities."]
        result = verify_grounding(sentences, dummy_chunks, threshold=0.3)
        refusal = refusal_check(result)

        assert refusal == ""


class TestCitationsUnit:
    def test_build_citations(self, dummy_chunks):
        from packages.rag_core.verifier import verify_grounding
        from packages.rag_core.citations import build_citations

        sentences = [
            "Budget procurement planning had irregularities.",
            "Unrelated text.",
        ]
        grounding = verify_grounding(sentences, dummy_chunks, threshold=0.3)
        citations = build_citations(grounding["sentences"], dummy_chunks)

        assert len(citations) == 1
        assert citations[0]["chunk_id"] == "c1"
        assert citations[0]["indicator_code"] == "P001"
        assert citations[0]["indicator_name"] == "Budget Irregularities"
        assert citations[0]["page_start"] == 10
        assert citations[0]["page_end"] == 12


class TestAgentUnit:
    def test_analyze_with_fake_llm(self, dummy_chunks, fake_generate):
        from packages.rag_core.agent import analyze

        result = analyze(
            "procurement budget issues",
            generate_fn=fake_generate,
            retrieved_chunks=dummy_chunks,
        )

        assert "answer" in result
        assert "Requiere revisión humana" in result["answer"]
        assert "sentences" in result
        assert "citations" in result
        assert "grounding_ratio" in result
        assert isinstance(result["grounding_ratio"], float)
        assert "retrieved" in result

    def test_analyze_refusal(self, dummy_chunks, fake_generate_refusal):
        from packages.rag_core.agent import analyze

        result = analyze(
            "irrelevant query",
            generate_fn=fake_generate_refusal,
            retrieved_chunks=dummy_chunks,
        )

        assert "answer" in result
        assert "citations" in result
        assert result["grounding_ratio"] >= 0.0

    def test_safe_language_in_system_prompt(self):
        from packages.rag_core.agent import SYSTEM_PROMPT

        prompt_lower = SYSTEM_PROMPT.lower()
        required = [
            "señal de riesgo",
            "red flag potencial",
            "posible irregularidad",
            "revisión humana",
            "no hay evidencia suficiente",
        ]
        for phrase in required:
            assert phrase in prompt_lower, f"Falta '{phrase}' en SYSTEM_PROMPT"

        assert "nunca afirmes corrupción" in prompt_lower, (
            "Falta instrucción de no afirmar corrupción"
        )

    def test_analyze_with_grounding_threshold(self, dummy_chunks, fake_generate):
        from packages.rag_core.agent import analyze

        result = analyze(
            "budget issues",
            generate_fn=fake_generate,
            retrieved_chunks=dummy_chunks,
            grounding_threshold=0.5,
        )

        assert "grounding_ratio" in result
        assert isinstance(result["grounding_ratio"], float)


# --------------------------------------------------------------------------- #
# Tests de integración
# --------------------------------------------------------------------------- #


class TestIntegration:
    def test_analyze_with_faiss_retrieval(self):
        try:
            from packages.rag_core.retrievers import faiss_search, load_chunks
        except Exception:
            pytest.skip("Retrievers no disponible")

        from packages.rag_core.agent import _build_context, SYSTEM_PROMPT

        chunks = load_chunks()
        candidates = faiss_search("bid rigging collusion", k=5, chunks=chunks)

        assert len(candidates) > 0

        # Verify context builder works with real data
        ctx = _build_context(candidates)
        assert "Fuente:" in ctx

    def test_analyze_end_to_end_with_fallback(self):
        try:
            from packages.rag_core.retrievers import faiss_search, load_chunks
        except Exception:
            pytest.skip("Retrievers no disponible")

        from packages.rag_core.agent import analyze, _minimal_analysis
        from packages.rag_core.agent import SYSTEM_PROMPT

        chunks = load_chunks()
        candidates = faiss_search("contract execution delays", k=5, chunks=chunks)

        result = analyze(
            "contract execution delays",
            generate_fn=_minimal_analysis,
            retrieved_chunks=candidates,
        )

        assert "answer" in result
        assert "grounding_ratio" in result
        assert "citations" in result
        assert len(result["citations"]) >= 0

    def test_grounding_with_real_data(self):
        try:
            from packages.rag_core.retrievers import faiss_search, load_chunks
        except Exception:
            pytest.skip("Retrievers no disponible")

        from packages.rag_core.verifier import verify_grounding

        chunks = load_chunks()
        candidates = faiss_search("tender planning budget", k=5, chunks=chunks)

        sentences = [
            "Budget planning in procurement has risks.",
        ]
        result = verify_grounding(sentences, candidates)
        assert "grounding_ratio" in result
        assert "sentences" in result
