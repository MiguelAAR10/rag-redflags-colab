# Handoff — 2026-06-29-1221 — agent-io-cli-proof

## CLI used

OpenCode

## Objective

Make Agent IO reliable for Claude Code, Codex, OpenCode and external agents: one command, active request discovery, output persisted to Markdown, and short English templates.

## Files touched

- `scripts/agent-io-new.sh`
- `packages/rag_core/tests/test_agent_io_script.py`
- `progress/agent_io/START_HERE.md`
- `progress/agent_io/QUEUE.md`
- `progress/agent_io/README.md`
- `progress/agent_io/_TEMPLATE_REQUEST.md`
- `progress/agent_io/_TEMPLATE_RESPONSE.md`
- `progress/agent_io/_TEMPLATE_REVIEW.md`
- `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REQUEST.md`
- `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/RESPONSE.md`
- `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REVIEW.md`
- `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/STATUS.md`
- `CLAUDE.md`
- `.codex/skills/rag-agentic-harness/SKILL.md`
- `.opencode/agent/worker.md`
- `docs/START_HERE.md`
- `docs/MEMORY_PROTOCOL.md`
- `docs/MULTI_CLI_PROTOCOL.md`
- `docs/CAVELOG.md`
- `docs/CONTEXT_GRAPH.md`
- `progress/context-graph.json`

## Decisions

- Agent IO prompts/templates are now English-first and concise.
- `scripts/agent-io-new.sh` creates a run and updates `progress/agent_io/QUEUE.md` with `## Active Run`.
- Claude/Codex/OpenCode instructions now tell agents to use Agent IO for audits/reviews/second opinions and save output in `RESPONSE.md`.
- A real active run was created for the next Claude Code test: `2026-06-29-1220-claude-final-ragas-audit`.

## Commands run

```bash
bash scripts/init.sh
python3 -m pytest packages/rag_core/tests/test_agent_io_script.py -q
bash scripts/agent-io-new.sh claude final-ragas-audit --model "Opus-4.8" --role "read-only final evaluation auditor"
bash scripts/verify.sh
bash scripts/build-context-graph.sh
bash scripts/handoff.sh "agent-io-cli-proof" opencode
```

## Result

Agent IO is now operational for CLI workflows. The human can tell Claude/Codex/OpenCode:

```text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
```

The agent should discover the active `REQUEST.md` from `QUEUE.md` and write or return content for the configured `RESPONSE.md`.

## Evidence

- `packages/rag_core/tests/test_agent_io_script.py`: 1 passed.
- `bash scripts/verify.sh`: 106 passed, 6 skipped, exit=0.
- `bash scripts/build-context-graph.sh`: 66 nodes, 241 edges, 0 orphans.
- Active run: `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REQUEST.md`.

## Risks

- If a CLI is in plan/read-only mode, it may not write `RESPONSE.md`; in that case it must return the response ready to paste.
- The active run remains pending until Claude Code is tested and `RESPONSE.md` is populated.

## Next single action

Test Claude Code with: `Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.` Then verify that the result lands in `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/RESPONSE.md` or is returned ready to paste there.
