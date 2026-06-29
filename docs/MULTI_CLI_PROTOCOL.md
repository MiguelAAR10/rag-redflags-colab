# MULTI_CLI_PROTOCOL — Coordinación Claude · Codex · OpenCode

> Frase guía: **Claude piensa e integra. Codex implementa y audita. OpenCode produce barato. El repo recuerda. Los scripts verifican.**

Los tres CLIs **no trabajan en el mismo chat**. Trabajan sobre el **mismo arnés del repo**: `AGENTS.md`, `docs/MEMORY_INDEX.md`, `specs/`, `progress/`, `docs/CAVELOG.md` y `scripts/`.

Cuando una interacción con un modelo externo ocurre fuera del flujo normal de worker con acceso a archivos, el prompt y la respuesta se registran en `progress/agent_io/`.

## 1. Flota real y roles (sin GPT/Codex — cuidar tokens)

Arranque universal de workers: **`docs/START_HERE.md`** (el humano solo pega *"Lee docs/START_HERE.md y ejecuta la actividad pendiente"*; la tarea vive en `progress/NEXT_ACTION.md`).

| Modelo / CLI | Rol | Úsalo para | NO lo uses para |
|---|---|---|---|
| **Claude** (caro→poco) | Coordinador · integrador · reviewer final | specs, fases, arquitectura, integración, CAVELOG, decisiones difíciles | boilerplate, parsear el PDF, edición mecánica |
| **Kimi K2** | Implementador fuerte (contexto amplio) | módulos centrales (loaders, retrievers, indexing), refactor | decisiones de scope |
| **DeepSeek** (V3 código / R1 razonamiento) | Implementador + reviewer técnico | código, tests, auditoría/razonamiento adversarial | expandir arquitectura |
| **MiniMax** | Worker barato (contexto largo) | docs, reportes markdown, resúmenes, tablas de evaluación | arquitectura crítica |
| **Qwen** | Worker simple **+ es el LLM obligatorio del RAG** | tareas pequeñas de código; y la **generación** del pipeline (Fase 6) | revisión final crítica |

Regla práctica: **un worker produce → DeepSeek/Claude endurece → Claude integra y valida.**
Los modelos abiertos corren idealmente dentro de un CLI con acceso a archivos (p.ej. OpenCode con el proveedor configurado en `opencode.json`); si es chat sin archivos, el humano pega la salida de `bash scripts/context-pack.sh`.

## 2. Aislamiento: cada CLI en su rama / worktree

Ningún agente trabaja sobre la misma carpeta crítica al mismo tiempo.

```bash
git checkout -b chore/harness-base        # rama base
# paralelizar por fase con worktrees:
git worktree add ../rag-dataset  feature/dataset
git worktree add ../rag-chunking feature/chunking
git worktree add ../rag-evals    feature/evals
```

## 3. Propiedad por fase (quién hace, quién revisa)

| Fase | CLI principal | Carpeta principal | Reviewer |
|---|---|---|---|
| 0 Harness | Claude | `docs/`, `specs/`, `progress/`, `scripts/` | Codex |
| 1 Dataset PDF | OpenCode/Codex | `packages/rag_core/loaders.py` | Claude |
| 2 Chunking | Codex | `packages/rag_core/chunkers.py` | Claude |
| 3 Embeddings+FAISS | Codex | `embeddings.py`, `indexing.py` | Claude |
| 4 Retrieval+Router | Codex | `retrievers.py` | Claude |
| 5 Reranker (bonus) | Codex | `rerankers.py` | Claude |
| 6 Qwen+Grounding | Claude/Codex | `agent.py`, `verifier.py`, `citations.py` | cruzado |
| 7 Evaluación | OpenCode | `packages/evals/` | Claude |
| 8 Notebook+Slides | Claude+Codex | `notebooks/`, `slides/` | Codex / Humano |

## 4. Formato de handoff (obligatorio para todo CLI)

Cada CLI deja un archivo en `progress/runs/YYYY-MM-DD-HHMM-<cli>-<fase>.md` con la plantilla de `progress/runs/_TEMPLATE.md`:

```
# Handoff — <fecha> — <fase>
## CLI usado:        Claude / Codex / OpenCode
## Objetivo:         qué se intentó
## Archivos tocados: lista
## Decisiones:       lista (→ también a CAVELOG)
## Comandos:         los ejecutados
## Resultado:        qué quedó funcionando
## Evidencia:        tests/outputs/métricas/conteos
## Riesgos:          qué falta revisar
## Próxima acción:   UNA sola tarea
```

**Claude solo integra cuando existe ese handoff y `verify.sh` pasa.**
Reviews independientes (Codex) van a `progress/reviews/`. Evidencia (métricas, tablas, screenshots) a `progress/evidence/`.

## 4.bis Agent IO (prompts/respuestas externas)

`progress/agent_io/` es la bitácora de prompts y outputs de agentes externos o sesiones multi-modelo. Sirve para MiniMax, Kimi, Qwen, Mimo, DeepSeek, Codex, Claude, OpenCode u otros modelos.

- Para saber qué prompt externo ejecutar: `progress/agent_io/QUEUE.md`.
- Para arrancar sin explicar rutas: `progress/agent_io/START_HERE.md`.
- Prompt exacto: `progress/agent_io/runs/<run-id>/REQUEST.md`.
- Respuesta del agente: `progress/agent_io/runs/<run-id>/RESPONSE.md`.
- Decisión de DANTE-OS/Claude: `progress/agent_io/runs/<run-id>/REVIEW.md`.
- Estado corto: `progress/agent_io/runs/<run-id>/STATUS.md`.

No reemplaza `tasks/queue.json`, `progress/NEXT_ACTION.md` ni `progress/runs/`. Si la revisión del output deriva en trabajo real, Claude actualiza la cola o `NEXT_ACTION` y el worker vuelve al flujo normal.

Frase unica para el humano:

```text
Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.
```

## 5. Flujo diario

```
1. Claude define la tarea (1 fase)
2. OpenCode o Codex ejecuta
3. Worker deja handoff en progress/runs/
4. Codex revisa si el autor fue OpenCode  → progress/reviews/
5. Claude integra → init.sh + verify.sh
6. Claude actualiza CAVELOG + CURRENT_STATE + NEXT_ACTION
```

## 6. Qué NO hacer

- Tres CLIs editando `main` a la vez.
- Claude leyendo el PDF completo.
- OpenCode tomando decisiones de arquitectura.
- Varios agentes tocando `CAVELOG` simultáneamente.
- Cerrar fase sin handoff ni `verify.sh`.
- Tratar `RESPONSE.md` de `agent_io` como decisión final sin `REVIEW.md`.
