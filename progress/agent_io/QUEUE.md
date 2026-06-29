# Agent IO Queue

Lightweight queue for external agent interactions. It does not replace `tasks/queue.json` or `progress/NEXT_ACTION.md`.

## Active Run

- **Run ID:** 2026-06-29-1220-claude-final-ragas-audit
- **Status:** draft
- **Agent suggested:** claude
- **Role:** read-only final evaluation auditor
- **Request:** `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REQUEST.md`
- **Response:** `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/RESPONSE.md`
- **Review:** `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REVIEW.md`

## Agent Instructions

If `Run ID` is `none`, answer exactly:

```text
No active interaction.
```

If `Run ID` is not `none`:

1. Open the `Request` path.
2. Execute only that request.
3. Save the complete output to `Response` if you have write access.
4. If you cannot write files, return the complete response so the human can paste it into `Response`.
5. Do not write `Review`; DANTE-OS/Claude does that.

## Human Instructions

Use this single instruction for the agent:

```text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
```
