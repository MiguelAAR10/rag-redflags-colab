"""
RAG Core Retrievers — Retrieval híbrido (BM25 + FAISS) + router de familias.

Entrega:
- bm25_search(query, k)
- faiss_search(query, k)
- hybrid_search(query, k, family=None)  [RRF o suma ponderada]
- route_family(query) -> list[str]

Requiere opcionalmente rank_bm25 para BM25 real (sin ella build_bm25 devuelve None).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX_PATH = REPO_ROOT / "data" / "index" / "redflags_flatip.index"
DEFAULT_MAPPING_PATH = REPO_ROOT / "data" / "index" / "chunk_id_mapping.json"
DEFAULT_CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "redflags_chunks.jsonl"

FAMILY_KEYWORDS = {
    "planeacion": [
        "planning",
        "planeacion",
        "presupuesto",
        "budget",
        "needs assessment",
        "needs",
        "procurement plan",
        "plan",
        "preparation",
        "tender strategy",
        "method",
    ],
    "competencia-licitacion": [
        "tender",
        "competencia",
        "competition",
        "bid",
        "licitacion",
        "bidding",
        "collusion",
        "bid rigging",
        "market",
        "rfp",
        "invitation",
        "shortlisted",
        "pre-qualification",
        "qualification",
        "open tender",
        "restricted",
    ],
    "adjudicacion": [
        "award",
        "adjudicacion",
        "selection",
        "winner",
        "awarded",
        "supplier",
        "contractor",
        "proposal evaluation",
        "evaluacion",
        "best value",
        "lowest price",
        "negotiated",
    ],
    "ejecucion-contrato": [
        "contract",
        "ejecucion",
        "implementation",
        "delivery",
        "performance",
        "payment",
        "milestone",
        "disbursement",
        "completion",
        "extension",
        "variation",
        "fraud",
        "integrity",
        "subcontract",
        "guarantee",
        "warranty",
    ],
}

FAMILY_DESCRIPTIONS = {
    "planeacion": (
        "Risks during procurement planning, budgeting, needs assessment "
        "and procurement strategy."
    ),
    "competencia-licitacion": (
        "Risks during the tender phase, bidding process, competition, "
        "collusion and bid rigging."
    ),
    "adjudicacion": (
        "Risks during the award phase, supplier selection, proposal "
        "evaluation and contracting."
    ),
    "ejecucion-contrato": (
        "Risks during contract execution, delivery, payments, milestones, "
        "variations and completion."
    ),
}

# --------------------------------------------------------------------------- #
# Carga de corpus
# --------------------------------------------------------------------------- #


def load_chunks(path: Optional[Path] = None) -> List[Dict]:
    """Carga chunks desde JSONL."""
    if path is None:
        path = DEFAULT_CHUNKS_PATH
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def _chunk_map(chunks: List[Dict]) -> Dict[str, Dict]:
    return {c["chunk_id"]: c for c in chunks}


# --------------------------------------------------------------------------- #
# BM25
# --------------------------------------------------------------------------- #


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())


def build_bm25(chunks: List[Dict]) -> Optional[Tuple[object, List[str]]]:
    """
    Construye índice BM25 sobre textos de chunks.
    Retorna None si rank_bm25 no está instalado.
    """
    try:
        from rank_bm25 import BM25Okapi
    except Exception:
        logger.warning("rank_bm25 no disponible; BM25 desactivado")
        return None

    texts = [c["text"] for c in chunks]
    tokenized = [_tokenize(t) for t in texts]
    return BM25Okapi(tokenized), texts


def bm25_search(
    query: str,
    k: int = 10,
    bm25_obj: Optional[Tuple[object, List[str]]] = None,
    chunks: Optional[List[Dict]] = None,
    family_filter: Optional[str] = None,
) -> List[Dict]:
    """
    Busca los k chunks más relevantes con BM25.

    Args:
        query: texto de consulta.
        k: número de resultados.
        bm25_obj: tupla (BM25Okapi, texts) o None.
        chunks: lista completa de chunks (para metadata y filtros).
        family_filter: si se especifica, solo chunks de esa familia.
    """
    if bm25_obj is None:
        raise RuntimeError("BM25 no inicializado (rank_bm25 no disponible?)")
    bm25, texts = bm25_obj
    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    ids = list(range(len(texts)))
    if family_filter:
        if chunks is None:
            raise ValueError("chunks requerido para family_filter")
        ids = [i for i in ids if chunks[i].get("family") == family_filter]

    ranked = sorted(ids, key=lambda i: scores[i], reverse=True)[:k]
    results = []
    for i in ranked:
        chunk = chunks[i] if chunks else {"text": texts[i]}
        results.append(
            {
                "chunk_id": chunk.get("chunk_id", f"idx_{i}"),
                "score": float(scores[i]),
                "family": chunk.get("family", ""),
                "indicator_code": chunk.get("indicator_code"),
                "indicator_name": chunk.get("indicator_name"),
                "page_start": chunk.get("page_start", 0),
                "page_end": chunk.get("page_end", 0),
                "text": chunk.get("text", texts[i]),
            }
        )
    return results


# --------------------------------------------------------------------------- #
# FAISS
# --------------------------------------------------------------------------- #


def faiss_search(
    query: str,
    k: int = 10,
    index_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
    chunks: Optional[List[Dict]] = None,
    family_filter: Optional[str] = None,
) -> List[Dict]:
    """
    Busca los k chunks más relevantes con FAISS (embeddings semánticos).

    Args:
        query: texto de consulta.
        k: número de resultados.
        index_path: ruta al índice FAISS.
        mapping_path: ruta al mapping faiss_id → chunk_id.
        chunks: lista completa de chunks (para metadata y filtros).
        family_filter: si se especifica, solo chunks de esa familia.
    """
    from packages.rag_core.embeddings import embed_texts
    from packages.rag_core.indexing import (
        build_mapping,
        load_index,
        load_mapping,
        resolve_chunk_ids,
        search,
    )

    if index_path is None:
        index_path = DEFAULT_INDEX_PATH
    if mapping_path is None:
        mapping_path = DEFAULT_MAPPING_PATH

    if not index_path.exists() or not mapping_path.exists():
        raise FileNotFoundError(
            f"Índice o mapping no encontrado: {index_path}, {mapping_path}"
        )

    index = load_index(index_path)
    mapping = load_mapping(mapping_path)
    chunk_map = _chunk_map(chunks) if chunks else {}

    # Para evitar desfase cuando el mapping no empieza en 0 (no debería),
    # construimos un mapa inverso rápido faiss_id → chunk si chunks está presente.
    if chunks:
        # mapping ya trae faiss_id → chunk_id; chunk_map chunk_id → chunk
        pass

    q_vec = embed_texts([query], show_progress=False, is_query=True)

    # Oversample si hay filtro para asegurar que alcancemos k tras filtrar
    search_k = k * 5 if family_filter else k
    search_k = min(search_k, index.ntotal)

    scores, ids = search(index, q_vec, k=search_k)
    chunk_ids = resolve_chunk_ids(mapping, ids)[0]

    results = []
    for idx_in_row, chunk_id in enumerate(chunk_ids):
        chunk = chunk_map.get(chunk_id)
        if family_filter and chunk and chunk.get("family") != family_filter:
            continue
        results.append(
            {
                "chunk_id": chunk_id,
                "score": float(scores[0][idx_in_row]),
                "family": chunk.get("family", "") if chunk else "",
                "indicator_code": chunk.get("indicator_code") if chunk else None,
                "indicator_name": chunk.get("indicator_name") if chunk else None,
                "page_start": chunk.get("page_start", 0) if chunk else 0,
                "page_end": chunk.get("page_end", 0) if chunk else 0,
                "text": chunk.get("text", "") if chunk else "",
            }
        )
        if len(results) >= k:
            break
    return results


# --------------------------------------------------------------------------- #
# Router de familias
# --------------------------------------------------------------------------- #


def route_family(query: str) -> List[str]:
    """
    Clasifica la consulta en familias de red flags.

    Estrategia:
    1. Keywords exactas (determinista, rápido).
    2. Si no hay match, embeddings de descripciones como fallback.

    Returns:
        Lista de familias (1 o más en caso de empate por keywords).
    """
    query_lower = query.lower()
    scores = {}
    for family, keywords in FAMILY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in query_lower)
        if score:
            scores[family] = score

    if scores:
        max_score = max(scores.values())
        return [f for f, s in scores.items() if s == max_score]

    # Fallback: embeddings similarity con descripciones
    try:
        from packages.rag_core.embeddings import embed_texts

        desc_texts = list(FAMILY_DESCRIPTIONS.values())
        desc_labels = list(FAMILY_DESCRIPTIONS.keys())
        desc_vecs = embed_texts(desc_texts, show_progress=False)
        q_vec = embed_texts([query], show_progress=False, is_query=True)
        # Cosine similarity (vectores normalizados → dot product)
        sims = (desc_vecs @ q_vec.T).flatten()
        best = int(np.argmax(sims))
        return [desc_labels[best]]
    except Exception:
        logger.warning("route_family fallback por embeddings falló")
        return ["competencia-licitacion"]  # default genérico


# --------------------------------------------------------------------------- #
# Fusión híbrida
# --------------------------------------------------------------------------- #


def _rrf_fusion(
    list_a: List[str],
    list_b: List[str],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion entre dos listas ordenadas de chunk_ids.
    Mayor k = más peso a rankings bajos.
    """
    scores: Dict[str, float] = {}
    for rank, chunk_id in enumerate(list_a):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rank + 1 + k)
    for rank, chunk_id in enumerate(list_b):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rank + 1 + k)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _weighted_fusion(
    results_a: List[Dict],
    results_b: List[Dict],
    alpha: float = 0.5,
) -> List[Tuple[str, float]]:
    """
    Suma ponderada de scores normalizados.
    alpha = peso para FAISS; (1-alpha) para BM25.
    """

    def _norm_scores(results: List[Dict]) -> Dict[str, float]:
        if not results:
            return {}
        max_s = max(r["score"] for r in results)
        min_s = min(r["score"] for r in results)
        rng = max_s - min_s if max_s != min_s else 1.0
        return {r["chunk_id"]: (r["score"] - min_s) / rng for r in results}

    norm_a = _norm_scores(results_a)  # BM25
    norm_b = _norm_scores(results_b)  # FAISS

    chunk_ids = set(norm_a.keys()) | set(norm_b.keys())
    fused: Dict[str, float] = {}
    for cid in chunk_ids:
        s = (1 - alpha) * norm_a.get(cid, 0.0) + alpha * norm_b.get(cid, 0.0)
        fused[cid] = s
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(
    query: str,
    k: int = 10,
    family: Optional[str] = None,
    fusion_method: str = "rrf",
    alpha: float = 0.5,
    bm25_obj: Optional[Tuple[object, List[str]]] = None,
    chunks: Optional[List[Dict]] = None,
    index_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Retrieval híbrido: BM25 + FAISS.

    Args:
        query: texto de consulta.
        k: número de resultados.
        family: filtra por familia.
        fusion_method: 'rrf' o 'weighted'.
        alpha: peso para FAISS en weighted (0..1).
        bm25_obj: tupla (BM25Okapi, texts) pre-construido.
        chunks: lista completa de chunks (para metadata y filtros).
        index_path / mapping_path: rutas al índice FAISS.
    """
    chunk_map = _chunk_map(chunks) if chunks else {}

    # BM25
    bm25_results: List[Dict] = []
    if bm25_obj is not None:
        try:
            bm25_results = bm25_search(
                query,
                k=k * 3,
                bm25_obj=bm25_obj,
                chunks=chunks,
                family_filter=family,
            )
        except Exception as exc:
            logger.warning("BM25 search falló: %s", exc)

    # FAISS
    faiss_results: List[Dict] = []
    try:
        faiss_results = faiss_search(
            query,
            k=k * 3,
            index_path=index_path,
            mapping_path=mapping_path,
            chunks=chunks,
            family_filter=family,
        )
    except Exception as exc:
        logger.warning("FAISS search falló: %s", exc)

    # Fusión
    bm25_ids = [r["chunk_id"] for r in bm25_results]
    faiss_ids = [r["chunk_id"] for r in faiss_results]

    if fusion_method == "rrf":
        fused = _rrf_fusion(bm25_ids, faiss_ids)
    elif fusion_method == "weighted":
        fused = _weighted_fusion(bm25_results, faiss_results, alpha=alpha)
    else:
        raise ValueError(f"fusion_method desconocido: {fusion_method}")

    # Construir resultados finales con metadata
    final: List[Dict] = []
    for chunk_id, score in fused[:k]:
        chunk = chunk_map.get(chunk_id, {})
        final.append(
            {
                "chunk_id": chunk_id,
                "score": round(float(score), 6),
                "family": chunk.get("family", ""),
                "indicator_code": chunk.get("indicator_code"),
                "indicator_name": chunk.get("indicator_name"),
                "page_start": chunk.get("page_start", 0),
                "page_end": chunk.get("page_end", 0),
                "text": chunk.get("text", ""),
            }
        )
    return final


if __name__ == "__main__":
    # Smoke test mínimo
    print("route_family('tender collusion'):", route_family("tender collusion"))
    print("route_family('contract payment'):", route_family("contract payment"))
    print("route_family('award winner'):", route_family("award winner"))
    print("route_family('planning budget'):", route_family("planning budget"))
