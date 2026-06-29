# Agent IO — Interacciones trazables con agentes

`progress/agent_io/` registra prompts, respuestas y revisiones de agentes externos o sesiones multi-modelo que no deben perderse en el chat.

## Para que sirve

- Saber que prompt exacto se envio a un agente.
- Saber que modelo respondio y cuando.
- Guardar el output completo en un archivo versionable.
- Revisar la respuesta con DANTE-OS antes de convertirla en accion real.
- Evitar copiar/pegar contexto largo entre chats sin trazabilidad.

## Que NO reemplaza

- `tasks/queue.json`: cola canonica del proyecto.
- `progress/NEXT_ACTION.md`: siguiente accion real del proyecto.
- `progress/runs/`: handoffs oficiales de ejecucion.
- `progress/evidence/`: metricas y outputs reproducibles.
- `docs/CAVELOG.md`: decisiones integradas y append-only.

## Flujo

1. El humano pega al agente una sola frase: `Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.`
2. El agente lee `progress/agent_io/QUEUE.md` y localiza `## Active Run`.
3. Si hay run activo, el agente abre el `REQUEST.md` indicado y responde siguiendo ese contrato.
4. La respuesta completa queda en `RESPONSE.md`.
5. DANTE-OS/Claude revisa y completa `REVIEW.md`.
6. Si la revision deriva en trabajo real, se actualiza `progress/NEXT_ACTION.md` o `tasks/queue.json`.

## Entry point dinamico

Para interacciones externas no expliques rutas manualmente. Usa siempre:

```text
Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.
```

El agente debe descubrir el prompt activo desde `progress/agent_io/QUEUE.md`.

## Regla central

Un `RESPONSE.md` no decide nada por si solo. La decision operativa vive en `REVIEW.md` y solo se convierte en trabajo del proyecto cuando actualiza `NEXT_ACTION.md`, `tasks/queue.json`, `CAVELOG.md` o un handoff oficial.
