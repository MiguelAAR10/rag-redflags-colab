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

## Agent IO obligatorio para auditorías y análisis

Cuando el usuario pida analizar, auditar, revisar, comparar o dar una segunda opinión sin implementar directamente, usa `progress/agent_io/`.

Si existe un `Active Run` en `progress/agent_io/QUEUE.md`:
1. Lee `progress/agent_io/START_HERE.md`.
2. Ejecuta solo el `REQUEST.md` activo.
3. Guarda el resultado completo en el `RESPONSE.md` indicado si tienes write access.
4. Si estás en modo plan/read-only y no puedes escribir, devuelve el contenido listo para pegar en `RESPONSE.md`.
5. No escribas `REVIEW.md`; eso lo hace DANTE-OS/Claude integrador.

Frase universal para agentes externos:

```text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
```
