# Checklist de Cumplimiento — Trabajo Final

Este checklist deriva de `docs/proyecto-final-indicaciones/README.md` y debe guiar la mejora posterior al V1 estable.

## Condición para aprobar

- [ ] Notebook corre `Run all` en Google Colab sin intervención manual ni errores.
- [ ] Corpus propio y real documentado.
- [ ] Pipeline RAG completo: ingesta, chunking, embeddings, FAISS, top-k, generación.
- [ ] Respuestas fundamentadas en contexto recuperado.
- [ ] Mínimo 2 técnicas avanzadas implementadas y justificadas.
- [ ] Set de evaluación de 10 a 15 preguntas.
- [ ] Al menos 2 preguntas trampa fuera del corpus.
- [ ] Métricas RAGAS implementadas o replicadas: faithfulness, answer relevance, context relevance.
- [ ] Puntajes RAGAS reportados y comentados.
- [ ] Primera celda del notebook contiene ficha técnica.
- [ ] Notebook incluye tabla de trazabilidad requisito/técnica -> celda.
- [ ] Presentación incluye problema, dominio, arquitectura, técnicas, resultados RAGAS y demo en vivo.

## Técnicas avanzadas candidatas ya alineadas al proyecto

- [x] Re-ranking con cross-encoder.
- [x] Citación obligatoria / trazabilidad de fuente.
- [x] Routing condicional / triaje por familia de red flag.
- [x] Interfaz Gradio como bonus.
- [x] Benchmark comparativo FAISS Flat vs HNSW / híbrido como bonus.
- [ ] RAGAS obligatorio pendiente de implementar/reportar formalmente.
- [ ] Preguntas trampa explícitas pendientes de asegurar en el set de evaluación final.
- [ ] Ficha técnica y tabla de trazabilidad pendientes de auditar contra notebook final.

## Prioridad de mejora

1. Hacer que el notebook cumpla `Run all` en Colab limpio.
2. Añadir o formalizar RAGAS: faithfulness, answer relevance, context relevance.
3. Asegurar evaluación 10-15 preguntas con >=2 trampas.
4. Agregar ficha técnica como primera celda y tabla de trazabilidad.
5. Actualizar presentación con resultados RAGAS.
