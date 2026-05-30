# MEMORY_INDEX — Mapa de lectura (qué abrir y qué NO)

Objetivo: gastar el mínimo de contexto. **No cargues el repo entero.** Abre solo lo que la fase necesita.

## Para iniciar CUALQUIER sesión (siempre)

1. `AGENTS.md`
2. `progress/CURRENT_STATE.md`
3. `progress/NEXT_ACTION.md`
4. `progress/HANDOFF.md`
5. `docs/CAVELOG.md` (solo la última entrada)
6. spec activa: `specs/004-redflags-rag.md`

## Nunca cargar completo (salvo necesidad puntual y justificada)

- PDF original (`data/raw/*.pdf`) → usar reportes/resúmenes en `progress/`.
- `data/processed/*.jsonl` grandes → leer muestra (head) o el reporte, no el archivo entero.
- Índices FAISS (`data/index/*`) → binarios, no se leen.
- Outputs de embeddings, logs extensos, notebooks grandes ya ejecutados.

## Lectura por fase

### Fase 0 — Harness (actual)
`AGENTS.md` · `docs/CAVEMAN.md` · `docs/MULTI_CLI_PROTOCOL.md` · `docs/RUBRICA.md` · `specs/004-redflags-rag.md`

### Fase 1 — Dataset (PDF → unidades documentales)
`specs/004-redflags-rag.md` · `packages/rag_core/loaders.py` · último run en `progress/runs/`
**No leer:** PDF completo, JSONL completo.

### Fase 2 — Chunking
`packages/rag_core/chunkers.py` · reporte de dataset en `progress/evidence/` · spec activa

### Fase 3 — Embeddings + FAISS
`packages/rag_core/embeddings.py` · `packages/rag_core/indexing.py`

### Fase 4 — Retrieval + Router
`packages/rag_core/retrievers.py` (+ familias de red flags en la spec)

### Fase 5 — Reranker (bonus)
`packages/rag_core/rerankers.py`

### Fase 6 — Qwen + Grounding
`packages/rag_core/agent.py` · `packages/rag_core/verifier.py` · `packages/rag_core/citations.py`

### Fase 7 — Evaluación
`packages/evals/` · `docs/RUBRICA.md` · `progress/evidence/`

### Fase 8 — Notebook + Slides
spec activa · módulos de `rag_core` (no duplicar lógica grande dentro del notebook)

## Dónde está cada cosa

| Necesito… | Archivo |
|---|---|
| Reglas de trabajo | `AGENTS.md` |
| Metodología (TCAD/PEV/handoff) | `docs/CAVEMAN.md` |
| Coordinación Claude/Codex/OpenCode | `docs/MULTI_CLI_PROTOCOL.md` |
| Ciclo humano (a quién le hablo) | `docs/LOOP.md` |
| Memoria / no saturar contexto | `docs/MEMORY_PROTOCOL.md` |
| Mapa navegable del repo (grafo) | `progress/context-graph.json` · `docs/CONTEXT_GRAPH.md` |
| Qué exige la nota | `docs/RUBRICA.md` |
| Verdad funcional del proyecto | `specs/004-redflags-rag.md` |
| Estado actual | `progress/CURRENT_STATE.md` |
| Qué hacer ahora | `progress/NEXT_ACTION.md` |
| Cómo retomar | `progress/HANDOFF.md` |
| Decisiones tomadas | `docs/CAVELOG.md` |
| Seguridad / lenguaje seguro | `docs/SECURITY_MODEL.md`, `AGENTS.md` |
