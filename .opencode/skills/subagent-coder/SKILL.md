# Subagent Coder

Skill for delegating focused coding tasks to subagents. It favors **impact over bureaucracy** but keeps enough structure to preserve repository integrity across CLIs (Claude, Kimi, DeepSeek, OpenCode).

## Core idea

Use the **simplest orchestration pattern that can complete the task safely**. Do not add agents, skills or abstractions unless they demonstrably improve the outcome.

## When to use this skill

- The task is bounded and verifiable.
- You want to parallelize work or isolate a complex inspection.
- The acceptance criteria can be expressed as a checklist.

## When NOT to use this skill

- Single-file edits that take <5 min.
- Tasks requiring continuous shared context across many files.
- Architectural decisions (use coordinator/human instead).

## Three orchestration profiles

Pick exactly one per task:

| Profile | Use when | Writers | Subagents | Example |
|---------|----------|---------|-----------|---------|
| `single-writer-inspector` | One precious file must change while everything else stays byte-identical | 1 principal + 1 read-only inspector | 1 inspector | Edit a Jupyter notebook, spec, or contract |
| `parallel-sectioning` | Independent files or sections can be worked in parallel | N principals, no shared files | 0 or N section workers | Write docs, slides, tests for separate modules |
| `evaluator-optimizer` | Output quality improves with iterative feedback | 1 generator + 1 evaluator | 1 evaluator | Refactor naming, polish UX copy, translate |

**Default:** `parallel-sectioning` for multi-file work, `single-writer-inspector` for single-file delicate edits.

## Workflow (all profiles)

1. **Integrator** writes a concise task spec in YAML and calls `bash scripts/subagent-run.sh <task.yaml>`.
2. **Subagent(s)** receive exactly: `Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.`
3. **Integrator** reviews `RESPONSE.md`, verifies acceptance independently, writes `REVIEW.md`, updates `docs/CAVELOG.md` and `progress/NEXT_ACTION.md`.

## Task spec format (YAML)

```yaml
run_id: f15-notebook-traceability
agent: subagent-coder
orchestration_profile: single-writer-inspector
role: implementer
mode: write
source: dante-os
related_task: F15
related_spec: specs/004-redflags-rag.md

goal: >-
  Add cell 0 technical sheet and a final traceability table to
  notebooks/redflags_rag_colab.ipynb. Keep all existing cells intact.

read_first:
  - progress/NEXT_ACTION.md
  - notebooks/redflags_rag_colab.ipynb
  - docs/proyecto-final-indicaciones/CHECKLIST.md
  - progress/runs/2026-06-29-1449-claude-fase14-notebook-ragas.md

do_not_read:
  - data/raw/*.pdf
  - data/processed/*.jsonl
  - data/index/*
  - large notebooks or logs unless explicitly required

subagent:
  name: NotebookTraceabilityInspector
  role: read-only
  objective: Map the notebook structure and produce an evidence-grounded insertion contract without modifying files.

allowed_writes:
  - notebooks/redflags_rag_colab.ipynb
  - progress/evidence/*
  - progress/runs/<stamp>-<cli>-f15-notebook-traceability.md
  - docs/CAVELOG.md

forbidden_writes:
  - packages/rag_core/*.py
  - packages/evals/ragas_metrics.py
  - data/eval/goldset.jsonl
  - data/processed/*
  - data/index/*
  - .env
  - specs/*

acceptance:
  - Cell 0 contains project title, author, date, architecture summary, data sources, LLM used, and safe-language warning.
  - A final markdown section contains a table mapping each major requirement to cell number(s) and evidence file/path.
  - bash scripts/verify.sh passes.
  - python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py -q passes.

rules:
  - Do not change the RAG architecture or Qwen pipeline.
  - Label RAGAS metrics as "RAGAS local" in every mention.
  - Use safe anti-corruption language ("red flags", "potential irregularities", "requires human review").
  - If blocked, document the gap in RESPONSE.md and continue with what you can.

output:
  response: progress/agent_io/runs/{run_id}/RESPONSE.md
  evidence: progress/evidence/f15-notebook-traceability.json
```

## How the helper builds the REQUEST

`scripts/subagent-run.sh` reads `orchestration_profile` and composes the `REQUEST.md` from:

1. Frontmatter (run_id, role, mode, etc.)
2. `<goal>`, `<read_first>`, `<do_not_read>`, `<allowed_writes>`, `<forbidden_writes>`, `<acceptance>`, `<rules>`
3. The full profile instructions from `.opencode/skills/subagent-coder/patterns/<profile>.md`
4. `<output>` paths

This keeps the YAML short while the contract is deep and precise.

## Subagent prompt (paste exactly)

```text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
```

## Response contract

The subagent writes `RESPONSE.md` with this structure:

```markdown
# F15 Notebook Traceability Response

## Status
PASS | PASS_WITH_NOTES | BLOCKED | FAIL

## Summary
One paragraph with cells before/after, preservation result, smoke-test result, verify result.

## Evidence
- command / exit code / output summary
- file changes

## Gaps
Anything blocked or unresolved.

## Next Single Action
What the integrator should do next.
```

For `single-writer-inspector` tasks, the response must also include the structured evidence JSON file.

## Integrator review

After the subagent finishes, the integrator:

1. Reads `RESPONSE.md`.
2. Verifies acceptance criteria independently (re-run tests if needed).
3. Writes `REVIEW.md` with verdict: `accepted`, `partially_accepted`, or `rejected`.
4. Updates `docs/CAVELOG.md` and `progress/NEXT_ACTION.md`.
5. Sets `progress/agent_io/QUEUE.md` to `Run ID: none`.

## Best practices

- **One goal per subagent.** If a task has two independent parts, split it into two task specs.
- **Acceptance criteria are the contract.** The subagent is done when every checkbox is green.
- **Forbidden files are guardrails.** They prevent subagents from drifting into architecture or data.
- **Verify before claiming.** The subagent must run the relevant tests and report exit codes.
- **Preserve evidence.** Always produce a machine-readable evidence file for delicate edits.

## Parallel example

For independent docs + slides work, launch two subagents:

```bash
bash scripts/subagent-run.sh tasks/f15-docs.yaml      # paste prompt to Kimi
bash scripts/subagent-run.sh tasks/f15-slides.yaml    # paste prompt to DeepSeek
```

Each writes to a separate run directory. The integrator merges and resolves conflicts.

## Anti-patterns

- **Don't** put architectural decisions in a subagent task.
- **Don't** ask a subagent to "improve the codebase" without a bounded scope.
- **Don't** skip the integrator review, even if the subagent says everything passed.
- **Don't** use parallel writers on the same file.
- **Don't** create new skills or helpers for a one-time task.
