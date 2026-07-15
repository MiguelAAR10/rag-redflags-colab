import json
from pathlib import Path

import pytest

from packages.evals.reporting import export_report_bundle


def _report():
    answerable = [
        {
            "id": f"a-{number}",
            "question_number": number,
            "question": f"Pregunta {number}",
            "answer": "Señal potencial; requiere revisión humana.",
            "status": "ANSWER",
            "generation_backend": "qwen",
            "duration_seconds": 1.0,
            "grounding_ratio": 1.0,
            "faithfulness": 1.0,
            "answer_relevance": 1.0,
            "context_relevance": 1.0,
            "retrieved_evidence": [
                {"Indicador": "R001", "Página": 24, "Extracto de evidencia": "texto"}
            ],
            "citations": [
                {"sentence": "Señal potencial.", "indicator_code": "R001", "page_start": 24}
            ],
        }
        for number in range(1, 12)
    ]
    security = [
        {
            "id": f"s-{number}",
            "question_number": number,
            "question": f"Pregunta {number}",
            "answer": "No hay evidencia suficiente; requiere revisión humana.",
            "actual_status": "ABSTAIN",
            "actual_abstain_reason": "OUT_OF_DOMAIN",
            "trap_type": "out_of_domain",
            "generation_backend": "qwen",
            "duration_seconds": 1.0,
            "grounding_ratio": 0.0,
            "status_match": True,
            "reason_match": True,
            "correction_match": True,
            "citation_leakage": False,
            "retrieved_evidence": [],
        }
        for number in range(12, 16)
    ]
    return {
        "phase": "goldset-v2-qwen-neural-colab",
        "n": 15,
        "n_answerable": 11,
        "mean_faithfulness": 1.0,
        "mean_answer_relevance": 1.0,
        "mean_context_relevance": 1.0,
        "execution": {"generation_backend": "qwen", "fallback_count": 0},
        "items": answerable,
        "security": {
            "items": security,
            "abstention_accuracy": 1.0,
            "reason_accuracy": 1.0,
            "false_premise_accuracy": 1.0,
            "citation_leakage_count": 0,
        },
    }


def test_export_report_bundle_writes_machine_and_human_artifacts(tmp_path: Path):
    paths = export_report_bundle(_report(), tmp_path)

    assert set(paths) == {"json", "csv", "html"}
    assert json.loads((tmp_path / "ragas-report.json").read_text())["n"] == 15
    csv_text = (tmp_path / "ragas-cases.csv").read_text()
    assert csv_text.count("\n") == 16
    assert "generation_backend" in csv_text
    assert "citations" in csv_text
    html_text = (tmp_path / "ragas-report.html").read_text()
    assert "Detalle de los 15 casos" in html_text
    assert "Citas por afirmación" in html_text
    assert "requieren revisión humana" in html_text


def test_neural_report_rejects_fallback(tmp_path: Path):
    report = _report()
    report["execution"]["fallback_count"] = 1

    with pytest.raises(ValueError, match="no puede contener fallbacks"):
        export_report_bundle(report, tmp_path)
