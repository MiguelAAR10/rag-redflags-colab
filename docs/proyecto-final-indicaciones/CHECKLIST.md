# Checklist de Cumplimiento — Trabajo Final

Este checklist deriva de `docs/proyecto-final-indicaciones/README.md` y debe guiar la mejora posterior al V1 estable.

## Condición para aprobar

- [ ] Notebook corre `Run all` en Google Colab sin intervención manual ni errores.
- [x] Corpus propio y real documentado.
- [x] Pipeline RAG completo: ingesta, chunking, embeddings, FAISS, top-k, generación.
- [x] Respuestas fundamentadas en contexto recuperado.
- [x] Mínimo 2 técnicas avanzadas implementadas y justificadas.
- [x] Set de evaluación de 15 preguntas.
- [x] Al menos 2 preguntas trampa fuera del corpus.
- [x] Proxies léxicos locales inspirados en RAGAS: faithfulness, answer relevance, context relevance.
- [x] Baseline offline reportado y comentado; pendiente reemplazo neural con Colab T4.
- [x] Primera celda del notebook contiene ficha técnica.
- [x] Notebook incluye tabla de trazabilidad requisito/técnica -> celda.
- [ ] Presentación incluye problema, dominio, arquitectura, técnicas, resultados RAGAS y demo en vivo.

## Técnicas avanzadas candidatas ya alineadas al proyecto

- [x] Re-ranking con cross-encoder.
- [x] Citación obligatoria / trazabilidad de fuente.
- [x] Routing condicional / triaje por familia de red flag.
- [x] Interfaz Gradio como bonus.
- [x] Benchmark comparativo FAISS Flat vs HNSW / híbrido como bonus.
- [x] Proxies RAGAS locales implementados y etiquetados sin afirmar equivalencia con la librería oficial.
- [x] Preguntas de seguridad explícitas aseguradas en el set de evaluación final.
- [x] Ficha técnica y tabla de trazabilidad auditadas contra el notebook final.

## Prioridad de mejora

1. Hacer que el notebook cumpla `Run all` en Colab limpio.
2. Añadir o formalizar RAGAS: faithfulness, answer relevance, context relevance.
3. Asegurar evaluación 10-15 preguntas con >=2 trampas.
4. Agregar ficha técnica como primera celda y tabla de trazabilidad.
5. Actualizar presentación con resultados RAGAS.
