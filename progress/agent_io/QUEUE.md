# Agent IO Queue

Cola liviana para prompts/interacciones externas. No reemplaza `tasks/queue.json` ni `progress/NEXT_ACTION.md`.

## Active Run

- **Run ID:** none
- **Status:** empty
- **Agent suggested:** none
- **Role:** none
- **Request:** n/a
- **Response:** n/a
- **Review:** n/a

## Agent Instructions

If `Run ID` is `none`, answer exactly:

```text
No hay interaccion pendiente.
```

If `Run ID` is not `none`:

1. Open the `Request` path.
2. Execute only that request.
3. Save or return the output for the `Response` path.
4. Do not write `Review`; DANTE-OS/Claude does that.

## Human Instructions

Frase unica para el agente:

```text
Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.
```

Si el agente no puede leer archivos, copia el contenido completo de `progress/agent_io/START_HERE.md`, este `QUEUE.md` y el `REQUEST.md` indicado.

## Last Reviewed Run

- **Run ID:** `2026-06-29-001-minimax-repo-audit`
- **Agent:** MiniMax-M3
- **Input:** `progress/agent_io/runs/2026-06-29-001-minimax-repo-audit/REQUEST.md`
- **Output:** `progress/agent_io/runs/2026-06-29-001-minimax-repo-audit/RESPONSE.md`
- **Review:** `progress/agent_io/runs/2026-06-29-001-minimax-repo-audit/REVIEW.md`
- **Status:** reviewed
