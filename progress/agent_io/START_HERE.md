# Agent IO START_HERE

> Universal entrypoint for Claude Code, Codex, OpenCode, MiniMax, Kimi, Qwen, Mimo, DeepSeek, or any external agent used for audits, reviews, second opinions, or prompt-based work.

## Single Human Instruction

```text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
```

If you cannot read files, ask the human for `progress/agent_io/QUEUE.md` and the active `REQUEST.md` content.

## Required Agent Steps

1. Read `progress/agent_io/QUEUE.md`.
2. Find `## Active Run`.
3. If `Run ID` is `none`, answer exactly: `No active interaction.`
4. If `Run ID` is not `none`, open the `Request` path.
5. Execute only that `REQUEST.md`. Do not expand scope.
6. Respect the request frontmatter: `agent`, `model`, `role`, `mode`, `status`, `related_task`, and `related_spec`.
7. Do not read files outside the request unless the request explicitly allows it.
8. Do not modify files unless the request explicitly allows write access.
9. If you have write access and the request allows it, save the complete answer to the `Response` path in `QUEUE.md`.
10. If you cannot write files, return the complete answer and clearly say it must be saved to the `Response` path.
11. Do not write `REVIEW.md`; DANTE-OS/Claude does that.
12. Do not update `progress/NEXT_ACTION.md`, `tasks/queue.json`, `docs/CAVELOG.md`, or `progress/runs/`; DANTE-OS/Claude does that during integration.

## Golden Rule

`REQUEST.md` instructs. `RESPONSE.md` records. `REVIEW.md` decides.

## Default Output Format

Follow the exact output format required by `REQUEST.md`. If the request does not define a format, use:

```markdown
## Result

## Evidence

## Risks

## Limits
```
