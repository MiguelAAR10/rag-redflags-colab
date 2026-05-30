"""
RAG Core Rerankers — Reordenamiento con cross-encoder.

Pipeline: hybrid_search top-20 → reranker → top-5.
Modelo: BAAI/bge-reranker-v2-m3 (o fallback).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def _load_cross_encoder(model_name: str = DEFAULT_MODEL):
    """Carga (y CACHEA) el CrossEncoder. Se carga una sola vez y se reutiliza."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name, trust_remote_code=True)


def rerank(
    query: str,
    candidates: List[Dict],
    top_n: int = 5,
    model_name: str = DEFAULT_MODEL,
) -> List[Dict]:
    """
    Reordena candidatos usando un cross-encoder.

    Args:
        query: texto de la consulta.
        candidates: lista de dicts con 'text' y metadata (salida de hybrid_search).
        top_n: número de resultados a devolver.
        model_name: nombre del modelo CrossEncoder.

    Returns:
        Lista de candidatos reordenados (los top_n mejores), cada uno con
        'rerank_score' añadido. Si el modelo no está disponible, devuelve
        los candidatos originales sin modificar (fallback).
    """
    if not candidates:
        return []

    try:
        model = _load_cross_encoder(model_name)
    except Exception as exc:
        logger.warning(
            "CrossEncoder '%s' no disponible (%s). "
            "Devolviendo candidatos sin rerank.",
            model_name,
            exc,
        )
        return candidates[:top_n]

    try:
        pairs = [[query, c["text"]] for c in candidates]
        scores = model.predict(pairs, show_progress_bar=False)

        if hasattr(scores, "tolist"):
            scores = scores.tolist()
        elif hasattr(scores, "astype"):
            scores = scores.astype(float).tolist()

        reranked = []
        for i, cand in enumerate(candidates):
            c = dict(cand)
            c["rerank_score"] = float(scores[i])
            reranked.append(c)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_n]

    except Exception as exc:
        logger.warning("Reranking falló (%s). Devolviendo candidatos sin rerank.", exc)
        return candidates[:top_n]


def load_candidates_from_faiss(
    query: str,
    k: int = 20,
    index_path=None,
    mapping_path=None,
    chunks_path=None,
) -> List[Dict]:
    """
    Carga candidatos desde FAISS (para pruebas de integración).

    Helper que usa retrievers.py para generar candidatos.
    """
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

    from rag_core.retrievers import faiss_search

    if chunks_path is None:
        chunks_path = repo_root / "data" / "processed" / "redflags_chunks.jsonl"

    import json

    chunks = []
    with open(chunks_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    return faiss_search(query, k=k, chunks=chunks, index_path=index_path, mapping_path=mapping_path)


if __name__ == "__main__":
    print("rerankers.py loaded OK")
    print(f"DEFAULT_MODEL = {DEFAULT_MODEL}")