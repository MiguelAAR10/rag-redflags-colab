# parallel-sectioning

Use this profile when **independent files or sections can be worked in parallel** without shared state. Each section gets its own writer; the integrator merges results.

## Execution model

```yaml
principal_integrator: 1
section_writers: N
read_only_subagents: 0
parallel_writers: N
branches: 0
worktrees: 0
commits: 0
pushes: 0
```

## When to choose this profile

- Writing docs + slides + README updates for the same release.
- Adding independent tests for separate modules.
- Updating configuration files that do not reference each other.

## When NOT to choose this profile

- Two sections touch the same file.
- One section's output is another's input.
- The task requires byte-level preservation of a single file.

## Task split

The integrator creates one YAML per section:

```yaml
run_id: f15-docs-proyecto
orchestration_profile: parallel-sectioning
section: docs

goal: Update docs/PROYECTO.md with RAGAS local label and scores table.

allowed_writes:
  - docs/PROYECTO.md
  - progress/runs/<stamp>-<cli>-f15-docs.md

forbidden_writes:
  - notebooks/*
  - packages/*
  - data/*
```

Each section writer receives only its own `REQUEST.md` and writes to its own run directory.

## Independence rules

- No two sections may declare the same file in `allowed_writes`.
- No section may depend on another section's output.
- If a merge conflict appears, the integrator resolves it manually.

## Response contract

Each section writer writes `RESPONSE.md` with:

```markdown
## Result
## Evidence
## Gaps
## Files changed
## Next Single Action
```

## Integrator merge

After all sections finish:

1. Read every `RESPONSE.md`.
2. Check for overlapping file changes.
3. Resolve conflicts if any.
4. Run `bash scripts/verify.sh` once.
5. Write a single `REVIEW.md` for the combined task.

## Anti-patterns

- Do not use parallel-sectioning for a notebook that needs exact cell preservation.
- Do not let section writers edit shared config files.
- Do not skip the integrator merge step.
