#!/usr/bin/env bash
set -euo pipefail

# scripts/subagent-run.sh
# Generate an Agent IO REQUEST.md from a YAML task spec + orchestration profile.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.opencode/skills/subagent-coder"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/subagent-run.sh <task.yaml> [--activate]"
  echo ""
  echo "Example:"
  echo "  bash scripts/subagent-run.sh tasks/f15-notebook.yaml --activate"
  exit 1
fi

TASK_FILE="$1"
ACTIVATE=false
if [ $# -ge 2 ] && [ "$2" = "--activate" ]; then
  ACTIVATE=true
fi

if [ ! -f "$TASK_FILE" ]; then
  echo "Error: task file not found: $TASK_FILE"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required."
  exit 1
fi

PY_PARSE=$(cat <<'PY'
import sys, yaml, pathlib, re

spec_file = sys.argv[1]
skills_dir = sys.argv[2]
request_path = sys.argv[3]
response_path = sys.argv[4]
review_path = sys.argv[5]

with open(spec_file) as f:
    spec = yaml.safe_load(f) or {}

run_id = spec.get("run_id", "")
if not run_id:
    print("ERROR: run_id is required", file=sys.stderr)
    sys.exit(1)

profile = spec.get("orchestration_profile", "parallel-sectioning")
pattern_file = pathlib.Path(skills_dir) / "patterns" / f"{profile}.md"
if not pattern_file.exists():
    print(f"ERROR: profile not found: {pattern_file}", file=sys.stderr)
    sys.exit(1)

pattern = pattern_file.read_text(encoding="utf-8")

# Substitute subagent placeholders if present in spec.
subagent = spec.get("subagent", {})
pattern = pattern.replace("<subagent_name>", subagent.get("name", "Inspector"))
pattern = pattern.replace("<subagent_role>", subagent.get("role", "read-only"))
pattern = pattern.replace("<subagent_objective>", subagent.get("objective", "Inspect and report."))

from datetime import datetime, timezone
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

frontmatter = f"""---
run_id: {run_id}
created_at: {now}
agent: {spec.get("agent", "subagent-coder")}
model: {spec.get("model", "unspecified")}
role: {spec.get("role", "implementer")}
mode: {spec.get("mode", "write")}
status: active
source: {spec.get("source", "dante-os")}
related_task: {spec.get("related_task", "")}
related_spec: {spec.get("related_spec", "")}
orchestration_profile: {profile}
---"""

def fmt_list(items):
    if not items:
        return "- (none)"
    return "\n".join(f"- {x}" for x in items)

subagent_block = ""
if subagent:
    subagent_block = f"""<subagent>
- name: {subagent.get("name", "Inspector")}
- role: {subagent.get("role", "read-only")}
- objective: {subagent.get("objective", "Inspect and report.")}
</subagent>
"""

output = spec.get("output", {})
response_out = output.get("response", response_path)
evidence_out = output.get("evidence", "")

content = f"""{frontmatter}

# REQUEST

<goal>
{spec.get("goal", "").strip()}
</goal>

<read_first>
{fmt_list(spec.get("read_first", []))}
</read_first>

<do_not_read>
{fmt_list(spec.get("do_not_read", []))}
</do_not_read>

<allowed_writes>
{fmt_list(spec.get("allowed_writes", []))}
</allowed_writes>

<forbidden_writes>
{fmt_list(spec.get("forbidden_writes", []))}
</forbidden_writes>

<acceptance>
{fmt_list(spec.get("acceptance", []))}
</acceptance>

<rules>
{fmt_list(spec.get("rules", []))}
</rules>

<orchestration>
profile: {profile}
{subagent_block}</orchestration>

---

{pattern}

<output>
Save your complete response to:
{response_out}

Evidence file (required for single-writer-inspector profile):
{evidence_out if evidence_out else "(none specified)"}

Do NOT write {review_path}; the integrator will write it.
</output>
"""

with open(request_path, "w", encoding="utf-8") as f:
    f.write(content)

print(request_path)
PY
)

RUN_ID="$(python3 - "$TASK_FILE" "$SKILLS_DIR" /dev/null /dev/null /dev/null <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    spec = yaml.safe_load(f) or {}
print(spec.get("run_id", ""))
PY
)"

if [ -z "$RUN_ID" ]; then
  echo "Error: task spec must define 'run_id'."
  exit 1
fi

RUN_DIR="$ROOT_DIR/progress/agent_io/runs/${RUN_ID}"
mkdir -p "$RUN_DIR"

REQUEST_PATH="$RUN_DIR/REQUEST.md"
RESPONSE_PATH="$RUN_DIR/RESPONSE.md"
REVIEW_PATH="$RUN_DIR/REVIEW.md"

python3 - "$TASK_FILE" "$SKILLS_DIR" "$REQUEST_PATH" "$RESPONSE_PATH" "$REVIEW_PATH" <<< "$PY_PARSE"

ROLE="$(python3 -c "import yaml; print((yaml.safe_load(open('$TASK_FILE')) or {}).get('role','implementer'))")"

# STATUS.md
cat > "$RUN_DIR/STATUS.md" <<EOF
# STATUS

- Run ID: \`${RUN_ID}\`
- Agent: subagent-coder
- Model: unspecified
- Role: ${ROLE}
- Status: active
- Request: \`${REQUEST_PATH}\`
- Response: \`${RESPONSE_PATH}\`
- Review: \`${REVIEW_PATH}\`
EOF

: > "$RESPONSE_PATH"

if [ "$ACTIVATE" = true ]; then
  cat > "$ROOT_DIR/progress/agent_io/QUEUE.md" <<EOF
# Agent IO Queue

## Active Run

- **Run ID:** ${RUN_ID}
- **Status:** active
- **Agent suggested:** subagent-coder
- **Role:** ${ROLE}
- **Request:** \`${REQUEST_PATH}\`
- **Response:** \`${RESPONSE_PATH}\`
- **Review:** \`${REVIEW_PATH}\`

## Agent Instructions

If \`Run ID\` is \`none\`:

\`\`\`text
No active interaction.
\`\`\`

If \`Run ID\` is not \`none\`:

1. Open the \`Request\` path.
2. Execute only that request.
3. Save the complete output to \`Response\`.
4. Do not write \`Review\`; the integrator does that.

## Human Instructions

\`\`\`text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
\`\`\`
EOF
  echo "Activated run: ${RUN_ID}"
fi

echo ""
echo "Run created: ${RUN_ID}"
echo "Profile:    $(python3 -c "import yaml; print((yaml.safe_load(open('$TASK_FILE')) or {}).get('orchestration_profile','parallel-sectioning'))")"
echo "Request:    ${REQUEST_PATH/#$ROOT_DIR\/.}"
echo "Response:   ${RESPONSE_PATH/#$ROOT_DIR\/.}"
echo ""
echo "Paste this exact prompt to the subagent CLI:"
echo ""
echo "  Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else."
echo ""
if [ "$ACTIVATE" = false ]; then
  echo "To activate this run in QUEUE.md, run:"
  echo "  bash scripts/subagent-run.sh $TASK_FILE --activate"
fi
