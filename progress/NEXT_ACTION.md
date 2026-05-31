# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**Fase 11 — Escribir `docs/PROYECTO.md`: documento de investigación detallado, BASE para los slides.**

- **CLI:** DeepSeek (o MiniMax) — ver `tasks/queue.json` → `F11-doc-slides` · **Reviewer:** Claude
- **Arranque:** `bash scripts/next-task.sh deepseek`

## Objetivo

Producir **`docs/PROYECTO.md`** en español, estilo **documento de investigación bonito** (mermaid, tablas, *callouts* `> [!NOTE]`, citas), que explique **todo el proyecto paso a paso** y sirva de **guion base para generar los slides** (8 secciones). NO es sobre el harness; el foco es el **sistema RAG avanzado** y el **caso de uso** (escáner de *red flags* bajo criterios claros, no sospechas).

## Fuentes a leer (para datos REALES, sin inventar)

- `README.md` (estructura y framing ya definidos) · `specs/004-redflags-rag.md` · `docs/RUBRICA.md`
- **Números reales** desde `progress/evidence/*.json` (conteos y métricas): fase1 (unidades), fase2 (chunks/fragmentación), fase3 (dim, vectores), fase4 (retrieval), fase5 (rerank), fase6 (grounding), fase7 (Recall@k/Precision@k, ejemplos bueno/malo).
- `docs/CAVELOG.md` (decisiones por fase). Firmas en `packages/rag_core/*.py` si hace falta.
- **No** volcar PDF/JSONL/índices al contexto; usar los reportes.

## Estructura obligatoria de `docs/PROYECTO.md`

1. **Portada** (placeholders: logo `docs/assets/logo-universidad.png`, Universidad, Curso, **Docente _\<completar\>_**, Autor MiguelAAR10, Fecha).
2. **Resumen / Abstract.**
3. **Problema y caso de uso** (escáner de *red flags*; criterios definidos, no sospechas; "requiere revisión humana").
4. **Fundamentos de RAG** (conceptos: retrieval, generación condicionada, grounding) con citas.
5. **Dataset** (con números reales: unidades, chunks, familias, dificultades).
6. **Arquitectura** (diagrama **mermaid**).
7. **Técnicas avanzadas** (embeddings E5, FAISS, HNSW, hybrid BM25+FAISS, reranker, grounding, citation-per-sentence) — explicadas y **citadas**.
8. **Pipeline paso a paso** (mermaid + narrativa).
9. **Decisiones técnicas** (chunk 1024/128 y por qué; k=5; modelos elegidos; Flat vs HNSW honesto).
10. **Evaluación y resultados** (Recall@k, Precision@k, grounding ratio, comparación de métodos, ejemplo bueno/malo) — **con los números de `progress/evidence`**.
11. **Minimización de alucinaciones** (grounding, refusal, lenguaje seguro).
12. **Demo (chat Gradio).**
13. **Ética y límites.**
14. **Limitaciones y trabajo futuro.**
15. **Referencias** (reusar las del README).
16. **Anexo — Mapeo a los 8 slides**: tabla `sección del doc → slide` (1 Título · 2 Problema · 3 Dataset · 4 Arquitectura · 5 Decisiones técnicas · 6 Demo · 7 Resultados · 8 Conclusiones), con 3–5 viñetas sugeridas por slide.

## Criterios de aceptación (los revisa Claude)

- [ ] Cubre las 16 secciones; el **Anexo mapea a los 8 slides** con viñetas.
- [ ] Usa **números reales** de `progress/evidence` (no inventados).
- [ ] ≥ 2 diagramas **mermaid** + sección de **Referencias**.
- [ ] **Lenguaje seguro** (señales de riesgo, no corrupción; revisión humana).
- [ ] `bash scripts/verify.sh` sigue verde (el doc no rompe nada).

## NO hacer

- No tocar el pipeline ni el notebook. Solo crear `docs/PROYECTO.md`.

## Verificación

`grep -c "^## " docs/PROYECTO.md` (debe haber muchas secciones) + `bash scripts/verify.sh`. Cierra con `bash scripts/handoff.sh "fase11-doc-slides" deepseek`.
