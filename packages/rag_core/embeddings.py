"""
RAG Core Embeddings — Generación de vectores normalizados con modelo multilingüe.

Usa sentence-transformers con intfloat/multilingual-e5-base (o BAAI/bge-m3).
Los vectores se normalizan para coseno (compatible con FAISS IndexFlatIP).
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "intfloat/multilingual-e5-base"


def _read_hf_token() -> Optional[str]:
    """Lee HF token de variable de entorno o .env, nunca hardcodea."""
    # 1) Variable de entorno
    for varname in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"):
        token = os.environ.get(varname)
        if token:
            return token

    # 2) Archivo .env (usado en desarrollo local)
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"):
                    return value

    return None


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    """Carga (y CACHEA) el modelo sentence-transformers con token HF si está disponible.

    Cacheado con lru_cache → el modelo se carga UNA sola vez por nombre y se
    reutiliza en retrieval, grounding y route_family (evita recargas/OOM en Colab).
    """
    from sentence_transformers import SentenceTransformer

    token = _read_hf_token()
    if token:
        # Inyectar token en el entorno para huggingface_hub
        os.environ.setdefault("HF_TOKEN", token)
        os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", token)

    return SentenceTransformer(model_name, trust_remote_code=True)


def embed_texts(
    texts: List[str],
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 32,
    show_progress: bool = True,
    is_query: bool = False,
) -> np.ndarray:
    """
    Genera embeddings normalizados para una lista de textos.

    Args:
        texts: Lista de textos a embeber.
        model_name: Nombre del modelo (sentence-transformers).
        batch_size: Tamaño del batch.
        show_progress: Mostrar barra de progreso.
        is_query: Si True, antepone "query:" para modelos e5.

    Returns:
        Matriz numpy (n, dim) con vectores L2-normalizados.
    """
    if not texts:
        raise ValueError("texts no puede estar vacío")

    model = _load_model(model_name)

    # Prefijo para modelos e5
    input_texts = texts
    if "e5" in model_name.lower() or "multilingual" in model_name.lower():
        prefix = "query:" if is_query else "passage:"
        input_texts = [f"{prefix} {t}" for t in texts]

    embeddings = model.encode(
        input_texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embeddings


def get_embedding_dim(model_name: str = DEFAULT_MODEL) -> int:
    """Devuelve la dimensionalidad de embeddings del modelo."""
    model = _load_model(model_name)
    # Compatibilidad con versiones antiguas y nuevas
    if hasattr(model, "get_embedding_dimension"):
        return model.get_embedding_dimension()
    return model.get_sentence_embedding_dimension()


if __name__ == "__main__":
    # Smoke test: embeber un texto pequeño
    dim = get_embedding_dim()
    print(f"Model dimension: {dim}")
    vec = embed_texts(["Hello world"], show_progress=False)
    print(f"Shape: {vec.shape}, norm: {np.linalg.norm(vec[0]):.4f}")
    print("Embeddings OK")