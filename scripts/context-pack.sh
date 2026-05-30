#!/usr/bin/env bash
set -euo pipefail

# Imprime el CONTEXTO MÍNIMO de arranque de sesión (para pegar a cualquier CLI sin
# cargar el repo entero). No incluye PDF, JSONL, índices ni notebooks.

print_file () {
  if [ -f "$1" ]; then
    echo "===== $1 ====="
    cat "$1"
    echo
  fi
}

echo "########## CONTEXT PACK (mínimo) ##########"
print_file "AGENTS.md"
print_file "docs/MEMORY_INDEX.md"
print_file "progress/CURRENT_STATE.md"
print_file "progress/NEXT_ACTION.md"
print_file "progress/HANDOFF.md"
print_file "specs/004-redflags-rag.md"
echo "########## fin context pack ##########"
echo "Tip: para decisiones previas revisa docs/CAVELOG.md (última entrada)."
