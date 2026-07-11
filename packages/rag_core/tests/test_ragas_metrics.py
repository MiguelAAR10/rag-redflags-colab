"""
GATE de aceptación — Fase 13: Métricas RAGAS locales deterministas.

Implementa tests para las 4 funciones mínimas exigidas por
`progress/NEXT_ACTION.md` y `specs/004-redflags-rag.md` (RAGAS local):

  - faithfulness(answer, contexts) -> float in [0, 1]
  - answer_relevance(question, answer) -> float in [0, 1]
  - context_relevance(question, contexts) -> float in [0, 1]
  - evaluate_ragas(items) -> dict

Restricciones verificadas:
  - Sin APIs externas, sin dependencias pesadas.
  - Maneja respuesta vacía, contexto vacío, refusal, pregunta trampa.
  - Determinista: mismo input → mismo output.
  - Todos los retornos son float en [0, 1] (sin NaN, sin >1, sin <0).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
GOLDSET = REPO / "data" / "eval" / "goldset.jsonl"
ABSTENTION_SET = REPO / "data" / "eval" / "abstention_set.jsonl"
# Marcadores inequívocos (alineados con packages/evals/ragas_metrics.py).
# "requiere revisión humana" NO es marcador de refusal: la regla 6 del
# SYSTEM_PROMPT la exige en TODAS las respuestas válidas, así que usarla
# como marcador hacía answer_relevance=0.0 para respuestas correctas
# (bug corregido tras auditoría externa 2026-07-11).
_REFUSAL_MARKERS = (
    "no hay evidencia suficiente",
    "insufficient evidence",
    "no puedo responder",
    "fuera del dominio",
    "cannot answer",
    "out of domain",
)


# --------------------------------------------------------------------------- #
# Helpers compartidos
# --------------------------------------------------------------------------- #


REFUSAL_TEXT_ES = (
    "No hay evidencia suficiente en los documentos recuperados "
    "para emitir observaciones fundamentadas. Requiere revisión humana."
)
REFUSAL_TEXT_EN = (
    "There is insufficient evidence in the retrieved documents "
    "to issue grounded observations. Requires human review."
)


def _is_unit_float(x: float) -> bool:
    """True si x es float finito en [0, 1]."""
    return (
        isinstance(x, float)
        and not math.isnan(x)
        and not math.isinf(x)
        and 0.0 <= x <= 1.0
    )


# --------------------------------------------------------------------------- #
# Tests de faithfulness
# --------------------------------------------------------------------------- #


class TestFaithfulness:
    def test_returns_float_in_unit_interval(self):
        from packages.evals.ragas_metrics import faithfulness

        answer = "El contrato se adjudicó por excepción."
        contexts = ["El contrato se adjudicó por excepción según la ley."]
        score = faithfulness(answer, contexts)
        assert _is_unit_float(score)

    def test_empty_answer_returns_unit_float(self):
        from packages.evals.ragas_metrics import faithfulness

        score = faithfulness("", ["texto de contexto"])
        assert _is_unit_float(score)

    def test_empty_contexts_returns_unit_float(self):
        from packages.evals.ragas_metrics import faithfulness

        score = faithfulness("respuesta", [])
        assert _is_unit_float(score)

    def test_both_empty_returns_unit_float(self):
        from packages.evals.ragas_metrics import faithfulness

        score = faithfulness("", [])
        assert _is_unit_float(score)

    def test_full_support_high_score(self):
        from packages.evals.ragas_metrics import faithfulness

        answer = (
            "El contrato se adjudicó por excepción. "
            "El oferente único fue rechazado por incumplimiento. "
            "Se requiere revisión humana."
        )
        contexts = [
            "El contrato se adjudicó por excepción según la ley.",
            "El oferente único fue rechazado por incumplimiento técnico.",
            "Se requiere revisión humana para validar el procedimiento.",
        ]
        score = faithfulness(answer, contexts)
        assert score >= 0.9, f"score={score}, esperaba >=0.9 con soporte pleno"

    def test_no_support_low_score(self):
        from packages.evals.ragas_metrics import faithfulness

        answer = (
            "El presidente renunció. La economía creció 10%. "
            "Hubo un terremoto ayer."
        )
        contexts = [
            "El contrato se adjudicó por excepción según la ley.",
            "El oferente único fue rechazado por incumplimiento técnico.",
        ]
        score = faithfulness(answer, contexts)
        assert score <= 0.2, f"score={score}, esperaba <=0.2 sin soporte"

    def test_refusal_answer_low_score(self):
        from packages.evals.ragas_metrics import faithfulness

        score = faithfulness(REFUSAL_TEXT_ES, ["texto arbitrario xyz"])
        assert _is_unit_float(score)
        assert score <= 0.3, f"score={score}, esperaba <=0.3 para refusal"

    def test_partial_support_middle_score(self):
        from packages.evals.ragas_metrics import faithfulness

        answer = (
            "El contrato se adjudicó por excepción. "
            "El presidente anunció una nueva reforma educativa."
        )
        contexts = ["El contrato se adjudicó por excepción según la ley."]
        score = faithfulness(answer, contexts)
        assert 0.2 <= score <= 0.8, f"score={score}, esperaba intermedio"

    def test_deterministic(self):
        from packages.evals.ragas_metrics import faithfulness

        answer = "Frase con tokens compartidos uno dos tres."
        contexts = ["Contexto uno dos tres cuatro cinco seis."]
        s1 = faithfulness(answer, contexts)
        s2 = faithfulness(answer, contexts)
        assert s1 == s2

    def test_whitespace_only_answer(self):
        from packages.evals.ragas_metrics import faithfulness

        score = faithfulness("   \n\t  ", ["texto válido"])
        assert _is_unit_float(score)


# --------------------------------------------------------------------------- #
# Tests de answer_relevance
# --------------------------------------------------------------------------- #


class TestAnswerRelevance:
    def test_returns_float_in_unit_interval(self):
        from packages.evals.ragas_metrics import answer_relevance

        score = answer_relevance(
            "¿Cuáles son las señales de riesgo en el contrato?",
            "Las señales de riesgo incluyen precios inflados.",
        )
        assert _is_unit_float(score)

    def test_empty_question_returns_unit_float(self):
        from packages.evals.ragas_metrics import answer_relevance

        score = answer_relevance("", "respuesta cualquiera")
        assert _is_unit_float(score)

    def test_empty_answer_returns_unit_float(self):
        from packages.evals.ragas_metrics import answer_relevance

        score = answer_relevance("¿Pregunta?", "")
        assert _is_unit_float(score)

    def test_both_empty_returns_unit_float(self):
        from packages.evals.ragas_metrics import answer_relevance

        score = answer_relevance("", "")
        assert _is_unit_float(score)

    def test_high_overlap_high_score(self):
        from packages.evals.ragas_metrics import answer_relevance

        question = "¿Cuáles son las señales de riesgo en contratación pública?"
        answer = (
            "Las señales de riesgo en contratación pública incluyen "
            "precios inflados, oferente único y plazos cortos."
        )
        score = answer_relevance(question, answer)
        assert score >= 0.5, f"score={score}, esperaba >=0.5 con alta coincidencia"

    def test_no_overlap_low_score(self):
        from packages.evals.ragas_metrics import answer_relevance

        question = "¿Cuáles son las señales de riesgo en contratación pública?"
        answer = "El gato subió al tejado y maulló tres veces."
        score = answer_relevance(question, answer)
        assert score <= 0.2, f"score={score}, esperaba <=0.2 sin coincidencia"

    def test_trap_question_low_score(self):
        """Pregunta trampa: incoherente / sin anclaje semántico."""
        from packages.evals.ragas_metrics import answer_relevance

        question = "¿Cuál es el sentido de la vida según un triángulo azul?"
        answer = "Respuesta tangencial con palabras sueltas."
        score = answer_relevance(question, answer)
        assert _is_unit_float(score)
        assert score <= 0.3, f"score={score}, esperaba <=0.3 para trampa"

    def test_refusal_answer_low_score(self):
        from packages.evals.ragas_metrics import answer_relevance

        question = "¿Hay corrupción en este contrato?"
        score = answer_relevance(question, REFUSAL_TEXT_ES)
        assert _is_unit_float(score)
        assert score <= 0.3

    def test_deterministic(self):
        from packages.evals.ragas_metrics import answer_relevance

        q = "pregunta uno dos tres"
        a = "respuesta uno dos tres cuatro"
        s1 = answer_relevance(q, a)
        s2 = answer_relevance(q, a)
        assert s1 == s2


# --------------------------------------------------------------------------- #
# Tests de context_relevance
# --------------------------------------------------------------------------- #


class TestContextRelevance:
    def test_returns_float_in_unit_interval(self):
        from packages.evals.ragas_metrics import context_relevance

        contexts = ["Texto sobre contratación pública y excepciones."]
        score = context_relevance(
            "¿Qué es una excepción en contratación?", contexts
        )
        assert _is_unit_float(score)

    def test_empty_question_returns_unit_float(self):
        from packages.evals.ragas_metrics import context_relevance

        score = context_relevance("", ["texto válido"])
        assert _is_unit_float(score)

    def test_empty_contexts_returns_unit_float(self):
        from packages.evals.ragas_metrics import context_relevance

        score = context_relevance("¿Pregunta?", [])
        assert _is_unit_float(score)

    def test_both_empty_returns_unit_float(self):
        from packages.evals.ragas_metrics import context_relevance

        score = context_relevance("", [])
        assert _is_unit_float(score)

    def test_all_relevant_high_score(self):
        from packages.evals.ragas_metrics import context_relevance

        question = "¿Cuáles son las señales de riesgo en contratación?"
        contexts = [
            "Las señales de riesgo en contratación incluyen excepciones.",
            "Más señales de riesgo: oferente único, plazos cortos.",
            "Documento adicional sobre contratación y sus riesgos.",
        ]
        score = context_relevance(question, contexts)
        assert score >= 0.7, f"score={score}, esperaba >=0.7 con alta relevancia"

    def test_none_relevant_low_score(self):
        from packages.evals.ragas_metrics import context_relevance

        question = "¿Cuáles son las señales de riesgo en contratación?"
        contexts = [
            "El gato subió al tejado y maulló tres veces.",
            "Receta de cocina: mezclar harina, agua y sal.",
        ]
        score = context_relevance(question, contexts)
        assert score <= 0.2, f"score={score}, esperaba <=0.2 sin relevancia"

    def test_mixed_relevance_middle_score(self):
        from packages.evals.ragas_metrics import context_relevance

        question = "¿Cuáles son las señales de riesgo en contratación?"
        contexts = [
            "Las señales de riesgo en contratación incluyen excepciones.",
            "Receta de cocina: mezclar harina, agua y sal.",
        ]
        score = context_relevance(question, contexts)
        assert 0.1 <= score <= 0.9, f"score={score}, esperaba intermedio"

    def test_trap_question_safe(self):
        from packages.evals.ragas_metrics import context_relevance

        question = "¿Cuál es el sentido de la vida según un triángulo azul?"
        contexts = ["Contexto normal sobre contratación pública."]
        score = context_relevance(question, contexts)
        assert _is_unit_float(score)

    def test_deterministic(self):
        from packages.evals.ragas_metrics import context_relevance

        q = "pregunta uno dos tres"
        c = ["uno dos tres cuatro cinco", "seis siete ocho nueve diez"]
        s1 = context_relevance(q, c)
        s2 = context_relevance(q, c)
        assert s1 == s2


# --------------------------------------------------------------------------- #
# Tests de evaluate_ragas
# --------------------------------------------------------------------------- #


class TestEvaluateRagas:
    def test_returns_dict(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        out = evaluate_ragas([])
        assert isinstance(out, dict)

    def test_empty_items_returns_zeros(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        out = evaluate_ragas([])
        assert out.get("n") == 0
        assert out.get("mean_faithfulness") == 0.0
        assert out.get("mean_answer_relevance") == 0.0
        assert out.get("mean_context_relevance") == 0.0

    def test_single_item_returns_aggregates(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {
                "question": "¿Señales de riesgo en contratación?",
                "answer": "Las señales de riesgo en contratación son excepciones.",
                "contexts": ["Las señales de riesgo en contratación incluyen excepciones."],
            }
        ]
        out = evaluate_ragas(items)
        assert out["n"] == 1
        assert _is_unit_float(out["mean_faithfulness"])
        assert _is_unit_float(out["mean_answer_relevance"])
        assert _is_unit_float(out["mean_context_relevance"])
        assert "items" in out
        assert len(out["items"]) == 1

    def test_multiple_items_aggregate_means(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {
                "question": "q1 palabras compartidas",
                "answer": "r1 palabras compartidas relevantes",
                "contexts": ["c1 palabras compartidas relevantes aqui"],
            },
            {
                "question": "q2 palabras compartidas",
                "answer": "r2 palabras compartidas relevantes",
                "contexts": ["c2 palabras compartidas relevantes aqui"],
            },
            {
                "question": "q3 totalmente diferente",
                "answer": "r3 totalmente diferente",
                "contexts": ["c3 totalmente diferente contenido"],
            },
        ]
        out = evaluate_ragas(items)
        assert out["n"] == 3
        assert _is_unit_float(out["mean_faithfulness"])
        assert _is_unit_float(out["mean_answer_relevance"])
        assert _is_unit_float(out["mean_context_relevance"])
        # Cada item debe tener sus 3 métricas en [0,1]
        for item in out["items"]:
            assert _is_unit_float(item["faithfulness"])
            assert _is_unit_float(item["answer_relevance"])
            assert _is_unit_float(item["context_relevance"])

    def test_handles_refusal_item(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {
                "question": "¿Cuál es la señal de riesgo?",
                "answer": REFUSAL_TEXT_ES,
                "contexts": ["Contexto sobre contratación pública."],
            }
        ]
        out = evaluate_ragas(items)
        assert out["n"] == 1
        assert _is_unit_float(out["mean_faithfulness"])
        assert _is_unit_float(out["mean_answer_relevance"])
        assert _is_unit_float(out["mean_context_relevance"])

    def test_handles_trap_question_item(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {
                "question": "¿Cuál es el sentido de la vida según un triángulo azul?",
                "answer": "No tengo información al respecto.",
                "contexts": ["Las señales de riesgo en contratación son excepciones."],
            }
        ]
        out = evaluate_ragas(items)
        assert out["n"] == 1
        assert _is_unit_float(out["mean_faithfulness"])
        assert _is_unit_float(out["mean_answer_relevance"])
        assert _is_unit_float(out["mean_context_relevance"])

    def test_handles_empty_fields_gracefully(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {"question": "", "answer": "", "contexts": []},
            {"question": "¿Algo?", "answer": "", "contexts": []},
            {"question": "", "answer": "Algo", "contexts": ["ctx"]},
        ]
        out = evaluate_ragas(items)
        assert out["n"] == 3
        assert _is_unit_float(out["mean_faithfulness"])
        assert _is_unit_float(out["mean_answer_relevance"])
        assert _is_unit_float(out["mean_context_relevance"])

    def test_deterministic_aggregate(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {
                "question": "pregunta",
                "answer": "respuesta con tokens compartidos",
                "contexts": ["contexto con tokens compartidos relevantes"],
            }
        ]
        out1 = evaluate_ragas(items)
        out2 = evaluate_ragas(items)
        assert out1["mean_faithfulness"] == out2["mean_faithfulness"]
        assert out1["mean_answer_relevance"] == out2["mean_answer_relevance"]
        assert out1["mean_context_relevance"] == out2["mean_context_relevance"]

    def test_output_keys_present(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        out = evaluate_ragas(
            [
                {
                    "question": "q",
                    "answer": "a",
                    "contexts": ["c"],
                }
            ]
        )
        for key in (
            "n",
            "mean_faithfulness",
            "mean_answer_relevance",
            "mean_context_relevance",
            "items",
        ):
            assert key in out, f"falta clave {key!r} en salida de evaluate_ragas"


# --------------------------------------------------------------------------- #
# Tests del gold set de evaluación (Fase 14)
# --------------------------------------------------------------------------- #


class TestGoldsetEval:
    """El set de evaluación RAGAS debe tener 10-15 ítems y >=2 trampas."""

    def _load(self):
        if not GOLDSET.exists():
            pytest.skip(f"goldset no encontrado: {GOLDSET}")
        items = []
        for line in GOLDSET.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                items.append(json.loads(line))
        return items

    def test_goldset_has_at_least_15_items(self):
        items = self._load()
        assert len(items) >= 15, f"goldset tiene {len(items)} ítems, se requieren >=15"

    def test_goldset_within_rubric_range(self):
        items = self._load()
        assert 10 <= len(items) <= 15, "la rúbrica pide entre 10 y 15 preguntas"

    def test_goldset_has_at_least_two_traps(self):
        items = self._load()
        traps = [it for it in items if it.get("trap") is True]
        assert len(traps) >= 2, f"se requieren >=2 preguntas trampa, hay {len(traps)}"

    def test_traps_expect_refusal_answer(self):
        items = self._load()
        traps = [it for it in items if it.get("trap") is True]
        for t in traps:
            expected = (t.get("expected_answer") or "").lower()
            assert any(m in expected for m in _REFUSAL_MARKERS), (
                f"la trampa {t.get('query')!r} debe esperar un refusal seguro"
            )

    def test_every_item_has_query(self):
        items = self._load()
        for it in items:
            assert it.get("query"), "todo ítem del goldset debe tener 'query'"

# --------------------------------------------------------------------------- #
# Regresión del bug de refusal (auditoría externa 2026-07-11)
# --------------------------------------------------------------------------- #


class TestRefusalBugRegression:
    """La coletilla obligatoria 'Requiere revisión humana.' (regla 6 del
    SYSTEM_PROMPT) NO debe clasificar una respuesta válida como refusal."""

    VALID_ANSWER = (
        "El contrato presenta una señal de riesgo por oferente único "
        "según el indicador R018 de la guía OCP. Requiere revisión humana."
    )

    def test_valid_answer_with_mandatory_tail_is_not_refusal(self):
        from packages.evals.ragas_metrics import _is_refusal

        assert _is_refusal(self.VALID_ANSWER) is False

    def test_valid_answer_scores_above_zero(self):
        from packages.evals.ragas_metrics import answer_relevance

        question = "¿Qué señal de riesgo presenta un contrato con oferente único?"
        score = answer_relevance(question, self.VALID_ANSWER)
        assert score > 0.0, (
            "una respuesta válida que cumple la regla 6 no puede puntuar 0"
        )

    def test_explicit_refusal_flag_is_authoritative(self):
        from packages.evals.ragas_metrics import answer_relevance

        question = "¿Qué señal de riesgo presenta este contrato?"
        # Señal explícita True fuerza 0 aunque el texto parezca respuesta
        assert answer_relevance(question, self.VALID_ANSWER, refusal=True) == 0.0
        # Señal explícita False desactiva el fallback léxico
        refusal_looking = "No hay evidencia suficiente sobre la señal de riesgo del contrato."
        assert answer_relevance(question, refusal_looking, refusal=False) > 0.0

    def test_evaluate_ragas_honors_item_refusal_flag(self):
        from packages.evals.ragas_metrics import evaluate_ragas

        items = [
            {
                "question": "¿Qué señal de riesgo hay con oferente único?",
                "answer": self.VALID_ANSWER,
                "contexts": ["Single bid received indicator R018."],
                "refusal": False,
            }
        ]
        out = evaluate_ragas(items)
        assert out["items"][0]["refusal"] is False
        assert out["items"][0]["answer_relevance"] > 0.0

    def test_out_of_domain_refusal_still_detected(self):
        from packages.evals.ragas_metrics import _is_refusal

        assert _is_refusal(
            "No puedo responder: la consulta está fuera del dominio de este "
            "documento (contratación pública). Requiere revisión humana."
        ) is True


class TestAbstentionSet:
    """Schema del abstention set (tipos A/B/C de la auditoría 2026-07-11)."""

    def _load(self):
        with open(ABSTENTION_SET, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_has_three_trap_types(self):
        items = self._load()
        types = {it["trap_type"] for it in items}
        assert types == {
            "out_of_domain",
            "in_domain_insufficient_evidence",
            "false_premise",
        }

    def test_every_item_has_expected_status(self):
        for it in self._load():
            assert it.get("expected_status") in ("ABSTAIN", "ANSWER")
            assert it.get("expected_abstain_reason")
            assert it.get("query") and it.get("rationale")

    def test_at_least_two_per_type(self):
        from collections import Counter

        counts = Counter(it["trap_type"] for it in self._load())
        for trap_type, n in counts.items():
            assert n >= 2, f"{trap_type} necesita >=2 casos, tiene {n}"


class TestAnalyzeAbstentionTaxonomy:
    """analyze() expone status/abstain_reason estructurados (P0 auditoría)."""

    def test_out_of_domain_taxonomy(self):
        from packages.rag_core.agent import analyze

        def refusing_llm(query, chunks, system_prompt):
            return (
                "No puedo responder: la consulta está fuera del dominio de "
                "este documento (contratación pública). Requiere revisión humana."
            )

        result = analyze(
            "Who won the World Cup?",
            generate_fn=refusing_llm,
            retrieved_chunks=[{"chunk_id": "c1", "text": "single bid indicator"}],
        )
        assert result["status"] == "ABSTAIN"
        assert result["abstain_reason"] == "OUT_OF_DOMAIN"

    def test_insufficient_evidence_taxonomy(self):
        from packages.rag_core.agent import analyze

        def ungrounded_llm(query, chunks, system_prompt):
            return "Afirmación sin relación alguna con el corpus recuperado."

        result = analyze(
            "¿Qué funcionario recibió un soborno?",
            generate_fn=ungrounded_llm,
            retrieved_chunks=[{"chunk_id": "c1", "text": "single bid indicator"}],
            grounding_threshold=0.9,
        )
        assert result["status"] == "ABSTAIN"
        assert result["abstain_reason"] == "INSUFFICIENT_EVIDENCE"

    def test_answer_taxonomy(self):
        from packages.rag_core.agent import analyze

        def grounded_llm(query, chunks, system_prompt):
            return "Single bid indicator detected. Requiere revisión humana."

        result = analyze(
            "single bidder",
            generate_fn=grounded_llm,
            retrieved_chunks=[
                {"chunk_id": "c1", "text": "Single bid indicator detected for tender."}
            ],
            grounding_threshold=0.2,
        )
        assert result["status"] == "ANSWER"
        assert result["abstain_reason"] == ""
