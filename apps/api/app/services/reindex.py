"""Reindexación inteligente de documentos subidos (F19, spec 007).

Al crear una versión de un documento:
1. Se trocea el texto en chunks deterministas (párrafos empaquetados, sin
   overlap para que el diff por hash sea estable).
2. Se calcula el hash sha256 de cada chunk.
3. Se hace diff contra los chunks de la versión anterior:
   - `added`: chunks nuevos → son los ÚNICOS que se embeben (Gemini) y se
     upsertean a la colección `subject_docs` de Qdrant.
   - `kept`: chunks intactos → reutilizan su `qdrant_point_id` existente,
     cero llamadas de embedding.
   - `removed`: chunks que desaparecieron → sus puntos se borran de Qdrant.
4. Si hay versión anterior, se registra un `ChangeEvent` (CDC).

`embed_fn` y `qdrant_client` son inyectables: los tests corren sin red y la
lógica de diff es idéntica con o sin indexación habilitada
(`RAG_INDEX_SUBJECT_DOCS`).
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from datetime import datetime
from typing import Callable, Dict, List, Optional

from sqlmodel import Session, select

from ..models import ChangeEvent, DocChunk, TdrVersion

logger = logging.getLogger(__name__)

SUBJECT_COLLECTION = "subject_docs"
CHUNK_TARGET_CHARS = 1200
_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "rag-redflags/subject_docs")


def chunk_text(text: str, target: int = CHUNK_TARGET_CHARS) -> List[str]:
    """Trocea por párrafos empaquetados hasta ~target chars, determinista.

    Sin overlap a propósito: el overlap haría que editar un párrafo cambie
    los hashes de los chunks vecinos y el diff perdería precisión.
    """
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: List[str] = []
    current: List[str] = []
    size = 0
    for para in paragraphs:
        # Párrafo gigante: se parte solo en bloques de `target`.
        while len(para) > target:
            if current:
                chunks.append("\n\n".join(current))
                current, size = [], 0
            chunks.append(para[:target])
            para = para[target:]
        if size + len(para) > target and current:
            chunks.append("\n\n".join(current))
            current, size = [], 0
        if para:
            current.append(para)
            size += len(para)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def point_id_for(tdr_id: int, chash: str) -> str:
    """UUID5 determinista por (tdr, hash de chunk) → upsert idempotente."""
    return str(uuid.uuid5(_NAMESPACE, f"{tdr_id}:{chash}"))


def _prev_chunks(session: Session, version_id: int) -> Dict[str, DocChunk]:
    rows = session.exec(
        select(DocChunk).where(DocChunk.tdr_version_id == version_id)
    ).all()
    return {r.chunk_hash: r for r in rows}


def _default_embed_fn() -> Callable[[List[str]], List[List[float]]]:
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from packages.rag_core.gemini_embeddings import embed_texts_gemini

    def _embed(texts: List[str]) -> List[List[float]]:
        return embed_texts_gemini(texts, task_type="RETRIEVAL_DOCUMENT")

    return _embed


def _ensure_collection(client, collection: str, dim: int = 768) -> None:
    from qdrant_client import models as qm

    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )


def reindex_version(
    session: Session,
    *,
    tdr_id: int,
    version: TdrVersion,
    text: str,
    prev_version: Optional[TdrVersion] = None,
    index_enabled: bool = False,
    embed_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
    qdrant_client=None,
    collection: str = SUBJECT_COLLECTION,
) -> Dict:
    """Chunk + diff + (opcional) upsert incremental a Qdrant + ChangeEvent.

    Devuelve un resumen: {chunks_total, chunks_added, chunks_kept,
    chunks_removed, embedded, change_event_id}.

    El diff y las filas DocChunk se computan SIEMPRE (baratos, deterministas);
    el embedding/upsert solo si `index_enabled` y hay cliente/credenciales.
    """
    chunks = chunk_text(text)
    hashes = [chunk_hash(c) for c in chunks]
    prev = _prev_chunks(session, prev_version.id) if prev_version else {}

    added = [h for h in hashes if h not in prev]
    kept = [h for h in hashes if h in prev]
    removed = [h for h in prev if h not in set(hashes)]

    embedded = 0
    if index_enabled and added:
        try:
            if qdrant_client is None:
                from qdrant_client import QdrantClient

                from ..config import get_settings

                settings = get_settings()
                qdrant_client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key,
                    timeout=60,
                )
            if embed_fn is None:
                embed_fn = _default_embed_fn()

            _ensure_collection(qdrant_client, collection)

            from qdrant_client import models as qm

            added_set = set(added)
            to_embed = [
                (h, c) for h, c in zip(hashes, chunks) if h in added_set
            ]
            vectors = embed_fn([c for _, c in to_embed])
            points = [
                qm.PointStruct(
                    id=point_id_for(tdr_id, h),
                    vector=vec,
                    payload={
                        "tdr_id": tdr_id,
                        "tdr_version_id": version.id,
                        "chunk_hash": h,
                        "text": c,
                    },
                )
                for (h, c), vec in zip(to_embed, vectors)
            ]
            for start in range(0, len(points), 100):
                qdrant_client.upsert(
                    collection_name=collection, points=points[start:start + 100]
                )
            embedded = len(points)

            if removed:
                qdrant_client.delete(
                    collection_name=collection,
                    points_selector=qm.PointIdsList(
                        points=[point_id_for(tdr_id, h) for h in removed]
                    ),
                )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Indexación de subject_docs falló (no bloquea): %s", exc)

    now = datetime.utcnow()
    for i, (h, c) in enumerate(zip(hashes, chunks)):
        prev_row = prev.get(h)
        session.add(
            DocChunk(
                tdr_version_id=version.id,
                chunk_hash=h,
                ord=i,
                text=c,
                qdrant_point_id=(
                    point_id_for(tdr_id, h)
                    if (index_enabled and (h in set(added) and embedded))
                    or (prev_row and prev_row.qdrant_point_id)
                    else ""
                ),
                embedded_at=(
                    now
                    if (index_enabled and h in set(added) and embedded)
                    else (prev_row.embedded_at if prev_row else None)
                ),
            )
        )

    change_event_id = None
    if prev_version is not None:
        event = ChangeEvent(
            tdr_id=tdr_id,
            from_version_id=prev_version.id,
            to_version_id=version.id,
            chunks_added=len(added),
            chunks_removed=len(removed),
            chunks_kept=len(kept),
        )
        session.add(event)
        session.flush()
        change_event_id = event.id

    return {
        "chunks_total": len(chunks),
        "chunks_added": len(added),
        "chunks_kept": len(kept),
        "chunks_removed": len(removed),
        "embedded": embedded,
        "change_event_id": change_event_id,
    }
