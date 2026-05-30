"""
Fase 5 pipeline runner — Reranker cross-encoder.

Compara: hybrid top-5 vs (hybrid top-20 + rerank top-5) en 3–5 queries.
Guarda reporte en progress/evidence/fase5-reranker-report.json
"""

import json
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "packages"))

from rag_core.rerankers import rerank, load_candidates_from_faiss


def run_phase5():
    test_queries = [
        "bid rigging during tender competition",
        "contract execution delays and payment issues",
        "award winner selection lowest price",
    ]

    results = {}

    for q in test_queries:
        t0 = time.time()

        try:
            candidates = load_candidates_from_faiss(q, k=20)
        except Exception as exc:
            results[q] = {"error": f"No se pudieron cargar candidatos: {exc}"}
            continue

        top5_hybrid = candidates[:5]

        try:
            reranked = rerank(q, candidates, top_n=5)
        except Exception as exc:
            results[q] = {
                "error": f"Reranker falló: {exc}",
                "hybrid_top5": [
                    {"chunk_id": c["chunk_id"], "family": c["family"], "score": c["score"]}
                    for c in top5_hybrid
                ],
            }
            continue

        results[q] = {
            "elapsed_ms": round((time.time() - t0) * 1000, 2),
            "num_candidates": len(candidates),
            "hybrid_top5": [
                {
                    "chunk_id": c["chunk_id"],
                    "family": c["family"],
                    "indicator_name": c.get("indicator_name"),
                    "score": round(c["score"], 4),
                }
                for c in top5_hybrid
            ],
            "reranked_top5": [
                {
                    "chunk_id": c["chunk_id"],
                    "family": c["family"],
                    "indicator_name": c.get("indicator_name"),
                    "score": round(c["score"], 4),
                    "rerank_score": round(c["rerank_score"], 4) if "rerank_score" in c else None,
                }
                for c in reranked
            ],
        }

    report = {
        "phase": "fase5-reranker",
        "model": "BAAI/bge-reranker-v2-m3",
        "queries_tested": len(test_queries),
        "results": results,
    }

    report_path = Path("progress/evidence/fase5-reranker-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Reporte guardado en {report_path}")
    for q, info in results.items():
        print(f"\nQuery: {q}")
        if "error" in info:
            print(f"  ERROR: {info['error']}")
        else:
            print(f"  hybrid top-5: {[c['chunk_id'] for c in info['hybrid_top5']]}")
            print(f"  reranked top-5: {[c['chunk_id'] for c in info['reranked_top5']]}")

    return report


if __name__ == "__main__":
    run_phase5()