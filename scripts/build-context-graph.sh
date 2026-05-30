#!/usr/bin/env bash
set -euo pipefail
# Genera el grafo de contexto del harness (docs/CONTEXT_GRAPH.md + progress/context-graph.json).
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then echo "python no encontrado"; exit 1; fi
"$PY" scripts/build_context_graph.py
