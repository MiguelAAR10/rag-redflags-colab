#!/usr/bin/env bash
set -euo pipefail

echo "== RAG Agentic Harness verify =="

bash scripts/init.sh

# Endurecimiento: el harness no solo debe existir, debe ser usable.
bash scripts/validate-harness.sh

PY="$(command -v python3 || command -v python || true)"

if [ -f "pyproject.toml" ] && [ -n "$PY" ]; then
  echo "-- compileall packages apps --"
  "$PY" -m compileall -q packages apps || true
fi

# Gate de tests: si pytest está disponible y existen tests, los corre (juzga el trabajo de cualquier CLI).
if [ -n "$PY" ] && "$PY" -m pytest --version >/dev/null 2>&1; then
  if find packages apps -name 'test_*.py' -print -quit 2>/dev/null | grep -q .; then
    echo "-- pytest (gate) --"
    "$PY" -m pytest -q || { echo "GATE DE TESTS FALLÓ"; exit 1; }
  fi
fi

if [ -f "package.json" ] && command -v npm >/dev/null 2>&1; then
  npm test --if-present
  npm run lint --if-present
  npm run build --if-present
fi

echo "Verify completed"
echo "Remember: update docs/CAVELOG.md y progress/ (CURRENT_STATE, NEXT_ACTION, runs/) after meaningful work."
