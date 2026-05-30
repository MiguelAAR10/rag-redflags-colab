#!/usr/bin/env bash
set -euo pipefail

echo "== RAG Agentic Harness init =="

# Detecta python o python3
PY="$(command -v python3 || command -v python || true)"

required=(
  "AGENTS.md"
  "CLAUDE.md"
  "docs/ARCHITECTURE.md"
  "docs/CAVELOG.md"
  "docs/CAVEMAN.md"
  "docs/MEMORY_INDEX.md"
  "docs/MULTI_CLI_PROTOCOL.md"
  "docs/RUBRICA.md"
  "docs/MCP_POLICY.md"
  "docs/SECURITY_MODEL.md"
  "specs/001-product-brief.md"
  "specs/004-redflags-rag.md"
  "progress/CURRENT_STATE.md"
  "progress/NEXT_ACTION.md"
  "progress/HANDOFF.md"
  "progress/runs"
  "tasks/backlog.json"
)

for path in "${required[@]}"; do
  if [ ! -e "$path" ]; then
    echo "Missing required path: $path"
    exit 1
  fi
done

echo "Structure OK"

if [ -n "$PY" ]; then
  "$PY" - <<'PY'
import json
from pathlib import Path
json.loads(Path("tasks/backlog.json").read_text())
print("Backlog JSON OK")
PY
else
  echo "WARN: python no encontrado; se omite validacion JSON"
fi

echo "Init OK"
