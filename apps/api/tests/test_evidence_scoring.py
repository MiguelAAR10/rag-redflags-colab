"""Tests for the deterministic agents that don't touch the LLM."""

from __future__ import annotations

from app.services.evidence import critique
from app.services.scoring import score


SAMPLE_ANSWER = (
    "### Evaluación preliminar\n"
    "Riesgo general: Medio\n\n"
    "### Señales de riesgo identificadas\n"
    "1. Señal: Plazo de entrega muy corto\n"
    "   - Evidencia del fragmento: 'El plazo es de 5 días hábiles.'\n"
    "   - Por qué importa: Plazos cortos reducen la competencia.\n"
    "   - Sustento recuperado: (Indicador: Bidding period too short, R010, p.10-12)\n\n"
    "2. Señal: Especificación técnica subjetiva\n"
    "   - Evidencia del fragmento: 'marca sugerida sin equivalente'.\n"
    "   - Por qué importa: Restringe la competencia.\n"
    "   - Sustento recuperado: (Indicador: Restrictive technical spec, R022, p.20-21)\n\n"
    "### Conclusión\n"
    "No se determina corrupción; son señales de riesgo potenciales. Requiere revisión humana."
)


SAMPLE_CITATIONS = [
    {
        "sentence": "Plazo corto.",
        "chunk_id": "c1",
        "indicator_code": "R010",
        "indicator_name": "Bidding period too short",
        "page_start": 10,
        "page_end": 12,
    },
    {
        "sentence": "Especificación restrictiva.",
        "chunk_id": "c2",
        "indicator_code": "R022",
        "indicator_name": "Restrictive technical specification",
        "page_start": 20,
        "page_end": 21,
    },
]


def test_critique_accepts_findings_with_citations():
    analysis = {
        "answer": SAMPLE_ANSWER,
        "sentences": [],
        "citations": SAMPLE_CITATIONS,
        "grounding_ratio": 0.8,
        "refusal": "",
    }
    result = critique(analysis, grounding_threshold=0.25)

    assert result.evidence_status == "sufficient"
    assert result.accepted_count == 2
    assert result.rejected_count == 0
    assert result.accepted_findings[0].citation
    assert result.accepted_findings[0].accepted


def test_critique_rejects_when_no_citations():
    analysis = {
        "answer": SAMPLE_ANSWER,
        "sentences": [],
        "citations": [],
        "grounding_ratio": 0.8,
        "refusal": "",
    }
    result = critique(analysis, grounding_threshold=0.25)
    assert result.evidence_status == "weak"
    assert result.accepted_count == 0


def test_critique_rejects_when_grounding_low():
    analysis = {
        "answer": SAMPLE_ANSWER,
        "sentences": [],
        "citations": SAMPLE_CITATIONS,
        "grounding_ratio": 0.10,
        "refusal": "",
    }
    result = critique(analysis, grounding_threshold=0.25)
    assert result.evidence_status == "weak"
    assert result.accepted_count == 0


def test_critique_marks_insufficient_on_refusal():
    analysis = {
        "answer": "",
        "sentences": [],
        "citations": [],
        "grounding_ratio": 0.0,
        "refusal": "No hay evidencia suficiente.",
    }
    result = critique(analysis, grounding_threshold=0.25)
    assert result.evidence_status == "insufficient"


def test_scoring_low_when_no_findings():
    crit = critique(
        {
            "answer": SAMPLE_ANSWER,
            "sentences": [],
            "citations": SAMPLE_CITATIONS,
            "grounding_ratio": 0.8,
            "refusal": "",
        },
        grounding_threshold=0.25,
    )
    # Force zero accepted to test scoring independently.
    crit.accepted_findings = []
    crit.rejected_findings = []
    verdict = score(crit)
    assert verdict.level == "Bajo"


def test_scoring_alto_on_high_severity_finding():
    crit = critique(
        {
            "answer": SAMPLE_ANSWER,
            "sentences": [],
            "citations": SAMPLE_CITATIONS,
            "grounding_ratio": 0.8,
            "refusal": "",
        },
        grounding_threshold=0.25,
    )
    crit.accepted_findings[0].severity = "Alto"
    verdict = score(crit)
    assert verdict.level == "Alto"


def test_scoring_insufficient_when_critique_insufficient():
    crit = critique(
        {
            "answer": "",
            "sentences": [],
            "citations": [],
            "grounding_ratio": 0.0,
            "refusal": "No hay evidencia suficiente.",
        },
        grounding_threshold=0.25,
    )
    verdict = score(crit)
    assert verdict.level == "Evidencia insuficiente"