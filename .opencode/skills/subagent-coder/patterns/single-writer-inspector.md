# single-writer-inspector

Use this profile when **one precious file must change while everything else stays byte-identical**. The principal is the only writer. One read-only subagent inspects the file and returns structured findings; the principal verifies, edits, validates and reports.

## Execution model

```yaml
principal_writer: 1
read_only_subagents_default: 1
read_only_subagents_maximum: 1
parallel_writers: 0
branches: 0
worktrees: 0
commits: 0
pushes: 0
```

## Subagent identity

`<subagent_name>` (read-only inspector)

- Objective: inspect the target file and produce an evidence-grounded insertion/editing contract.
- Must not edit, create or delete files.
- Must not run the notebook or execute long-running code.
- Must not propose architecture changes.
- Must not infer missing metadata from the filesystem username.
- Output: structured JSON only, no conversational prose.

## Verify state first

Run read-only:

```bash
pwd
git status --short --branch
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
```

Confirm:

- target file exists;
- no merge/rebase is active;
- no unexpected modification overlaps the allowed write paths.

Classify existing changes as `EXPECTED`, `UNRELATED`, or `BLOCKING`. Stop only when a blocking overlap exists.

## Read-only subagent contract

Allowed scope: target file + files listed in `<read_first>` + paths explicitly referenced by those files.

Required output JSON:

```json
{
  "status": "COMPLETE | INCOMPLETE | BLOCKED",
  "target": {
    "path": "relative/path",
    "original_checksum": "sha256",
    "element_count": 0,
    "elements": [
      {
        "original_index": 0,
        "id": "string|null",
        "type": "markdown|code|raw",
        "first_meaningful_line": "string"
      }
    ]
  },
  "metadata": {
    "field_name": {
      "value": "string|null",
      "evidence": "path and location"
    }
  },
  "mappings": [
    {
      "requirement": "retrieval|reranking|citations|RAGAS local|refusal safety|goldset evaluation",
      "original_indexes": [0],
      "evidence_paths": ["relative/path"],
      "confidence": "HIGH|MEDIUM|LOW"
    }
  ],
  "preservation_risks": [],
  "unknowns": []
}
```

## Principal fan-in

Before editing:

- confirm every cited path exists;
- confirm the referenced element contains the claimed functionality;
- reject unsupported claims;
- preserve unresolved values as explicit blockers or unknowns.

Do not copy a subagent claim directly into the target file without verification.

## Metadata policy

Do not invent:

- author names;
- model identifiers;
- version numbers;
- dates other than the one supplied in the task spec.

Determination order for each metadata field:

1. target file itself;
2. files in `<read_first>`;
3. project config or `AGENTS.md`/`CLAUDE.md`;
4. fallback: `No especificado en los artefactos del proyecto`.

Use the date supplied in the task frontmatter. If none, use today's ISO date.

## Preservation contract

"Keep all existing elements intact" means:

- no existing element is deleted;
- no existing element source changes;
- no existing element type changes;
- no existing element ID changes;
- no existing element metadata changes;
- no existing outputs/execution counts change (for notebooks);
- original element order remains unchanged relative to other original elements.

For notebooks specifically:

- if the notebook originally contains `N` cells, the final notebook must contain `N + K` cells, where `K` is the number of insertions/appends requested;
- every original cell `i` must equal final cell `i + shift`, where `shift` is the number of cells inserted before it.

## Cell/element fingerprints

Before mutation, compute SHA-256 over canonical JSON of each existing element:

```text
cell_type / element_type
source
metadata
id, when present
outputs, when present
execution_count, when present
attachments, when present
```

After mutation verify:

```text
before_fingerprint[i] == after_fingerprint[i + shift]
```

Do not persist element contents in evidence. Persist only:

- original element count;
- final element count;
- original file SHA-256;
- final file SHA-256;
- preservation result;
- inserted/appended indexes.

## Safe editing

For Jupyter notebooks:

- use `nbformat`;
- do not edit raw JSON;
- do not use regex substitution;
- do not normalize, clear or re-execute existing cells;
- write to a temporary file first, reopen and validate, then atomically replace the target.

For other files:

- prefer `edit` tool / structured string replacement;
- avoid broad rewrites;
- keep diffs minimal.

## Evidence file

Create a JSON evidence file at the path declared in `<output>`. Required fields:

```json
{
  "run_id": "string",
  "status": "PASS | PASS_WITH_NOTES | BLOCKED | FAIL",
  "repository": {
    "branch": "string",
    "starting_head": "string"
  },
  "target": {
    "path": "relative/path",
    "original_sha256": "string",
    "final_sha256": "string",
    "original_element_count": 0,
    "final_element_count": 0,
    "inserted_indexes": [0],
    "appended_indexes": [0],
    "original_elements_preserved": true
  },
  "metadata_sources": {},
  "mappings": [],
  "validation": [
    {
      "command": "string",
      "exit_code": 0,
      "result": "PASS | FAIL"
    }
  ],
  "skills_used": [],
  "subagent": {
    "name": "string",
    "status": "COMPLETE | INCOMPLETE | BLOCKED"
  },
  "files_modified": []
}
```

## Validation order

1. Focused test first (e.g. `test_notebook_smoke.py`).
2. `bash scripts/verify.sh`.
3. Validate evidence JSON syntax.
4. Preservation check.
5. `git diff --check`, `git status --short`, `git diff --stat`.

Do not execute or clear the whole notebook unless `verify.sh` explicitly requires it.

## Repair loop

```text
PATCH → focused test → inspect failure → one hypothesis → smallest correction → rerun focused test
```

Maximum 3 distinct repair hypotheses. Do not repeat the same edit without new evidence. Do not modify tests or package code to make the target pass.

## Acceptance criteria

Return `PASS` only when:

1. target file is readable before and after;
2. exactly the requested insertions/appends were made;
3. final element count equals original count plus insertions;
4. every original fingerprint matches at shifted index;
5. required content is present in new cells/sections;
6. every evidence path exists;
7. no forbidden file changed;
8. focused tests pass;
9. `scripts/verify.sh` passes;
10. evidence JSON is valid;
11. `RESPONSE.md` is written;
12. `REVIEW.md` does not exist or remains untouched.

Return `PASS_WITH_NOTES` when all executable gates pass but noncritical metadata is unresolved.

Return `BLOCKED` when a required condition cannot be met without modifying forbidden paths or inventing evidence.

## Response contract

Write `RESPONSE.md` with:

```markdown
# <Task> Response

## Status
PASS | PASS_WITH_NOTES | BLOCKED | FAIL

## Summary
Cells/elements before and after, preservation result, test results.

## Skills activated
| Skill | Path | Purpose |

## Subagent
- name:
- status:
- findings verified by principal:

## Preservation
- original SHA-256:
- final SHA-256:
- original element count:
- final element count:
- inserted indexes:
- appended indexes:
- original elements preserved:

## Metadata
List each field, value and evidence source.

## Mappings / Traceability
| Requirement | Final indexes | Evidence paths | Status |

## Validation
| Command | Exit code | Result |

## Files changed
## Forbidden-path verification
## Open questions or blockers
## Final verdict
```

Do not write `REVIEW.md`.

## Final chat response

Return only a compact summary: status, element counts, preservation result, test results, evidence path, response path, unresolved metadata if any. Do not paste full file contents or long logs.
