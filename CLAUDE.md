# CLAUDE.md

Lee primero `AGENTS.md`.

## Uso con Claude Code

Este repo está diseñado para trabajar con sesiones cortas y verificables.

Antes de empezar:
```bash
bash scripts/init.sh
```

Después de cualquier cambio:
```bash
bash scripts/verify.sh
```

## Regla de contexto

No cargues todo el repo en una sola sesión. **Lee primero el contexto mínimo** (en este orden):
1. `docs/MEMORY_INDEX.md` — el mapa: qué abrir según la fase
2. `progress/CURRENT_STATE.md` y `progress/NEXT_ACTION.md`
3. `progress/HANDOFF.md`
4. spec activa: `specs/004-redflags-rag.md`
5. `docs/CAVELOG.md` (solo última entrada)

Metodología en `docs/CAVEMAN.md`. Coordinación con Codex/OpenCode en `docs/MULTI_CLI_PROTOCOL.md`.
**No** abras PDF, JSONL grandes, índices FAISS ni notebooks completos salvo necesidad puntual.

Como subagentes usa `.claude/agents/` (coordinator, spec-planner, dataset-engineer, rag-implementer, evaluator, reviewer). El coordinador delega; no implementa todo.

## Handoff

Al finalizar una sesión, crea un archivo en:

```text
progress/runs/YYYY-MM-DD-HHMM-short-title.md
```

Debe incluir:
- objetivo
- archivos tocados
- comandos ejecutados
- resultados
- problemas
- próximos pasos
