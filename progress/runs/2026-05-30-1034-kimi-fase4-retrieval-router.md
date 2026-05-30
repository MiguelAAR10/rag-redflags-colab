# Handoff — 2026-05-30-1034 — fase4-retrieval-router

## CLI usado
Kimi K2 (OpenCode)

## Objetivo
Implementar Fase 4 — Retrieval híbrido (BM25 + FAISS) + router de familias de red flags.

## Archivos tocados
- `packages/rag_core/retrievers.py` (nuevo)
- `packages/rag_core/tests/test_retrieval_router.py` (nuevo, gate de F4)
- `packages/rag_core/run_phase4.py` (nuevo, runner/evidencia)
- `progress/evidence/fase4-retrieval-report.json` (generado)
- `docs/CAVELOG.md` (actualizado)

## Decisiones
- RRF (Reciprocal Rank Fusion) como método de fusión por defecto; suma ponderada (`weighted`) como alternativa configurable.
- `route_family` usa keywords bilingües (EN/ES) deterministas con fallback a embeddings de descripciones.
- `rank_bm25` es dependencia opcional: build_bm25 devuelve None si no está instalado, y los tests/integration hacen `pytest.skip` graceful.
- Filtrado por familia implementado como pre-filtro en BM25 y post-filtro con oversample (k*5) en FAISS.

## Comandos ejecutados
```bash
bash scripts/init.sh
python3 -m pytest packages/rag_core/tests/test_retrieval_router.py -q
bash scripts/verify.sh
python3 packages/rag_core/run_phase4.py
bash scripts/handoff.sh "fase4-retrieval-router" kimi
```

## Resultado
- `retrievers.py` entrega `bm25_search`, `faiss_search`, `hybrid_search` y `route_family` con metadata completa por resultado.
- Gate `test_retrieval_router.py`: 14 passed (unitarios deterministas), 3 skipped (integración sin rank_bm25).
- `verify.sh` pasa en verde: 53 passed, 3 skipped.
- Reporte de evidencia generado con ejemplos de queries → top-k y demostración de filtrado por familia.

## Evidencia
- `progress/evidence/fase4-retrieval-report.json`: 299 chunks; router clasifica 5/5 queries correctamente; FAISS real recupera chunks relevantes (scores 0.80–0.86).
- `pytest -q packages/rag_core/tests/test_retrieval_router.py` → 14 passed, 3 skipped.
- `bash scripts/verify.sh` → 53 passed, 3 skipped, exit=0.

## Riesgos
- `rank_bm25` no está en el entorno local; en Colab se debe instalar para activar BM25 real.
- FAISS search con modelo e5-base tarda ~6–15s/query en CPU; aceptable para demo en T4.
- Oversample k*5 para filtro de familia es suficiente con 299 vectores, pero no escalable sin sub-índices.

## Próxima acción exacta
Fase 5 — Reranker cross-encoder (`packages/rag_core/rerankers.py`).
