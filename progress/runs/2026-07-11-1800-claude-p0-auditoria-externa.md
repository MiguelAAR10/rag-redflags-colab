# P0 auditoría externa — bug refusal RAGAS + taxonomía de abstención

- **Fecha:** 2026-07-11
- **Rama:** v2 (`78d1ae8`); Colab main (`5efe346`)
- **Origen:** auditoría externa exhaustiva (nota 6.3/10) sobre la rama v2 del
  repo Colab. Decisión: NO disimular — arreglar los P0 (horas) y documentar
  P1/P2 como roadmap. Los fixes son evidencia de madurez, no de debilidad.

## Triage del feedback (qué era cierto y qué no)

| # | Señalamiento | Veredicto |
|---|---|---|
| 7 | Bug `"requiere revisión humana"` como marcador de refusal → toda respuesta válida puntúa answer_relevance=0 | **CIERTO Y GRAVE** — explica el 0.337 del baseline. Corregido. |
| 11 | OUT_OF_DOMAIN ≠ INSUFFICIENT_EVIDENCE mezclados (3 fuentes de verdad) | **CIERTO** — corregido con taxonomía estructurada. |
| 9/10 | Trampas solo out-of-domain; faltan tipo B (in-domain sin evidencia) y C (premisa falsa); goldset es retrieval-benchmark | **CIERTO** — abstention_set.jsonl creado (6 casos, 3 tipos). Goldset académico intacto (rúbrica: 10–15 preguntas). |
| 8 | No es RAGAS oficial | **YA ETIQUETADO** como "RAGAS local"; etiqueta reforzada a "PROXY léxico" en celda 9.2 y metric_set. |
| 12 | Router como filtro duro | **NO APLICA al pipeline real**: `agent._retrieve_and_rerank` llama `hybrid_search` SIN family. Es global + el filtro es opcional. |
| 5/6 | Grounding solo contra corpus OCP, no contra el documento; token overlap ≠ entailment | **CIERTO conceptualmente (P1)** — parcialmente mitigado: (a) el web ya tiene EvidenceCritic que rechaza findings sin cita literal del análisis; (b) F18 introdujo grounding semántico Gemini. El dual grounding formal queda como tarea P1 integrada a F20. |
| 14 | CURRENT_STATE desactualizado en el repo auditado | **CIERTO** — el auditor leyó la RAMA v2 del repo Colab (obsoleta). progress/ sincronizado en main del Colab. Pendiente: actualizar/borrar la rama v2 de ese repo (decisión del usuario; requiere force push). |

## Fixes implementados (P0)

1. **`ragas_metrics.py`**: marcadores envenenados eliminados; `refusal`
   explícito por item (autoritativo, viene de `analyze()["refusal"]`);
   fallback léxico solo con marcadores inequívocos; items del reporte
   incluyen el refusal resuelto.
2. **`agent.py`**: `analyze()` emite `status` (`ANSWER|ABSTAIN`) y
   `abstain_reason` (`OUT_OF_DOMAIN|INSUFFICIENT_EVIDENCE`) — el texto
   humano se deriva de la estructura, no al revés.
3. **`goldset.jsonl`**: trampas tipadas (`trap_type=out_of_domain`,
   `expected_status`, `expected_abstain_reason`); `expected_answer` corregido
   (ya no mezcla taxonomías).
4. **`data/eval/abstention_set.jsonl`** (nuevo): 6 casos / 3 tipos —
   out_of_domain, in_domain_insufficient_evidence (soborno/monto inexistente),
   false_premise (premisa invertida sobre la guía). Se ejecuta como gate en
   F20; FALSE_PREMISE requiere el Self-RAG loop para detectarse.
5. **Notebook 9.2**: pasa el `refusal` explícito; imprime `status` por item;
   etiqueta "PROXY léxico… no es la librería oficial ragas".
6. **Tests**: 11 nuevos de regresión (el bug no puede volver sin romper CI).

## Gate
`bash scripts/verify.sh` → **198 passed, 6 skipped**.

## Impacto esperado en métricas
El `mean_answer_relevance=0.337` del baseline estaba artificialmente
deprimido por el bug. El Run all de Colab (V1.1, pendiente del usuario)
regenerará el reporte con la señal explícita → valor real por primera vez.

## P1/P2 pendientes (registrados, NO bloquean la entrega académica)
- P1: dual grounding (evidencia-del-TDR vs criterio-OCP) + salida JSON
  estructurada → integrado al diseño de F20 (tarea #10).
- P1: correr abstention_set como gate automático (F20).
- P2: comparativa E5/FAISS vs Gemini/Qdrant ya existe para retrieval
  (f17b-*-recall.json); extender a end-to-end tras F20.
