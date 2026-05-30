# Handoff — 2026-05-30-1059 — fase5-reranker

## CLI usado
MiniMax (OpenCode)

## Objetivo
Implementar Fase 5 — Reranker cross-encoder (BONUS): reordenar top-20 de hybrid_search en top-5 con BAAI/bge-reranker-v2-m3.

## Archivos tocados
- `packages/rag_core/rerankers.py` (nuevo)
- `packages/rag_core/tests/test_reranker.py` (nuevo, gate de F5)
- `packages/rag_core/run_phase5.py` (nuevo, runner/evidencia)
- `progress/evidence/fase5-reranker-report.json` (generado)
- `docs/CAVELOG.md` (actualizado)

## Decisiones
- `rerank(query, candidates, top_n=5)` con fallback graceful: si el modelo no carga o predict falla, devuelve candidatos originales sin romper.
- Fake cross-encoder en tests (monkeypatch) que devuelve scores inversos al orden original — así se verifica que el reordenamiento realmente ocurre.
- Helper `load_candidates_from_faiss(query, k=20)` para integración directa con retrievers.py.

## Comandos ejecutados
```bash
bash scripts/init.sh
python3 -m pytest packages/rag_core/tests/test_reranker.py -q
bash scripts/verify.sh
python3 packages/rag_core/run_phase5.py
bash scripts/handoff.sh "fase5-reranker" minimax
```

## Resultado
- `rerankers.py` entrega `rerank` con cross-encoder BAAI/bge-reranker-v2-m3 y fallback intacto.
- Gate `test_reranker.py`: 7 passed (unitarios deterministas), 1 skipped (integración con modelo real).
- `verify.sh` pasa en verde: 60 passed, 4 skipped.
- Reporte generado con comparación visible hybrid top-5 vs reranked top-5 en 3 queries.

## Evidencia
- `progress/evidence/fase5-reranker-report.json`: 3 queries, cross-encoder reordena todos los top-5.
- `pytest -q packages/rag_core/tests/test_reranker.py` → 7 passed, 1 skipped.
- `bash scripts/verify.sh` → 60 passed, 4 skipped, exit=0.

## Riesgos
- El modelo bge-reranker-v2-m3 (~390MB) corre en CPU; aceptable en Colab T4.
- Sin GPU el predict es más lento; no bloquea la funcionalidad.

## Próxima acción exacta
Fase 6 — Qwen + Grounding (`packages/rag_core/agent.py` + `verifier.py` + `citations.py`).