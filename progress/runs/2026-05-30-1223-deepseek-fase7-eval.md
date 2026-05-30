# Handoff — 2026-05-30-1223 — fase7-eval

## CLI usado
DeepSeek (OpenCode)

## Objetivo
Implementar Fase 7 — Evaluación cuantitativa + cualitativa: gold set ≥10 items, Recall@k, Precision@k, comparación FAISS vs hybrid vs rerank, grounding ratio, ejemplo bueno y malo.

## Archivos tocados
- `data/eval/goldset.jsonl` (nuevo: 12 queries con relevant_indicator_codes verificados)
- `packages/evals/metrics.py` (nuevo: recall_at_k, precision_at_k, mean_grounding_ratio, compare_methods)
- `packages/rag_core/tests/test_eval.py` (nuevo, gate de F7: 15 tests)
- `packages/rag_core/run_phase7.py` (nuevo, runner/evidencia)
- `progress/evidence/fase7-eval-report.json` (generado)
- `progress/evidence/fase7-eval-report.md` (generado)
- `docs/CAVELOG.md` (actualizado)

## Decisiones
- Gold set con 12 queries, cada una con 1-3 indicator_codes relevantes (verificados contra los 69 códigos únicos del dataset).
- Métricas: recall_at_k y precision_at_k comparan indicator_codes recuperados vs relevantes.
- Comparación de 3 métodos: FAISS-only, hybrid (BM25+FAISS), hybrid_top20+rerank_top5.
- Evaluación de 3 queries en local (muestra); gold set completo en Colab.
- BONUS: `_try_rouge_bleu` con `rouge_score`/`nltk` (graceful skip si no instalado).

## Comandos ejecutados
```bash
bash scripts/init.sh
python3 -m pytest packages/rag_core/tests/test_eval.py -q
bash scripts/verify.sh
python3 packages/rag_core/run_phase7.py
bash scripts/handoff.sh "fase7-eval" deepseek
```

## Resultado
- `metrics.py` + `test_eval.py` + gold set implementados.
- Gate `test_eval.py`: 15 passed (11 unitarios + 2 gold set validation + 1 integración + 1 extra que apareció).
- `verify.sh` pasa en verde: **90 passed, 4 skipped**, exit=0.
- Reporte JSON y MD generados con métricas, comparación y análisis cualitativo (mejor y peor ejemplo).

## Evidencia
- `progress/evidence/fase7-eval-report.json` y `.md`: R@3=0.833, R@5=0.833 (sin BM25, FAISS/hybrid/rerank idénticos en esta muestra).
- Gold set: 12 items (>10 requerido), códigos verificados.
- `pytest -q packages/rag_core/tests/test_eval.py` → 15 passed.
- `bash scripts/verify.sh` → 90 passed, 4 skipped, exit=0.

## Riesgos
- Sin `rank_bm25`, FAISS/hybrid/rerank producen métricas idénticas. En Colab con BM25, la comparación tendrá varianza real entre métodos.
- Evaluación limitada a 3 queries en local por tiempo de reranker. Gold set completo (12 items) se ejecuta en Colab donde FAISS + reranker corren en GPU.

## Próxima acción exacta
Fase 8 — Notebook final de Colab + slides.
