# Agent IO START_HERE — Arranque universal para interacciones externas

> Para MiniMax, Kimi, Qwen, Mimo, DeepSeek, Codex, Claude, OpenCode o cualquier agente usado como chat externo / segunda opinion / auditor read-only.

## Frase unica que pega el humano

```text
Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.
```

Si tu entorno no puede leer archivos, pide al humano el contenido de `progress/agent_io/QUEUE.md` y del `REQUEST.md` indicado.

## Pasos obligatorios del agente

1. Lee `progress/agent_io/QUEUE.md`.
2. Ubica la seccion `## Active Run`.
3. Si `Run ID` es `none`, responde exactamente: `No hay interaccion pendiente.`
4. Si `Run ID` no es `none`, abre el path indicado en `Request`.
5. Ejecuta solo el `REQUEST.md` indicado. No expandas alcance.
6. Respeta `agent`, `model`, `role`, `mode`, `status`, `related_task` y `related_spec` del frontmatter.
7. No leas archivos fuera de los indicados en el request, salvo que el request lo autorice.
8. No modifiques archivos salvo autorizacion explicita en el request.
9. Si tienes write access y el request lo permite, guarda la respuesta en el path `Response` indicado en `QUEUE.md`.
10. Si no tienes write access, devuelve la respuesta completa al humano para que la guarde en `Response`.
11. No escribas `REVIEW.md`; eso lo hace DANTE-OS/Claude.
12. No actualices `progress/NEXT_ACTION.md`, `tasks/queue.json`, `docs/CAVELOG.md` ni `progress/runs/`; eso lo hace DANTE-OS/Claude al integrar.

## Regla de oro

`REQUEST.md` manda. `RESPONSE.md` informa. `REVIEW.md` decide.

## Salida esperada

Responde siguiendo exactamente el formato pedido en `REQUEST.md`. Si el request no define formato, usa:

```markdown
## Resultado

## Evidencia

## Riesgos

## Limites
```
