# Agent IO — Traceable Agent Interactions

`progress/agent_io/` records prompts, responses, and reviews from external agents or multi-model sessions that must not be lost in chat.

## Purpose

- Track the exact prompt sent to an agent.
- Track which model answered and when.
- Store the complete output in a versioned file.
- Review the response with DANTE-OS before turning it into project work.
- Avoid untraceable chat copy/paste.

## What It Does Not Replace

- `tasks/queue.json`: cola canonica del proyecto.
- `progress/NEXT_ACTION.md`: siguiente accion real del proyecto.
- `progress/runs/`: handoffs oficiales de ejecucion.
- `progress/evidence/`: metricas y outputs reproducibles.
- `docs/CAVELOG.md`: decisiones integradas y append-only.

## Flow

1. The human gives the agent one instruction: `Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.`
2. The agent reads `progress/agent_io/QUEUE.md` and finds `## Active Run`.
3. If a run is active, the agent opens the referenced `REQUEST.md` and follows that contract.
4. The complete answer is saved in `RESPONSE.md`.
5. DANTE-OS/Claude reviews it in `REVIEW.md`.
6. If the review creates real project work, DANTE-OS/Claude updates `progress/NEXT_ACTION.md` or `tasks/queue.json`.

## Dynamic Entrypoint

Do not explain paths manually for external interactions. Always use:

```text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
```

The agent must discover the active prompt from `progress/agent_io/QUEUE.md`.

## Core Rule

`RESPONSE.md` never decides anything by itself. The operational decision lives in `REVIEW.md` and becomes project work only when it updates `NEXT_ACTION.md`, `tasks/queue.json`, `CAVELOG.md`, or an official handoff.
