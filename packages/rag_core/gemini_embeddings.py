"""Embeddings vía API de Google (gemini-embedding-001).

Ruta de producción (F18): el backend web no carga modelos locales; embebe
queries y verifica grounding con la misma API que pobló Qdrant
(scripts/build_qdrant_index.py). El notebook académico NO usa este módulo:
sigue con E5 local (embeddings.py).

Auth (en orden): Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=true +
GOOGLE_CLOUD_PROJECT, vía ADC) o API key (GOOGLE_API_KEY / GEMINI_API_KEY).
Nunca se hardcodea una credencial.
"""

from __future__ import annotations

import os
from typing import Callable, List, Optional

DEFAULT_EMBED_MODEL = "gemini-embedding-001"
DEFAULT_DIM = 768  # truncado MRL; requiere re-normalizar (docs de Google)
DEFAULT_BATCH_SIZE = 32


def _truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def make_gemini_client():
    """Cliente google-genai: Vertex AI (ADC) si está configurado; si no, API key."""
    from google import genai

    if _truthy(os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "")):
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
    return genai.Client(api_key=api_key)


def _normalize(vec: List[float]) -> List[float]:
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec] if norm else vec


def embed_texts_gemini(
    texts: List[str],
    *,
    task_type: str,
    dim: int = DEFAULT_DIM,
    model: str = DEFAULT_EMBED_MODEL,
    client=None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> List[List[float]]:
    """Embebe con gemini-embedding-001, truncado a `dim` y re-normalizado.

    task_type: 'RETRIEVAL_QUERY' (consultas), 'RETRIEVAL_DOCUMENT' (corpus)
    o 'SEMANTIC_SIMILARITY' (comparación frase-a-frase, p. ej. grounding).
    """
    from google.genai import types

    if client is None:
        client = make_gemini_client()

    vectors: List[List[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        result = client.models.embed_content(
            model=model,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=dim,
            ),
        )
        vectors.extend(_normalize(list(e.values)) for e in result.embeddings)
    return vectors


def make_query_embed_fn(client=None) -> Callable[[List[str]], List[List[float]]]:
    """Función parcial para embeber consultas (inyectable en VectorStore)."""
    def _embed(texts: List[str]) -> List[List[float]]:
        return embed_texts_gemini(texts, task_type="RETRIEVAL_QUERY", client=client)

    return _embed


def make_similarity_embed_fn(client=None) -> Callable[[List[str]], List[List[float]]]:
    """Función parcial para grounding semántico (inyectable en verifier)."""
    def _embed(texts: List[str]) -> List[List[float]]:
        return embed_texts_gemini(
            texts, task_type="SEMANTIC_SIMILARITY", client=client
        )

    return _embed
