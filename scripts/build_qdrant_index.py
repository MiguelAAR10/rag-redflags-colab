#!/usr/bin/env python3
"""F17b — Población de Qdrant Cloud con el corpus estándar (guía OCP).

Embedea data/processed/redflags_chunks.jsonl con gemini-embedding-001 (dim 768)
y hace upsert idempotente a la colección `standard_kb` en Qdrant Cloud.

El notebook académico NO usa este script (decisión spec 007): el índice de
producción vive en Qdrant; el notebook sigue autosuficiente con E5+FAISS.

Uso:
    python3 scripts/build_qdrant_index.py            # indexa (idempotente)
    python3 scripts/build_qdrant_index.py --recreate # borra y re-crea la colección
    python3 scripts/build_qdrant_index.py --eval     # gate de recall@5 vs goldset
    python3 scripts/build_qdrant_index.py --query "single bidder short deadline"

Credenciales (env o .env, nunca hardcodeadas):
    GEMINI_API_KEY | GOOGLE_API_KEY
    QDRANT_ENDPOINT | QDRANT_URL, QDRANT_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "redflags_chunks.jsonl"
GOLDSET_PATH = REPO_ROOT / "data" / "eval" / "goldset.jsonl"
EVIDENCE_PATH = REPO_ROOT / "progress" / "evidence" / "f17b-qdrant-index-report.json"

COLLECTION = "standard_kb"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768  # truncado MRL; requiere re-normalizar (docs de Google)
BATCH_SIZE = 32
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "rag-redflags/standard_kb")

PAYLOAD_FIELDS = (
    "chunk_id", "indicator_code", "indicator_name", "family",
    "page_start", "page_end", "block_type", "text",
)


def load_env_file(path: Path) -> None:
    """Carga variables de un .env simple sin dependencia de python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_credentials() -> tuple[str, str, str]:
    load_env_file(REPO_ROOT / ".env")
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
    qdrant_url = os.environ.get("QDRANT_URL") or os.environ.get("QDRANT_ENDPOINT") or ""
    qdrant_key = os.environ.get("QDRANT_API_KEY", "")
    missing = [name for name, val in [
        ("GEMINI_API_KEY/GOOGLE_API_KEY", api_key),
        ("QDRANT_ENDPOINT/QDRANT_URL", qdrant_url),
        ("QDRANT_API_KEY", qdrant_key),
    ] if not val]
    if missing:
        sys.exit(f"Faltan credenciales en el entorno/.env: {', '.join(missing)}")
    return api_key, qdrant_url, qdrant_key


def load_chunks() -> list[dict]:
    return [json.loads(line) for line in CHUNKS_PATH.read_text().splitlines() if line.strip()]


def normalize(vec: list[float]) -> list[float]:
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec] if norm else vec


def embed_texts(client, texts: list[str], *, task_type: str) -> list[list[float]]:
    """Embedea con gemini-embedding-001 @768, re-normalizado (MRL truncation)."""
    from google.genai import types

    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBED_DIM,
            ),
        )
        vectors.extend(normalize(list(e.values)) for e in result.embeddings)
        print(f"  embebidos {min(start + BATCH_SIZE, len(texts))}/{len(texts)}")
    return vectors


def point_id_for(chunk_id: str) -> str:
    """UUID5 determinista por chunk_id -> upsert idempotente."""
    return str(uuid.uuid5(NAMESPACE, chunk_id))


def build(recreate: bool) -> None:
    from qdrant_client import QdrantClient
    from qdrant_client import models as qm
    from google import genai

    api_key, qdrant_url, qdrant_key = get_credentials()
    gclient = genai.Client(api_key=api_key)
    qclient = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=60)

    if recreate and qclient.collection_exists(COLLECTION):
        qclient.delete_collection(COLLECTION)
        print(f"Colección {COLLECTION} eliminada (--recreate)")
    if not qclient.collection_exists(COLLECTION):
        qclient.create_collection(
            collection_name=COLLECTION,
            vectors_config=qm.VectorParams(size=EMBED_DIM, distance=qm.Distance.COSINE),
        )
        print(f"Colección {COLLECTION} creada (dim={EMBED_DIM}, cosine)")

    chunks = load_chunks()
    print(f"Chunks a indexar: {len(chunks)}")
    vectors = embed_texts(gclient, [c["text"] for c in chunks], task_type="RETRIEVAL_DOCUMENT")

    points = [
        qm.PointStruct(
            id=point_id_for(chunk["chunk_id"]),
            vector=vec,
            payload={k: chunk.get(k) for k in PAYLOAD_FIELDS},
        )
        for chunk, vec in zip(chunks, vectors)
    ]
    for start in range(0, len(points), 100):
        qclient.upsert(collection_name=COLLECTION, points=points[start:start + 100])
    count = qclient.count(COLLECTION).count
    print(f"Upsert completo. Puntos en {COLLECTION}: {count}")

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps({
        "phase": "f17b-qdrant-index",
        "collection": COLLECTION,
        "embed_model": EMBED_MODEL,
        "dim": EMBED_DIM,
        "points": count,
        "source": str(CHUNKS_PATH.relative_to(REPO_ROOT)),
    }, indent=2, ensure_ascii=False))
    print(f"Evidencia: {EVIDENCE_PATH.relative_to(REPO_ROOT)}")


def search(qclient, gclient, query: str, k: int = 5) -> list[dict]:
    vec = embed_texts(gclient, [query], task_type="RETRIEVAL_QUERY")[0]
    hits = qclient.query_points(collection_name=COLLECTION, query=vec, limit=k).points
    return [{"score": h.score, **(h.payload or {})} for h in hits]


def run_query(query: str) -> None:
    from qdrant_client import QdrantClient
    from google import genai

    api_key, qdrant_url, qdrant_key = get_credentials()
    for r in search(QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=60),
                    genai.Client(api_key=api_key), query):
        print(f"{r['score']:.3f} | {r.get('indicator_code')} | "
              f"{r.get('indicator_name')} | p{r.get('page_start')}")


def run_eval() -> None:
    """Gate de recall@5: Gemini/Qdrant debe estar a la altura del baseline E5/FAISS."""
    from qdrant_client import QdrantClient
    from google import genai

    api_key, qdrant_url, qdrant_key = get_credentials()
    qclient = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=60)
    gclient = genai.Client(api_key=api_key)

    gold = [json.loads(line) for line in GOLDSET_PATH.read_text().splitlines() if line.strip()]
    scored = []
    for item in gold:
        expected = set(item.get("relevant_indicator_codes") or [])
        if not expected:  # trampas: no cuentan para recall de retrieval
            continue
        hits = search(qclient, gclient, item["query"], k=5)
        got = {h.get("indicator_code") for h in hits}
        recall = len(expected & got) / len(expected)
        scored.append({"query": item["query"][:60], "expected": sorted(expected),
                       "recall@5": recall})
        print(f"recall@5={recall:.2f}  {item['query'][:70]}")
    mean_recall = sum(s["recall@5"] for s in scored) / len(scored)
    print("-" * 60)
    print(f"MEAN recall@5 (Gemini/Qdrant, n={len(scored)}): {mean_recall:.3f}")
    print("Baseline E5/FAISS local de referencia: ver progress/evidence/fase7-eval-report.json")

    report_path = REPO_ROOT / "progress" / "evidence" / "f17b-qdrant-recall.json"
    report_path.write_text(json.dumps({
        "phase": "f17b-qdrant-recall-gate",
        "embed_model": EMBED_MODEL, "dim": EMBED_DIM,
        "mean_recall_at_5": mean_recall, "items": scored,
    }, indent=2, ensure_ascii=False))
    print(f"Evidencia: {report_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--query", type=str, default="")
    args = parser.parse_args()
    if args.query:
        run_query(args.query)
    elif args.eval:
        run_eval()
    else:
        build(recreate=args.recreate)
