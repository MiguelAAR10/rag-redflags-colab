"""
RAG Core Indexing — Construcción y búsqueda con FAISS.

Baseline: IndexFlatIP (inner product = cosine sobre vectores normalizados).
Bonus: HNSW (IndexHNSWFlat).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def build_index(vectors: np.ndarray, use_hnsw: bool = False) -> "faiss.Index":
    """
    Construye índice FAISS sobre vectores normalizados.

    Args:
        vectors: Matriz (n, dim) con vectores L2-normalizados.
        use_hnsw: Si True, usa IndexHNSWFlat (bonus). Sino, IndexFlatIP.

    Returns:
        Índice FAISS entrenado con los vectores añadidos.
    """
    import faiss

    if vectors.ndim != 2:
        raise ValueError(f"vectors debe ser 2D, shape={vectors.shape}")
    if vectors.shape[0] == 0:
        raise ValueError("vectors está vacío")

    dim = vectors.shape[1]
    vectors = np.ascontiguousarray(vectors, dtype=np.float32)

    if use_hnsw:
        M = 32
        index = faiss.IndexHNSWFlat(dim, M)
        index.hnsw.efConstruction = 200
        index.verbose = False
    else:
        index = faiss.IndexFlatIP(dim)

    index.add(vectors)
    return index


def search(
    index: "faiss.Index",
    query_vec: np.ndarray,
    k: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Busca los k vecinos más cercanos en el índice.

    Args:
        index: Índice FAISS.
        query_vec: Vector de consulta (dim,) o matriz (n, dim).
        k: Número de resultados.

    Returns:
        (scores, ids) — scores = inner product (mayor = más similar),
        ids = posiciones en el índice.
    """
    import faiss

    if query_vec.ndim == 1:
        query_vec = query_vec.reshape(1, -1)
    query_vec = np.ascontiguousarray(query_vec, dtype=np.float32)

    scores, ids = index.search(query_vec, k)
    return scores, ids


def save_index(index: "faiss.Index", path: Path) -> None:
    """Persiste índice FAISS a disco."""
    import faiss

    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))
    logger.info(f"Índice guardado: {path} ({index.ntotal} vectores)")


def load_index(path: Path) -> "faiss.Index":
    """Carga índice FAISS desde disco."""
    import faiss

    if not path.exists():
        raise FileNotFoundError(f"Índice no encontrado: {path}")
    return faiss.read_index(str(path))


def build_mapping(chunks: List[Dict], start_id: int = 0) -> Dict[int, str]:
    """
    Construye mapping faiss_id → chunk_id.

    Args:
        chunks: Lista de chunks (con chunk_id).
        start_id: ID de inicio en FAISS (típicamente 0).

    Returns:
        Diccionario {faiss_id: chunk_id}.
    """
    return {start_id + i: c["chunk_id"] for i, c in enumerate(chunks)}


def save_mapping(mapping: Dict[int, str], path: Path) -> None:
    """Persiste mapping a JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in mapping.items()}, f, indent=2, ensure_ascii=False)
    logger.info(f"Mapping guardado: {path} ({len(mapping)} entradas)")


def load_mapping(path: Path) -> Dict[int, str]:
    """Carga mapping desde JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Mapping no encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def resolve_chunk_ids(
    mapping: Dict[int, str],
    faiss_ids: np.ndarray,
) -> List[List[str]]:
    """
    Convierte ids de FAISS a chunk_ids usando el mapping.

    Args:
        mapping: Diccionario {faiss_id: chunk_id}.
        faiss_ids: Matriz de ids de FAISS (n_queries, k).

    Returns:
        Lista de listas de chunk_ids.
    """
    results = []
    for row in faiss_ids:
        row_ids = [mapping.get(int(idx), "UNKNOWN") for idx in row]
        results.append(row_ids)
    return results


if __name__ == "__main__":
    # Smoke test con vectores dummy
    import faiss

    dim = 128
    n = 50
    np.random.seed(42)
    vecs = np.random.randn(n, dim).astype(np.float32)
    # Normalizar
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

    # Build + search
    idx = build_index(vecs)
    assert idx.ntotal == n
    q = np.random.randn(dim).astype(np.float32)
    q = q / np.linalg.norm(q)
    scores, ids = search(idx, q, k=5)
    print(f"Query → top-5 scores: {scores[0]}, ids: {ids[0]}")

    # Save/load round-trip
    tmp_idx = Path("/tmp/test_faiss.index")
    save_index(idx, tmp_idx)
    idx2 = load_index(tmp_idx)
    scores2, ids2 = search(idx2, q, k=5)
    assert np.allclose(scores, scores2), "Round-trip scores mismatch"
    assert np.all(ids == ids2), "Round-trip ids mismatch"
    tmp_idx.unlink()
    print("FAISS round-trip OK")