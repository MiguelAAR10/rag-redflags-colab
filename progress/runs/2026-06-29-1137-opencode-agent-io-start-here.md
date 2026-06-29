# Handoff — 2026-06-29-1137 — agent-io-start-here

## CLI usado

OpenCode

## Objetivo

Hacer que Agent IO sea dinámico: el humano debe poder dar una sola instrucción al agente y el agente descubrir automáticamente el prompt activo y dónde dejar su output.

## Archivos tocados

- `progress/agent_io/START_HERE.md`
- `progress/agent_io/QUEUE.md`
- `progress/agent_io/README.md`
- `docs/MEMORY_INDEX.md`
- `docs/MEMORY_PROTOCOL.md`
- `docs/MULTI_CLI_PROTOCOL.md`
- `docs/START_HERE.md`
- `docs/CAVELOG.md`
- `docs/CONTEXT_GRAPH.md`
- `progress/context-graph.json`
- `progress/HANDOFF.md`

## Decisiones

- `progress/agent_io/START_HERE.md` es el entrypoint universal para agentes externos.
- La frase única del humano es: `Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.`
- `progress/agent_io/QUEUE.md` usa `## Active Run` con campos fijos: `Run ID`, `Status`, `Agent suggested`, `Role`, `Request`, `Response`, `Review`.
- Si `Run ID` es `none`, el agente responde `No hay interaccion pendiente.`
- `REVIEW.md` y cambios de `NEXT_ACTION.md` siguen siendo responsabilidad de DANTE-OS/Claude, no del agente externo.

## Comandos ejecutados

```bash
bash scripts/init.sh
bash scripts/build-context-graph.sh
bash scripts/handoff.sh "agent-io-start-here" opencode
bash scripts/verify.sh
```

## Resultado

Agent IO ya permite operar con una instrucción corta. El agente externo lee `START_HERE`, consulta `QUEUE.md`, abre el `REQUEST.md` activo si existe, y sabe dónde debe guardarse o devolverse el output.

## Evidencia

- `progress/agent_io/START_HERE.md` define pasos obligatorios del agente.
- `progress/agent_io/QUEUE.md` tiene `## Active Run` parseable.
- `progress/agent_io/README.md` documenta el entrypoint dinámico.
- `docs/MEMORY_PROTOCOL.md` y `docs/MULTI_CLI_PROTOCOL.md` referencian la frase única.
- `bash scripts/build-context-graph.sh` terminó con 65 nodos, 235 aristas, 0 huérfanos.
- `bash scripts/verify.sh` terminó con 105 passed, 6 skipped, exit=0.

## Riesgos

- No hay run activo en Agent IO actualmente (`Run ID: none`), por diseño.
- Para usar el flujo, el siguiente prompt externo debe crear un run y actualizar `QUEUE.md`.

## Próxima acción exacta

La siguiente acción del proyecto sigue siendo la validación final del notebook en Colab T4 indicada por `progress/NEXT_ACTION.md`.
