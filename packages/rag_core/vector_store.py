"""VectorStore — abstracción del backend de retrieval (F18, spec 007).

Dos implementaciones intercambiables detrás de la misma interfaz:

- FaissVectorStore: envuelve el retrieval híbrido local existente
  (BM25 + FAISS + router de familias). Es lo que usa el notebook académico
  y los tests; no requiere red.
- QdrantVectorStore: producción. Embebe la query con gemini-embedding-001
  y consulta la colección `standard_kb` en Qdrant Cloud (poblada por
  scripts/build_qdrant_index.py). Devuelve chunks en el MISMO formato dict
  que el resto del pipeline (rerankers/verifier/citations) ya consume.

Selección en la web vía settings (RAG_VECTOR_STORE=faiss|qdrant).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional


RESULT_FIELDS = (
    "chunk_id",
    "text",
    "score",
    "indicator_code",
    "indicator_name",
    "family",
    "page_start",
    "page_end",
)


def normalize_result(result: Dict) -> Dict:
    """Normalize one backend result to the shared retrieval contract."""
    text = result.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("vector store result requires non-empty text")

    normalized = {field: result.get(field) for field in RESULT_FIELDS}
    normalized["text"] = text.strip()
    if normalized["score"] is not None:
        normalized["score"] = float(normalized["score"])
    return normalized


def normalize_results(results: List[Dict]) -> List[Dict]:
    """Normalize results, excluding entries that have no usable text."""
    normalized = []
    for result in results:
        text = result.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        normalized.append(normalize_result(result))
    return normalized


class VectorStore(ABC):
    """Interfaz mínima: query en texto → top-k chunks (dicts)."""

    @abstractmethod
    def search(
        self,
        query: str,
        k: int = 5,
        family_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Devuelve hasta k chunks: {chunk_id, text, indicator_code,
        indicator_name, family, page_start, page_end, score}."""


class FaissVectorStore(VectorStore):
    """Envuelve el retrieval híbrido local (BM25 + FAISS + router)."""

    def __init__(self, chunks: Optional[List[Dict]] = None):
        self._chunks = chunks

    def search(
        self,
        query: str,
        k: int = 5,
        family_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        from packages.rag_core.retrievers import hybrid_search, load_chunks

        if self._chunks is None:
            self._chunks = load_chunks()
        family = family_filter[0] if family_filter else None
        results = hybrid_search(query, k=k, family=family, chunks=self._chunks)
        return normalize_results(results)


class QdrantVectorStore(VectorStore):
    """Producción: Gemini embeddings + Qdrant Cloud (colección standard_kb).

    `client` y `embed_fn` son inyectables para tests deterministas sin red.
    """

    def __init__(
        self,
        *,
        collection: str = "standard_kb",
        url: str = "",
        api_key: str = "",
        client=None,
        embed_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
    ):
        self.collection = collection
        self._url = url or os.environ.get("QDRANT_URL") or os.environ.get(
            "QDRANT_ENDPOINT", ""
        )
        self._api_key = api_key or os.environ.get("QDRANT_API_KEY", "")
        self._client = client
        self._embed_fn = embed_fn
        self._preflight_ok = False
        self._vector_name = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            if not self._url:
                raise RuntimeError(
                    "QDRANT_URL/QDRANT_ENDPOINT no configurado para QdrantVectorStore."
                )
            self._client = QdrantClient(
                url=self._url, api_key=self._api_key, timeout=60
            )
        return self._client

    def _get_embed_fn(self):
        if self._embed_fn is None:
            from packages.rag_core.gemini_embeddings import make_query_embed_fn

            self._embed_fn = make_query_embed_fn()
        return self._embed_fn

    def preflight(self) -> None:
        """Validate the configured Qdrant collection once per store instance."""
        if self._preflight_ok:
            return

        try:
            client = self._get_client()
            exists = client.collection_exists(collection_name=self.collection)
        except Exception:
            raise RuntimeError("No se pudo validar la colección Qdrant.") from None
        if not exists:
            raise RuntimeError("La colección Qdrant configurada no existe.")

        try:
            point_count = client.count(
                collection_name=self.collection, exact=True
            ).count
            collection_info = client.get_collection(collection_name=self.collection)
            vectors = collection_info.config.params.vectors
            vector_name = None
            if isinstance(vectors, dict):
                if len(vectors) != 1:
                    raise ValueError("expected one vector configuration")
                vector_name, vectors = next(iter(vectors.items()))
            size = vectors.size
            distance = getattr(vectors.distance, "value", vectors.distance)
        except Exception:
            raise RuntimeError("No se pudo validar la colección Qdrant.") from None

        if point_count <= 0:
            raise RuntimeError("La colección Qdrant está vacía.")
        if size != 768:
            raise RuntimeError("La colección Qdrant debe usar vectores de dimensión 768.")
        if str(distance).lower() != "cosine":
            raise RuntimeError("La colección Qdrant debe usar distancia cosine.")

        self._vector_name = vector_name
        self._preflight_ok = True

    def search(
        self,
        query: str,
        k: int = 5,
        family_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        self.preflight()
        vec = self._get_embed_fn()([query])[0]

        query_filter = None
        if family_filter:
            from qdrant_client import models as qm

            query_filter = qm.Filter(
                must=[qm.FieldCondition(key="family", match=qm.MatchAny(any=family_filter))]
            )

        hits = self._get_client().query_points(
            collection_name=self.collection,
            query=vec,
            using=self._vector_name,
            limit=k,
            query_filter=query_filter,
        ).points

        return normalize_results(
            [{**(h.payload or {}), "score": h.score} for h in hits]
        )


def make_vector_store(kind: str = "faiss", **kwargs) -> VectorStore:
    """Factory por nombre: 'faiss' (local, default) o 'qdrant' (producción)."""
    kind = (kind or "faiss").strip().lower()
    if kind == "qdrant":
        return QdrantVectorStore(**kwargs)
    if kind == "faiss":
        return FaissVectorStore(**kwargs)
    raise ValueError(f"vector store desconocido: {kind!r} (usa 'faiss' o 'qdrant')")
