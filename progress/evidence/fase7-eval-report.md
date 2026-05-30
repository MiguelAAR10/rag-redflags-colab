# Fase 7 — Reporte de Evaluación

> Gold set: 12 items. Muestra evaluada: 3 queries.
> Evaluación completa del gold set en Colab por tiempo de embedding/cross-encoder.

## Métricas comparativas (3 queries)

| Método | Recall@3 | Recall@5 | Precision@3 | Precision@5 |
|---|---|---|---|---|
| faiss_only | 0.833 | 0.833 | 0.444 | 0.267 |
| hybrid_bm25_faiss | 0.833 | 0.833 | 0.444 | 0.267 |
| hybrid_top20_rerank_top5 | 0.833 | 0.833 | 0.444 | 0.267 |

## Grounding Ratio promedio
**Mean Grounding Ratio**: 0.3051

## Análisis cualitativo

### Ejemplo BUENO
- **Query**: The procurement planning documents were not published to the public.
- **Esperados**: ['R001']
- **Recuperados**: ['R001', 'R063']
- **Recall@5**: 1.0
- **Explicación**: El retrieval encontró indicadores relevantes coincidentes con lo esperado.

### Ejemplo MALO
- **Query**: A single bidder submitted a proposal for this contract.
- **Esperados**: ['R018', 'R019']
- **Recuperados**: ['R018', 'R035']
- **Recall@5**: 0.5
- **Explicación**: El retrieval no encontró los indicadores esperados. Posiblemente la consulta usa lenguaje diferente al del documento, o los indicadores relevantes requieren un análisis más contextual.

## Notas
- Evaluación completa (12 items) pendiente para Colab donde FAISS + reranker corren en GPU T4.
- Gold set validado: 12 items, indicator codes verificados contra dataset.
