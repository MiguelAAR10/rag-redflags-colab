"""
Fase 3 pipeline runner — Embeddings + FAISS index.

Carga chunks, genera embeddings, construye índice, persiste todo en data/index/.
"""

import json
import sys
import time
from pathlib import Path

# Añadir packages/ al path para imports locales
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np


def run_phase3(chunks_path: str = "data/processed/redflags_chunks.jsonl",
               index_dir: str = "data/index",
               model_name: str = "intfloat/multilingual-e5-base",
               use_hnsw: bool = False):
    """Pipeline completo: embed → index → persist."""

    # ------------------------------------------------------------------ #
    # 1. Cargar chunks
    # ------------------------------------------------------------------ #
    chunks_path = Path(chunks_path)
    if not chunks_path.exists():
        raise FileNotFoundError(f"No existe {chunks_path}")

    chunks = []
    with open(chunks_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    print(f"Chunks cargados: {len(chunks)}")

    # ------------------------------------------------------------------ #
    # 2. Embeddings
    # ------------------------------------------------------------------ #
    from rag_core.embeddings import embed_texts, get_embedding_dim

    texts = [c["text"] for c in chunks]
    print(f"Generando embeddings con {model_name}...")
    t0 = time.time()
    vectors = embed_texts(texts, model_name=model_name, batch_size=32)
    elapsed = time.time() - t0

    dim = vectors.shape[1]
    print(f"Embeddings: shape={vectors.shape}, dim={dim}, time={elapsed:.1f}s")
    # Verificar normalización
    norms = np.linalg.norm(vectors, axis=1)
    print(f"Normas: min={norms.min():.4f}, max={norms.max():.4f}, mean={norms.mean():.4f}")

    # ------------------------------------------------------------------ #
    # 3. Construir índice FAISS
    # ------------------------------------------------------------------ #
    from rag_core.indexing import build_index, save_index, build_mapping, save_mapping

    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    index = build_index(vectors, use_hnsw=use_hnsw)
    idx_time = time.time() - t0
    print(f"Índice construido: {index.ntotal} vectores, tiempo={idx_time:.1f}s, type={type(index).__name__}")

    # Persistir índice
    idx_name = "redflags_hnsw.index" if use_hnsw else "redflags_flatip.index"
    idx_path = index_dir / idx_name
    save_index(index, idx_path)

    # ------------------------------------------------------------------ #
    # 4. Mapping chunk_id ↔ faiss_id
    # ------------------------------------------------------------------ #
    mapping = build_mapping(chunks, start_id=0)
    map_path = index_dir / "chunk_id_mapping.json"
    save_mapping(mapping, map_path)

    # ------------------------------------------------------------------ #
    # 5. Reporte
    # ------------------------------------------------------------------ #
    report = {
        "model": model_name,
        "embedding_dim": dim,
        "num_chunks": len(chunks),
        "num_vectors": len(vectors),
        "embedding_time_s": round(elapsed, 1),
        "index_time_s": round(idx_time, 1),
        "index_type": "HNSW" if use_hnsw else "IndexFlatIP",
        "index_path": str(idx_path),
        "mapping_path": str(map_path),
        "norms": {
            "min": round(float(norms.min()), 6),
            "max": round(float(norms.max()), 6),
            "mean": round(float(norms.mean()), 6),
        },
    }

    report_path = Path("progress/evidence/fase3-embeddings-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReporte guardado en {report_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    run_phase3()