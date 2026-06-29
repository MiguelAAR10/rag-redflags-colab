#!/usr/bin/env bash
set -euo pipefail

# Creates a new Agent IO run and points progress/agent_io/QUEUE.md to it.
# Usage:
#   bash scripts/agent-io-new.sh <agent> <topic> [--model MODEL] [--role ROLE]

if [[ $# -lt 2 ]]; then
  echo "Usage: bash scripts/agent-io-new.sh <agent> <topic> [--model MODEL] [--role ROLE]" >&2
  exit 2
fi

AGENT="$1"
TOPIC="$2"
shift 2

MODEL="unspecified"
ROLE="read-only auditor"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="${2:-}"
      shift 2
      ;;
    --role)
      ROLE="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

slugify() {
  tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-'
}

STAMP="$(date +%Y-%m-%d-%H%M)"
AGENT_SLUG="$(printf '%s' "$AGENT" | slugify)"
TOPIC_SLUG="$(printf '%s' "$TOPIC" | slugify)"
RUN_ID="${STAMP}-${AGENT_SLUG}-${TOPIC_SLUG}"
BASE="progress/agent_io"
RUN_DIR="${BASE}/runs/${RUN_ID}"

mkdir -p "$RUN_DIR"

copy_template() {
  local template="$1"
  local output="$2"
  if [[ -f "$template" ]]; then
    sed \
      -e "s/RUN_ID/${RUN_ID}/g" \
      -e "s/AGENT/${AGENT_SLUG}/g" \
      -e "s/MODEL/${MODEL}/g" \
      -e "s/ROLE/${ROLE}/g" \
      "$template" > "$output"
  else
    printf '# %s\n' "$(basename "$output" .md)" > "$output"
  fi
}

copy_template "${BASE}/_TEMPLATE_REQUEST.md" "${RUN_DIR}/REQUEST.md"
copy_template "${BASE}/_TEMPLATE_RESPONSE.md" "${RUN_DIR}/RESPONSE.md"
copy_template "${BASE}/_TEMPLATE_REVIEW.md" "${RUN_DIR}/REVIEW.md"

cat > "${RUN_DIR}/STATUS.md" <<EOF
# STATUS

- Run ID: \`${RUN_ID}\`
- Agent: ${AGENT_SLUG}
- Model: ${MODEL}
- Role: ${ROLE}
- Status: draft
- Request: \`${RUN_DIR}/REQUEST.md\`
- Response: \`${RUN_DIR}/RESPONSE.md\`
- Review: \`${RUN_DIR}/REVIEW.md\`
EOF

cat > "${BASE}/QUEUE.md" <<EOF
# Agent IO Queue

Lightweight queue for external agent interactions. It does not replace \`tasks/queue.json\` or \`progress/NEXT_ACTION.md\`.

## Active Run

- **Run ID:** ${RUN_ID}
- **Status:** draft
- **Agent suggested:** ${AGENT_SLUG}
- **Role:** ${ROLE}
- **Request:** \`${RUN_DIR}/REQUEST.md\`
- **Response:** \`${RUN_DIR}/RESPONSE.md\`
- **Review:** \`${RUN_DIR}/REVIEW.md\`

## Agent Instructions

If \`Run ID\` is \`none\`, answer exactly:

\`\`\`text
No active interaction.
\`\`\`

If \`Run ID\` is not \`none\`:

1. Open the \`Request\` path.
2. Execute only that request.
3. Save the complete output to \`Response\` if you have write access.
4. If you cannot write files, return the complete response so the human can paste it into \`Response\`.
5. Do not write \`Review\`; DANTE-OS/Claude does that.

## Human Instructions

Use this single instruction for the agent:

\`\`\`text
Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.
\`\`\`
EOF

echo "$RUN_ID"
