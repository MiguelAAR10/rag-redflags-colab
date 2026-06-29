---
run_id: YYYY-MM-DD-NNN-agent-topic
created_at: YYYY-MM-DDTHH:MM:SS
agent: minimax|kimi|qwen|mimo|deepseek|codex|claude|opencode|other
model: MODEL_NAME
role: read-only auditor|builder|reviewer|librarian|other
mode: read-only|write-enabled
status: draft
source: dante-os
related_task: none
related_spec: specs/004-redflags-rag.md
---

# REQUEST

## Objetivo

Describe una sola actividad verificable.

## Contexto minimo a leer

1. `AGENTS.md`
2. `docs/MEMORY_INDEX.md`
3. `progress/CURRENT_STATE.md`
4. `progress/NEXT_ACTION.md`
5. `progress/HANDOFF.md`
6. spec activa

## No leer completo

- `data/raw/*.pdf`
- `data/processed/*.jsonl`
- `data/index/*`
- notebooks grandes completos

## Reglas

- No inventar estado.
- Separar confirmado, inferido, desconocido y bloqueante.
- Citar rutas exactas.
- No imprimir secretos.
- Respetar lenguaje seguro del dominio.

## Formato esperado

Define la estructura exacta de salida.
