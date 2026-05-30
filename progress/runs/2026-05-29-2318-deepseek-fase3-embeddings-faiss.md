# Handoff — 2026-05-29-2318 — fase3-embeddings-faiss

## CLI usado
deepseek

## Objetivo
Generar embeddings de los 299 chunks con modelo multilingüe, construir índice FAISS, persistir en `data/index/`.

## Archivos tocados
- `packages/rag_core/embeddings.py` — creado (`embed_texts` con SentenceTransformer, normalización L2)
- `packages/rag_core/indexing.py` — creado (FAISS IndexFlatIP + HNSW, save/load, mapping chunk_id)
- `packages/rag_core/run_phase3.py` — creado (pipeline runner: chunk→embed→index→persist)
- `packages/rag_core/tests/test_embeddings_faiss.py` — gate F3 (16 tests)
- `data/index/redflags_flatip.index` — índice FAISS (299 vectores, 768-dim)
- `data/index/chunk_id_mapping.json` — mapping faiss_id → chunk_id
- `progress/evidence/fase3-embeddings-report.json` — reporte con métricas
- `docs/CAVELOG.md` — entrada de decisión añadida

## Decisiones
- Modelo: `intfloat/multilingual-e5-base` (278M, 768-dim) — multilingüe EN/ES, más ligero que bge-m3.
- Baseline: IndexFlatIP (inner product = cosine sobre vectores normalizados).
- HNSW implementado como bonus (`use_hnsw=True` en build_index).
- Prefijos `passage:` / `query:` automáticos para modelo e5.
- Token HF leído de `HF_TOKEN` env var o `.env`; nunca hardcodeado ni impreso.
- Tests unitarios con dummy numpy arrays (siempre corren, sin GPU ni modelo).

## Comandos ejecutados
```bash
pip install faiss-cpu sentence-transformers --break-system-packages
python3 packages/rag_core/run_phase3.py
python3 -m pytest packages/rag_core/tests/test_embeddings_faiss.py -q
bash scripts/verify.sh
bash scripts/handoff.sh "fase3-embeddings-faiss" deepseek
```

## Resultado
✅ **Todos los criterios de aceptación pasaron:**
- `embed_texts` devuelve `(n, dim)` con vectores normalizados (normas=1.0000) ✓
- `build_index` + `search` round-trip: indexar vectores y query devuelve k resultados ordenados por score ✓
- `chunk_id` recuperable desde faiss_id (mapping correcto) ✓
- 12 tests unitarios deterministas (dummy vectors) siempre corren ✓
- 4 tests de integración con modelo real pasan ✓
- `bash scripts/verify.sh` verde (39 passed total) ✓

**Métricas:**
- Modelo: intfloat/multilingual-e5-base, dim=768
- Chunks: 299 → Vectores: 299
- Tiempo embedding: 85.3s (CPU)
- Índice: IndexFlatIP, 898 KB en disco
- Normas: min=1.0, max=1.0, mean=1.0

## Evidencia
- `data/index/redflags_flatip.index`: índice FAISS persistido
- `data/index/chunk_id_mapping.json`: 299 entradas
- `progress/evidence/fase3-embeddings-report.json`: métricas completas
- `pytest -q`: 16 passed (F3) + 23 passed (F1+F2) = 39 total

## Riesgos
- Modelo e5-base ocupa ~1.1 GB en RAM; en Colab T4 cabe, pero debe documentarse en el notebook.
- IndexFlatIP con 299 vectores es instantáneo (O(n·d) trivial); si el dataset crece, migrar a HNSW.
- El índice no incluye texto crudo (solo vectores + mapping); el retrieval usará el mapping para devolver chunk_id + texto.

## Próxima acción exacta
**Fase 4 — Retrieval + Router:** crear `packages/rag_core/retrievers.py` con búsqueda híbrida BM25 + FAISS, router por familia (`planeacion`, `competencia/licitacion`, `adjudicacion`, `ejecucion/contrato`). Leer spec + último run en `progress/runs/` antes de implementar.