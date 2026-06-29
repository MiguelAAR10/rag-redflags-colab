# RAG Agentic Harness Skill

## Cuándo usar esta skill
Usa esta skill cuando la tarea involucre:
- RAG
- agentes
- retrieval
- citas
- MCP
- verificación
- arquitectura del harness

## Proceso
1. Leer AGENTS.md.
2. Leer spec relevante.
3. Ejecutar o solicitar `bash scripts/init.sh`.
4. Planificar.
5. Implementar con cambios mínimos.
6. Ejecutar `bash scripts/verify.sh`.
7. Registrar en CAVELOG/progress.

## Agent IO

Para análisis, auditorías, reviews o segundas opiniones, usa `progress/agent_io/`:

1. Leer `progress/agent_io/START_HERE.md`.
2. Leer `progress/agent_io/QUEUE.md`.
3. Si hay `Active Run`, ejecutar solo el `REQUEST.md` activo.
4. Guardar el output completo en el `RESPONSE.md` indicado si hay write access.
5. No escribir `REVIEW.md`; lo hace DANTE-OS/Claude.

Frase universal: `Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.`

## Criterio de salida
No declarar éxito si no hay evidencia de verificación.
