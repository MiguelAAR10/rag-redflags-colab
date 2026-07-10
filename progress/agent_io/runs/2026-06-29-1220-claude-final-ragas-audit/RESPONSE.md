---
run_id: 2026-06-29-1220-claude-final-ragas-audit
received_at: 2026-06-29T12:20:00
agent: claude
model: Opus-4.8
duration: unknown
write_access_used: true
---

# RESPONSE — final-ragas-audit

## Result

El V1 (F0–F12) es un RAG agéntico anticorrupción funcional y verificado (`verify.sh` ≈ 104–106 passed). Frente a las indicaciones finales UNI quedan **4 brechas que topan la nota**: (1) métricas RAGAS no existen, (2) no hay puntajes RAGAS reportados, (3) el set de evaluación no tiene preguntas trampa, (4) falta la tabla de trazabilidad. La ficha técnica y el "Run all" limpio están parciales. El pipeline RAG base, las técnicas avanzadas y los bonus ya cumplen.

## Requirement Matrix

| Requirement | Current State | Gap | Files / Cells |
|---|---|---|---|
| Run all en Colab sin errores | 🟡 Parcial | Falta probar en sesión limpia (`pip install rank_bm25`, Qwen 4-bit `RAG_QWEN_4BIT=1`) | `notebooks/redflags_rag_colab.ipynb` |
| Corpus propio y real | ✅ | — | `data/raw/OCP2024-RedFlagProcurement-1.pdf` |
| Pipeline RAG completo (ingesta→chunking→embeddings→FAISS→top-k→generación) | ✅ | — | notebook §2–§8 |
| ≥2 técnicas avanzadas justificadas | ✅ (rerank cross-encoder, citación/trazabilidad, routing, multiformato) | — | `rerankers.py`, `retrievers.py`, `citations.py` |
| Respuestas grounded en contexto | ✅ (grounding ratio + refusal) | revisar `mean_grounding_ratio=0.0` en bloque `comparison` del reporte | notebook §8, `verifier.py` |
| Set eval 10–15 preguntas | 🟡 | Hay **12** in-corpus (cuenta OK) | `data/eval/goldset.jsonl` |
| **≥2 preguntas trampa fuera del corpus** | ❌ | **0 trampas** marcadas; todas son red flags válidas | `data/eval/goldset.jsonl` |
| **RAGAS: faithfulness, answer relevance, context relevance** | ❌ | **Las 3 ausentes**; solo hay recall@k/precision@k/grounding/ROUGE-BLEU | `packages/evals/metrics.py` |
| Reportar y comentar puntajes RAGAS | ❌ | Sin celda ni reporte | notebook §9; `progress/evidence/` |
| Ficha técnica como 1ª celda | 🟡 | Cell 0 tiene dominio/arquitectura/modelos; **faltan** campo "Objetivo", lista explícita de "Técnicas avanzadas" y el rótulo "Ficha técnica" | notebook cell 0 |
| Tabla de trazabilidad requisito/técnica → celda | ❌ | **No existe**; el notebook no menciona "trazabilidad" en ninguna celda | notebook (nueva celda tras ficha) |
| Presentación con resultados RAGAS + demo | 🟡 | `docs/PROYECTO.md` base sin números RAGAS (no menciona ragas/trazabilidad) | slides / `docs/PROYECTO.md` |

## Priority Fixes

1. **RAGAS local** (`packages/evals/ragas_metrics.py` nuevo): `faithfulness`, `answer_relevance`, `context_relevance` + `evaluate_ragas(goldset, pipeline)`. Reutiliza Qwen como juez y embeddings e5 ya cargados. Tests en `packages/rag_core/tests/`.
2. **Goldset**: añadir campo `trap: true|false` y **3 preguntas trampa** fuera de corpus (p.ej. receta de cocina, consulta médica, evento deportivo) → 15 ítems, ≥2 trampas. El sistema debe rehusar (reusar refusal de §8.2 como evidencia).
3. **Notebook §9.2 (código)**: correr RAGAS sobre el goldset, imprimir tabla de puntajes y guardar `progress/evidence/ragas-report.json`; **§9.3 (markdown)**: comentar qué revelan los puntajes sobre recuperación vs generación.
4. **Notebook cell 0**: rotular "Ficha técnica" y añadir "Objetivo" + "Técnicas avanzadas".
5. **Notebook nueva celda**: tabla de trazabilidad requisito/técnica → celda.
6. **Slides**: incorporar tabla RAGAS + casos trampa + demo en vivo.

## RAGAS Decision

- **Recommended approach:** Implementación **local** siguiendo el paper (arXiv:2309.15217), usando Qwen2.5-3B como LLM juez y embeddings e5 para similitud, en vez de la librería `ragas`.
- **Why:** La librería `ragas` requiere un LLM juez externo (típicamente OpenAI) + red, lo que **rompe "Run all" en Colab limpio** sin API key y contradice la reproducibilidad offline. El proyecto ya carga Qwen + e5 localmente; las 3 métricas son replicables: faithfulness = proporción de claims de la respuesta inferibles del contexto (Qwen descompone + verifica), answer relevance = similitud coseno pregunta vs preguntas regeneradas desde la respuesta, context relevance = proporción de oraciones del contexto relevantes a la pregunta. (Documentar en slides que se siguió el paper, no la librería.)
- **Files likely affected:** `packages/evals/ragas_metrics.py` (nuevo), `packages/evals/metrics.py` (reuso de helpers), `data/eval/goldset.jsonl`, `notebooks/redflags_rag_colab.ipynb` (§9.2/§9.3 + cell 0 + trazabilidad), `progress/evidence/ragas-report.json` (nuevo).

## Next Single Action

Implementar `packages/evals/ragas_metrics.py` con las tres métricas RAGAS locales (faithfulness, answer_relevance, context_relevance) + función `evaluate_ragas`, con tests unitarios, **sin tocar aún el notebook ni el corpus**. (DANTE-OS/Claude actualiza `NEXT_ACTION.md` durante la integración.)

## Limits

- Auditoría read-only: sin cambios de código, notebook, datos ni índices.
- Inspección del notebook solo estructural (títulos/orden de celdas), no se ejecutó "Run all" — el estado de Run-all en Colab limpio queda sin verificar empíricamente.
- Goldset leído completo (12 líneas) solo para contar y verificar trampas.
- No se escribió `REVIEW.md`, `NEXT_ACTION.md`, `CAVELOG.md`, `tasks/queue.json` ni `progress/runs/` (los gestiona DANTE-OS/Claude integrador).
