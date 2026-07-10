---
run_id: 2026-06-29-1449-fase14-notebook-ragas-integration-implementer
created_at: 2026-06-29T14:49:00
agent: fase14-notebook-ragas-integration
model: unspecified
role: implementer
mode: write
status: active
source: dante-os
related_task: fase14
related_spec: specs/004-redflags-rag.md
---

# REQUEST

## Goal

Integrate the local RAGAS metrics module into the final Colab notebook section 9 and extend `data/eval/goldset.jsonl` from 12 to 15 items with at least 2 explicit `trap: true` questions. This is Phase 14 of the UNI final RAG project.

## Read First

1. `progress/NEXT_ACTION.md` (it is the Phase 14 contract; follow it strictly)
2. `progress/runs/2026-06-29-1354-opencode-fase13-ragas-metrics.md` (what F13 produced)
3. `progress/runs/2026-06-29-1402-opencode-fase13-ragas-integration.md` (integrator verdict)
4. `packages/evals/ragas_metrics.py` (the metrics you must call)
5. `data/eval/goldset.jsonl` (current 12 items)
6. `notebooks/redflags_rag_colab.ipynb` (section 9 evaluation, the integration site)
7. `docs/proyecto-final-indicaciones/README.md` and `docs/proyecto-final-indicaciones/CHECKLIST.md`

## Do Not Read Fully

- `data/raw/*.pdf`
- `data/processed/*.jsonl`
- `data/index/*`
- Large `.jsonl` or `logs/` outputs
- Older handoff files (just the F13 handoff above is enough)

## Allowed Writes

- `data/eval/goldset.jsonl` (append only; preserve existing 12 items)
- `notebooks/redflags_rag_colab.ipynb` (only the section 9 cells)
- `progress/evidence/ragas-report.json` (new file)
- `packages/rag_core/tests/test_ragas_metrics.py` (only if you add a small goldset-related test)
- `progress/runs/<stamp>-<cli>-fase14-notebook-ragas.md` (handoff)
- `docs/CAVELOG.md` (append a Phase 14 entry dated 2026-06-29)

## Forbidden Writes

- `packages/rag_core/*.py` (retrieval, loaders, pipeline) — unless you need a tiny pure helper that does NOT change architecture; if you must, justify it
- `packages/evals/ragas_metrics.py` — already accepted, do not change signatures
- `data/processed/*`, `data/index/*`, `.env`
- Any spec file under `specs/`
- `progress/agent_io/**` — write only in `progress/runs/` and `docs/CAVELOG.md`

## Rules

- One change at a time, but you may make several small commits inside this run.
- Use TDD: if you add a test, write it first and see it fail before implementing.
- Do not introduce the external `ragas` library or any OpenAI/external API call. Local metrics only.
- Label every output as "RAGAS local" — never call it "RAGAS" without qualifier in notebook/slides.
- Keep domain-safe language: red flags, potential irregularities, "requires human review". No corruption claims.
- Cite evidence: source path + page/section where the answer claims it.
- If you cannot do part of the task, say it explicitly in RESPONSE.md under `Gaps` and continue with what you can.
- Do not modify `progress/agent_io/QUEUE.md` or the `STATUS.md` of this run; the integrator (DANTE-OS) will close it.

## Deliverables (what to put in RESPONSE.md)

```markdown
## Result

## Evidence

- commands run with exact exit codes
- new entries in goldset.jsonl (item ids, trap flags, expected answer)
- notebook section 9 final cell diff (before/after a few lines)
- progress/evidence/ragas-report.json content summary

## Gaps

## Next Single Action
```

## Acceptance Checklist (must be green before you declare success)

1. `data/eval/goldset.jsonl` contains >=15 items; >=2 have `trap: true` and an `expected_answer` that is a refusal or "no hay evidencia suficiente".
2. `notebooks/redflags_rag_colab.ipynb` section 9 has a cell that imports `evaluate_ragas` from `packages.evals.ragas_metrics`, loads `data/eval/goldset.jsonl`, runs the metric over it, and prints a table with `mean_faithfulness`, `mean_answer_relevance`, `mean_context_relevance` plus per-item rows.
3. `progress/evidence/ragas-report.json` exists and has `n`, `mean_faithfulness`, `mean_answer_relevance`, `mean_context_relevance`, `items`.
4. `python3 -m pytest packages/rag_core/tests/test_ragas_metrics.py -q` passes.
5. `bash scripts/verify.sh` passes (expected: 143+ passed, 6 skipped; tolerate slight increase if you add tests).
6. `docs/CAVELOG.md` has a new dated Phase 14 entry.
7. `progress/runs/<stamp>-<cli>-fase14-notebook-ragas.md` handoff exists.

## Suggested Order

1. Append 3 new items (2 traps + 1 normal in-corpus) to `data/eval/goldset.jsonl`. Verify with `wc -l`.
2. Add a tiny test in `test_ragas_metrics.py` that loads the goldset and asserts it parses (`>=15`, `>=2 trap=true`).
3. Edit `notebooks/redflags_rag_colab.ipynb` section 9: import `evaluate_ragas`, run over goldset, write `progress/evidence/ragas-report.json`, print table.
4. Run `bash scripts/verify.sh`.
5. Append CAVELOG entry dated 2026-06-29.
6. Write handoff in `progress/runs/`.

If any step blocks you, stop, document the block in `## Gaps`, and continue with the rest.