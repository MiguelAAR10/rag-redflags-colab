#!/usr/bin/env bash
set -euo pipefail

# Crea un handoff en progress/runs/ a partir de la plantilla y actualiza progress/HANDOFF.md
# Uso: bash scripts/handoff.sh "fase1-dataset" [cli]
#   cli (opcional): claude | codex | opencode   (default: claude)

TITLE="${1:-sesion}"
CLI="${2:-claude}"
SLUG="$(echo "${CLI}-${TITLE}" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
STAMP="$(date +%Y-%m-%d-%H%M)"
OUT="progress/runs/${STAMP}-${SLUG}.md"
TEMPLATE="progress/runs/_TEMPLATE.md"

mkdir -p progress/runs

if [ -f "$TEMPLATE" ]; then
  sed -e "s/<FECHA>/${STAMP}/" -e "s/<FASE>/${TITLE}/" "$TEMPLATE" > "$OUT"
else
  printf '# Handoff — %s — %s\n\n## CLI usado\n%s\n\n## Objetivo\n\n## Próxima acción exacta\n' \
    "$STAMP" "$TITLE" "$CLI" > "$OUT"
fi

# Actualiza el puntero en HANDOFF.md
{
  echo "# HANDOFF — Punto de retoma más reciente"
  echo
  echo "- **Último handoff:** \`${OUT}\`"
  echo "- **CLI:** ${CLI}"
  echo "- **Fase/título:** ${TITLE}"
  echo "- **Para retomar:** lee \`AGENTS.md\` → \`progress/CURRENT_STATE.md\` → \`progress/NEXT_ACTION.md\` → spec activa."
} > progress/HANDOFF.md

echo "Handoff creado: $OUT"
echo "Edítalo y completa Resultado/Evidencia/Riesgos/Próxima acción."
