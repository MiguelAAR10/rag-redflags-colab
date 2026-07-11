"""GATE F18 — grounding 'gemini': semántico multilingüe con embed_fn inyectable.

Cubre el caso que el método léxico no puede resolver: respuesta en español
contra corpus en inglés (solapamiento de tokens ≈ 0 aunque la evidencia sea
correcta). El embed_fn fake es determinista: no hay red en CI.
"""

from __future__ import annotations

import math

import pytest


def _unit(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


@pytest.fixture
def fake_embed_fn():
    """Embeddings deterministas por tema, independientes del idioma.

    Simula el comportamiento multilingüe de gemini-embedding-001: la frase en
    español sobre oferente único cae cerca del chunk en inglés de single bid.
    """
    # Orden importa: 'period' antes que 'bid' para que "bidding period"
    # caiga en el tema plazos y no en el tema oferente-unico.
    vocab = {
        "oferente": [1.0, 0.0, 0.0],
        "plazo": [0.0, 1.0, 0.0],
        "period": [0.05, 0.95, 0.0],
        "bid": [0.95, 0.05, 0.0],
        "francia": [0.0, 0.0, 1.0],
        "cookies": [0.0, 0.1, 0.9],
    }

    def _embed(texts):
        out = []
        for t in texts:
            low = t.lower()
            vec = [0.01, 0.01, 0.01]
            for word, wvec in vocab.items():
                if word in low:
                    vec = wvec
                    break
            out.append(_unit(vec))
        return out

    return _embed


@pytest.fixture
def english_chunks():
    return [
        {"chunk_id": "c1", "text": "Single bid received for the tender."},
        {"chunk_id": "c2", "text": "Short bidding period before the deadline."},
    ]


class TestGeminiGrounding:
    def test_cross_lingual_sentence_is_supported(self, fake_embed_fn, english_chunks):
        from packages.rag_core.verifier import verify_grounding

        result = verify_grounding(
            ["Se detectó un único oferente en el proceso."],
            english_chunks,
            threshold=0.6,
            method="gemini",
            embed_fn=fake_embed_fn,
        )
        assert result["sentences"][0]["supported"] is True
        assert result["sentences"][0]["best_chunk_id"] == "c1"
        assert result["grounding_ratio"] == 1.0

    def test_out_of_domain_sentence_not_supported(self, fake_embed_fn, english_chunks):
        from packages.rag_core.verifier import verify_grounding

        result = verify_grounding(
            ["La capital de Francia es París."],
            english_chunks,
            threshold=0.6,
            method="gemini",
            embed_fn=fake_embed_fn,
        )
        assert result["sentences"][0]["supported"] is False
        assert result["grounding_ratio"] == 0.0

    def test_mixed_sentences_ratio(self, fake_embed_fn, english_chunks):
        from packages.rag_core.verifier import verify_grounding

        result = verify_grounding(
            [
                "El plazo de presentación fue extremadamente corto.",
                "Las mejores cookies llevan chocolate.",
            ],
            english_chunks,
            threshold=0.6,
            method="gemini",
            embed_fn=fake_embed_fn,
        )
        supported = [s["supported"] for s in result["sentences"]]
        assert supported == [True, False]
        assert result["grounding_ratio"] == 0.5

    def test_empty_sentences(self, fake_embed_fn, english_chunks):
        from packages.rag_core.verifier import verify_grounding

        result = verify_grounding(
            [], english_chunks, threshold=0.6, method="gemini", embed_fn=fake_embed_fn
        )
        assert result["grounding_ratio"] == 0.0
        assert result["sentences"] == []

    def test_no_chunks(self, fake_embed_fn):
        from packages.rag_core.verifier import verify_grounding

        result = verify_grounding(
            ["Se detectó un único oferente."],
            [],
            threshold=0.6,
            method="gemini",
            embed_fn=fake_embed_fn,
        )
        assert result["sentences"][0]["supported"] is False
        assert result["grounding_ratio"] == 0.0

    def test_lexical_still_default_and_validates(self, english_chunks):
        from packages.rag_core.verifier import verify_grounding

        with pytest.raises(ValueError):
            verify_grounding(["x"], english_chunks, method="bm25")


class TestOutOfDomainForcedRefusal:
    """Regla 0: si el LLM se rehúsa por fuera de dominio, el refusal se fuerza
    deterministamente aunque el grounding puntúe alto (la frase de refusal
    menciona 'contratación pública' y se parece al corpus)."""

    def test_refusal_forced_even_with_high_grounding(self, english_chunks):
        from packages.rag_core.agent import OUT_OF_DOMAIN_REFUSAL, analyze

        def refusing_llm(query, chunks, system_prompt):
            return (
                "No puedo responder: la consulta está fuera del dominio de "
                "este documento (contratación pública). Requiere revisión humana."
            )

        result = analyze(
            "What is the capital of France?",
            generate_fn=refusing_llm,
            retrieved_chunks=english_chunks,
        )
        assert result["refusal"] == OUT_OF_DOMAIN_REFUSAL
        assert result["answer"] == OUT_OF_DOMAIN_REFUSAL
        assert result["citations"] == [], "un refusal no debe llevar citas"

    def test_domain_answer_not_flagged(self, english_chunks):
        from packages.rag_core.agent import analyze

        def domain_llm(query, chunks, system_prompt):
            return (
                "Single bid received for the tender. "
                "Short bidding period before the deadline. "
                "Requiere revisión humana."
            )

        result = analyze(
            "single bidder short deadline",
            generate_fn=domain_llm,
            retrieved_chunks=english_chunks,
            grounding_threshold=0.2,
        )
        assert result["refusal"] == ""
        assert result["citations"], "respuesta grounded debe llevar citas"
