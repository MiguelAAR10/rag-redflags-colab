#!/usr/bin/env bash
set -euo pipefail

# next-task.sh — imprime la siguiente micro-tarea READY de tasks/queue.json
# Uso: scripts/next-task.sh [owner_cli]
# READY = status=="todo" y todos sus depends_on con status=="done".
# No modifica ningun archivo (no destructivo).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
QUEUE="${REPO_ROOT}/tasks/queue.json"

OWNER="${1:-}"

if [[ ! -f "${QUEUE}" ]]; then
  echo "ERROR: no se encontro ${QUEUE}" >&2
  exit 1
fi

python3 - "${QUEUE}" "${OWNER}" <<'PY'
import json
import sys

queue_path = sys.argv[1]
owner = sys.argv[2] if len(sys.argv) > 2 else ""

with open(queue_path, encoding="utf-8") as fh:
    data = json.load(fh)

tasks = data.get("tasks", [])
status_by_id = {t["id"]: t.get("status") for t in tasks}

def is_ready(task):
    if task.get("status") != "todo":
        return False
    deps = task.get("depends_on", []) or []
    return all(status_by_id.get(dep) == "done" for dep in deps)

candidates = [t for t in tasks if is_ready(t)]
if owner:
    candidates = [t for t in candidates if t.get("owner_cli") == owner]

if not candidates:
    if owner:
        print(f"No hay tareas READY para owner_cli='{owner}'.")
    else:
        print("No hay tareas READY.")
    sys.exit(0)

t = candidates[0]
deps = t.get("depends_on", []) or []
print("Siguiente tarea READY:")
print(f"  id        : {t.get('id')}")
print(f"  phase     : {t.get('phase')}")
print(f"  title     : {t.get('title')}")
print(f"  owner_cli : {t.get('owner_cli')}")
print(f"  status    : {t.get('status')}")
print(f"  depends_on: {', '.join(deps) if deps else '(ninguna)'}")
print(f"  test_cmd  : {t.get('test_cmd')}")
PY
