---
run_id: RUN_ID
created_at: YYYY-MM-DDTHH:MM:SS
agent: AGENT
model: MODEL
role: ROLE
mode: read-only
status: draft
source: dante-os
related_task: none
related_spec: specs/004-redflags-rag.md
---

# REQUEST

## Goal

State one verifiable task.

## Read First

1. `AGENTS.md`
2. `docs/MEMORY_INDEX.md`
3. `progress/CURRENT_STATE.md`
4. `progress/NEXT_ACTION.md`
5. `progress/HANDOFF.md`
6. Active spec

## Do Not Read Fully

- `data/raw/*.pdf`
- `data/processed/*.jsonl`
- `data/index/*`
- large notebooks or logs unless explicitly required

## Rules

- Do not invent state.
- Separate confirmed, inferred, unknown, and blocking facts.
- Cite exact file paths.
- Do not print secrets.
- Keep domain-safe language.
- If write access is not explicitly allowed, do not modify files.

## Output Format

Use concise Markdown:

```markdown
## Result

## Evidence

## Gaps

## Next Single Action
```
