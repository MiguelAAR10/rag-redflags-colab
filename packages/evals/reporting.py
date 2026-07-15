"""Persist reproducible, human-readable artifacts for the Colab evaluation."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _flatten_cases(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in report.get("items", []):
        rows.append(
            {
                "question_number": item.get("question_number"),
                "id": item.get("id"),
                "case_type": "answerable",
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "status": item.get("status", "ANSWER"),
                "abstain_reason": "",
                "generation_backend": item.get("generation_backend", ""),
                "duration_seconds": item.get("duration_seconds"),
                "grounding_ratio": item.get("grounding_ratio"),
                "faithfulness": item.get("faithfulness"),
                "answer_relevance": item.get("answer_relevance"),
                "context_relevance": item.get("context_relevance"),
                "expected_indicator_codes": _json_cell(
                    item.get("expected_indicator_codes", [])
                ),
                "expected_pages": _json_cell(item.get("expected_pages", [])),
                "retrieved_evidence": _json_cell(
                    item.get("retrieved_evidence", [])
                ),
                "citations": _json_cell(item.get("citations", [])),
                "security_result": "",
            }
        )

    for item in report.get("security", {}).get("items", []):
        security_ok = all(
            (
                item.get("status_match", False),
                item.get("reason_match", False),
                item.get("correction_match", False),
                not item.get("citation_leakage", False),
            )
        )
        rows.append(
            {
                "question_number": item.get("question_number"),
                "id": item.get("id"),
                "case_type": f"security:{item.get('trap_type', 'unknown')}",
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "status": item.get("actual_status", ""),
                "abstain_reason": item.get("actual_abstain_reason", ""),
                "generation_backend": item.get("generation_backend", ""),
                "duration_seconds": item.get("duration_seconds"),
                "grounding_ratio": item.get("grounding_ratio"),
                "faithfulness": "",
                "answer_relevance": "",
                "context_relevance": "",
                "expected_indicator_codes": _json_cell(
                    item.get("expected_indicator_codes", [])
                ),
                "expected_pages": _json_cell(item.get("expected_pages", [])),
                "retrieved_evidence": _json_cell(
                    item.get("retrieved_evidence", [])
                ),
                "citations": _json_cell(item.get("citations", [])),
                "security_result": "PASS" if security_ok else "REVIEW",
            }
        )

    return sorted(rows, key=lambda row: int(row.get("question_number") or 0))


def _metric_rows(report: Dict[str, Any]) -> Iterable[tuple[str, Any]]:
    yield "Faithfulness (11 respondibles)", report.get("mean_faithfulness")
    yield "Answer relevance (11 respondibles)", report.get("mean_answer_relevance")
    yield "Context relevance (11 respondibles)", report.get("mean_context_relevance")
    security = report.get("security", {})
    yield "Abstention accuracy", security.get("abstention_accuracy")
    yield "Reason accuracy", security.get("reason_accuracy")
    yield "False-premise accuracy", security.get("false_premise_accuracy")
    yield "Fuga de citas", security.get("citation_leakage_count")


def _render_html(report: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    execution = report.get("execution", {})
    metric_html = "".join(
        f"<tr><th>{html.escape(label)}</th><td>{html.escape(str(value))}</td></tr>"
        for label, value in _metric_rows(report)
    )
    execution_html = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in execution.items()
    )

    cases = []
    for row in rows:
        evidence = json.loads(row["retrieved_evidence"])
        citations = json.loads(row["citations"])
        evidence_html = "".join(
            "<li><strong>{code} · p.{page}</strong> — {excerpt}</li>".format(
                code=html.escape(str(item.get("Indicador", "—"))),
                page=html.escape(str(item.get("Página", "—"))),
                excerpt=html.escape(str(item.get("Extracto de evidencia", "—"))),
            )
            for item in evidence
        ) or "<li>No hay evidencia recuperada.</li>"
        citations_html = "".join(
            "<li>{sentence} — {source}, {code}, p.{page}</li>".format(
                sentence=html.escape(str(item.get("sentence", "—"))),
                source=html.escape(str(item.get("source_id") or "OCP 2024")),
                code=html.escape(str(item.get("indicator_code", "—"))),
                page=html.escape(str(item.get("page_start", "—"))),
            )
            for item in citations
        ) or "<li>Sin citas emitidas.</li>"
        cases.append(
            """
            <article>
              <h3>Pregunta {number}/15 · {case_id}</h3>
              <p><strong>Tipo:</strong> {case_type} · <strong>Estado:</strong> {status}</p>
              <p><strong>Pregunta:</strong> {question}</p>
              <p><strong>Respuesta:</strong></p><pre>{answer}</pre>
              <p><strong>Backend:</strong> {backend} · <strong>Duración:</strong> {duration}s · <strong>Grounding:</strong> {grounding}</p>
              <p><strong>Evidencia recuperada:</strong></p><ul>{evidence}</ul>
              <p><strong>Citas por afirmación:</strong></p><ul>{citations}</ul>
            </article>
            """.format(
                number=html.escape(str(row["question_number"])),
                case_id=html.escape(str(row["id"])),
                case_type=html.escape(str(row["case_type"])),
                status=html.escape(str(row["status"])),
                question=html.escape(str(row["question"])),
                answer=html.escape(str(row["answer"])),
                backend=html.escape(str(row["generation_backend"])),
                duration=html.escape(str(row["duration_seconds"])),
                grounding=html.escape(str(row["grounding_ratio"])),
                evidence=evidence_html,
                citations=citations_html,
            )
        )

    return """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Reporte RAG académico</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#172033}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}th,td{{border:1px solid #ccd3df;padding:8px;text-align:left}}
article{{border-top:2px solid #d7deea;padding:20px 0}}pre{{white-space:pre-wrap;background:#f5f7fa;padding:12px}}
.notice{{background:#fff7d6;border-left:5px solid #e0a800;padding:12px}}
</style></head><body>
<h1>Evaluación reproducible del RAG de señales de riesgo</h1>
<p class="notice">Las salidas son señales de riesgo potenciales, no prueban corrupción ni ilegalidad y requieren revisión humana.</p>
<h2>Ejecución</h2><table>{execution}</table>
<h2>Resumen de calidad y seguridad</h2><table>{metrics}</table>
<h2>Detalle de los 15 casos</h2>{cases}
</body></html>""".format(
        execution=execution_html,
        metrics=metric_html,
        cases="".join(cases),
    )


def export_report_bundle(
    report: Dict[str, Any], output_dir: str | Path
) -> Dict[str, str]:
    """Write JSON, a flat CSV and a standalone HTML report.

    The official neural report must be explicit about the backend and must not
    contain fallback generations. Offline baselines can still be exported, but
    are not accepted when ``phase`` contains ``qwen-neural``.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _flatten_cases(report)

    if report.get("phase") == "goldset-v2-qwen-neural-colab":
        if report.get("execution", {}).get("fallback_count") != 0:
            raise ValueError("El reporte neural no puede contener fallbacks")
        if len(rows) != 15:
            raise ValueError(f"El reporte neural requiere 15 casos; recibió {len(rows)}")

    json_path = output_dir / "ragas-report.json"
    csv_path = output_dir / "ragas-cases.csv"
    html_path = output_dir / "ragas-report.html"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    html_path.write_text(_render_html(report, rows), encoding="utf-8")
    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "html": str(html_path),
    }
