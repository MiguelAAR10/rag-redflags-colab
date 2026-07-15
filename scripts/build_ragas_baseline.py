#!/usr/bin/env python3
"""Build the explicit offline contract baseline for the versioned RAGAS report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.evals.ragas_metrics import evaluate_ragas


GOLDSET = ROOT / "data" / "eval" / "goldset.jsonl"
CHUNKS = ROOT / "data" / "processed" / "redflags_chunks.jsonl"
OUTPUT = ROOT / "progress" / "evidence" / "ragas-report.json"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as jsonl_file:
        return [json.loads(line) for line in jsonl_file if line.strip()]


def main() -> None:
    gold = load_jsonl(GOLDSET)
    chunks = load_jsonl(CHUNKS)
    chunks_by_code: dict[str, list[str]] = {}
    for chunk in chunks:
        code = chunk.get("indicator_code")
        text = str(chunk.get("text") or "").strip()
        if code and text:
            chunks_by_code.setdefault(code, []).append(text)

    answerable = [item for item in gold if not item.get("trap")]
    security = [item for item in gold if item.get("trap")]
    metric_items = []
    for item in answerable:
        contexts = []
        for code in item["relevant_indicator_codes"]:
            contexts.extend(chunks_by_code.get(code, [])[:1])
        metric_items.append(
            {
                "question": item["query"],
                "answer": item["expected_answer"],
                "contexts": contexts,
                "refusal": False,
            }
        )

    report = evaluate_ragas(metric_items)
    for row, item in zip(report["items"], answerable):
        row["id"] = item["id"]
        row["expected_pages"] = item["expected_pages"]
    report["n_answerable"] = report.pop("n")
    report["n"] = len(gold)
    report["traps"] = len(security)
    report["security"] = {
        "n": len(security),
        "status": "NOT_RUN_OFFLINE",
        "abstention_accuracy": None,
        "reason_accuracy": None,
        "citation_leakage_count": None,
        "items": [
            {
                "id": item["id"],
                "trap_type": item["trap_type"],
                "expected_status": item["expected_status"],
                "expected_abstain_reason": item.get("expected_abstain_reason", ""),
            }
            for item in security
        ],
    }
    report.update(
        {
            "phase": "goldset-v2-offline-contract-baseline",
            "metric_set": "Proxies lexicos locales inspirados en RAGAS",
            "metric_scope": "Solo 11 preguntas respondibles; seguridad separada",
            "paper_ref": "Es et al. 2025, arXiv:2309.15217",
            "note": (
                "Baseline OFFLINE de contrato: usa respuestas esperadas y chunks "
                "seleccionados por los codigos gold. No mide el pipeline neural. "
                "El notebook debe reemplazarlo con Qwen + retrieval real en Colab."
            ),
        }
    )
    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Reporte baseline escrito en {OUTPUT}")


if __name__ == "__main__":
    main()
