"""
Fase 4 pipeline runner — Retrieval híbrido + router de familias.

Demuestra:
- route_family sobre consultas de ejemplo.
- faiss_search real (si índice existe).
- hybrid_search (si BM25 está disponible).

Guarda reporte en progress/evidence/fase4-retrieval-report.json
"""

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages"))

import numpy as np

from rag_core.retrievers import (
    build_bm25,
    faiss_search,
    hybrid_search,
    load_chunks,
    route_family,
)


def run_phase4():
    chunks = load_chunks()
    print(f"Chunks cargados: {len(chunks)}")

    # ------------------------------------------------------------------ #
    # 1. Router de familias (determinista, no requiere modelo)
    # ------------------------------------------------------------------ #
    test_queries = [
        "budget planning and needs assessment",
        "bid rigging during tender competition",
        "award winner selection lowest price",
        "contract execution delay payment milestone",
        "collusion among bidders in open tender",
    ]

    router_results = []
    for q in test_queries:
        t0 = time.time()
        fams = route_family(q)
        router_results.append({
            "query": q,
            "families": fams,
            "elapsed_ms": round((time.time() - t0) * 1000, 2),
        })

    print("\nRouter results:")
    for r in router_results:
        print(f"  {r['query']} -> {r['families']} ({r['elapsed_ms']} ms)")

    # ------------------------------------------------------------------ #
    # 2. FAISS search real (semántico)
    # ------------------------------------------------------------------ #
    faiss_results = {}
    for q in test_queries:
        try:
            t0 = time.time()
            res = faiss_search(q, k=5, chunks=chunks)
            faiss_results[q] = {
                "elapsed_ms": round((time.time() - t0) * 1000, 2),
                "top_k": [
                    {
                        "chunk_id": r["chunk_id"],
                        "family": r["family"],
                        "indicator_name": r["indicator_name"],
                        "score": round(r["score"], 4),
                        "text_snippet": r["text"][:120] + "..." if len(r["text"]) > 120 else r["text"],
                    }
                    for r in res
                ],
            }
        except Exception as exc:
            faiss_results[q] = {"error": str(exc)}

    # ------------------------------------------------------------------ #
    # 3. BM25 + hybrid (si rank_bm25 disponible)
    # ------------------------------------------------------------------ #
    bm25_obj = build_bm25(chunks)
    hybrid_results = {}
    if bm25_obj:
        print("\nBM25 disponible — corriendo hybrid_search...")
        for q in test_queries:
            t0 = time.time()
            res_rrf = hybrid_search(q, k=5, bm25_obj=bm25_obj, chunks=chunks, fusion_method="rrf")
            res_wgt = hybrid_search(q, k=5, bm25_obj=bm25_obj, chunks=chunks, fusion_method="weighted", alpha=0.6)
            hybrid_results[q] = {
                "elapsed_ms": round((time.time() - t0) * 1000, 2),
                "rrf_top_k": [
                    {
                        "chunk_id": r["chunk_id"],
                        "family": r["family"],
                        "indicator_name": r["indicator_name"],
                        "score": round(r["score"], 4),
                    }
                    for r in res_rrf
                ],
                "weighted_top_k": [
                    {
                        "chunk_id": r["chunk_id"],
                        "family": r["family"],
                        "indicator_name": r["indicator_name"],
                        "score": round(r["score"], 4),
                    }
                    for r in res_wgt
                ],
            }
    else:
        print("\nBM25 no disponible (instalar rank_bm25 para hybrid completo)")

    # ------------------------------------------------------------------ #
    # 4. Demostración de filtrado por familia
    # ------------------------------------------------------------------ #
    filter_demo = {}
    demo_query = "contract delays and payment issues"
    for family in ["planeacion", "competencia-licitacion", "adjudicacion", "ejecucion-contrato"]:
        try:
            if bm25_obj:
                res = hybrid_search(demo_query, k=5, family=family, bm25_obj=bm25_obj, chunks=chunks)
            else:
                res = faiss_search(demo_query, k=5, chunks=chunks, family_filter=family)
            filter_demo[family] = {
                "count": len(res),
                "families_in_results": list({r["family"] for r in res}),
            }
        except Exception as exc:
            filter_demo[family] = {"error": str(exc)}

    print("\nFilter demo:")
    for fam, info in filter_demo.items():
        print(f"  {fam}: {info}")

    # ------------------------------------------------------------------ #
    # 5. Reporte
    # ------------------------------------------------------------------ #
    report = {
        "phase": "fase4-retrieval-router",
        "num_chunks": len(chunks),
        "bm25_available": bm25_obj is not None,
        "router": router_results,
        "faiss": faiss_results,
        "hybrid": hybrid_results,
        "family_filter_demo": filter_demo,
    }

    report_path = Path("progress/evidence/fase4-retrieval-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReporte guardado en {report_path}")
    return report


if __name__ == "__main__":
    run_phase4()
