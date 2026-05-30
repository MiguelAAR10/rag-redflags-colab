"""
Fase 6 pipeline runner — Qwen/Grounding/Citations evidence.

Simula 3 contratos de prueba con FAISS retrieval + minimal_analysis (sin Qwen
en local) y compara grounding_ratio por query.

Guarda reporte en progress/evidence/fase6-grounding-report.json
"""

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "packages"))

from rag_core.agent import analyze, _minimal_analysis
from rag_core.retrievers import route_family


SAMPLE_CONTRACTS = [
    (
        "contract_bid_rigging",
        "Un contrato de obra pública por 5M USD con solo un oferente "
        "y precios idénticos entre los dos únicos participantes. "
        "El plazo entre publicación y apertura fue de 3 días.",
    ),
    (
        "contract_delays",
        "Un contrato de servicios de consultoría con 18 meses de retraso "
        "en la entrega y pagos parciales sin hitos verificables. "
        "No hay evidencia de penalización por incumplimiento.",
    ),
    (
        "contract_clean",
        "Evaluación de un proceso de contratación estándar "
        "sin irregularidades aparentes, con múltiples oferentes "
        "y criterios de adjudicación transparentes.",
    ),
]


def run_phase6():
    results = {}

    for name, query in SAMPLE_CONTRACTS:
        family = route_family(query)

        try:
            from rag_core.retrievers import faiss_search, load_chunks

            chunks = load_chunks()
            candidates = faiss_search(query, k=5, chunks=chunks)
        except Exception as exc:
            results[name] = {"error": str(exc)}
            continue

        result = analyze(
            query,
            generate_fn=_minimal_analysis,
            retrieved_chunks=candidates,
            grounding_method="lexical",
        )

        results[name] = {
            "query": query[:120] + "..." if len(query) > 120 else query,
            "family": family,
            "num_candidates": len(candidates),
            "answer": result["answer"],
            "grounding_ratio": result["grounding_ratio"],
            "num_citations": len(result["citations"]),
            "num_sentences": len(result["sentences"]),
            "supported_sentences": sum(
                1 for s in result["sentences"] if s["supported"]
            ),
            "citations": [
                {
                    "sentence": c["sentence"][:80] + "..."
                    if len(c["sentence"]) > 80
                    else c["sentence"],
                    "indicator_code": c["indicator_code"],
                    "indicator_name": c["indicator_name"],
                    "page": f"{c['page_start']}-{c['page_end']}",
                }
                for c in result["citations"]
            ],
            "has_refusal": bool(result["refusal"]),
            "has_safe_language": "requiere revisión humana" in result["answer"].lower(),
        }

    report = {
        "phase": "fase6-qwen-grounding",
        "model": "Qwen2.5-3B-Instruct (simulado con _minimal_analysis)",
        "queries_tested": len(results),
        "results": results,
    }

    report_path = Path("progress/evidence/fase6-grounding-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Reporte guardado en {report_path}")
    for name, info in results.items():
        if "error" in info:
            print(f"\n{name}: ERROR {info['error']}")
        else:
            print(
                f"\n{name}: family={info['family']}, "
                f"grounding_ratio={info['grounding_ratio']}, "
                f"citations={info['num_citations']}, "
                f"safe_language={info['has_safe_language']}"
            )

    return report


if __name__ == "__main__":
    run_phase6()
