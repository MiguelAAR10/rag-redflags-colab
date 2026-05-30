#!/usr/bin/env bash
set -uo pipefail

# Valida que el harness no solo EXISTA sino que sea USABLE por Claude, Codex y OpenCode.
# Evita el "verde falso": archivos presentes pero frontmatter roto o reglas muertas.

FAILED=0
ok ()   { printf '  [OK]   %s\n' "$1"; }
fail () { printf '  [FAIL] %s\n' "$1"; FAILED=$((FAILED+1)); }

# Detecta python (para validar JSON)
PY="$(command -v python3 || command -v python || true)"

# --- helpers de frontmatter ----------------------------------------------
# ¿el archivo abre con '---' en la primera línea?
opens_frontmatter () { [ "$(head -n1 "$1")" = "---" ]; }
# ¿hay un cierre '---' (un segundo '---' después de la línea 1)?
closes_frontmatter () { [ "$(grep -c '^---[[:space:]]*$' "$1")" -ge 2 ]; }
# ¿existe un campo 'clave:' dentro de las primeras 40 líneas (zona de frontmatter)?
has_field () { head -n40 "$1" | grep -Eq "^[[:space:]]*$2:"; }

echo "== validate-harness =="

# 1) Archivos núcleo del harness ------------------------------------------
echo "-- archivos núcleo --"
for f in AGENTS.md docs/MEMORY_INDEX.md docs/CAVEMAN.md \
         docs/MULTI_CLI_PROTOCOL.md docs/MEMORY_PROTOCOL.md docs/START_HERE.md \
         progress/CURRENT_STATE.md progress/NEXT_ACTION.md progress/HANDOFF.md; do
  if [ -f "$f" ]; then ok "existe $f"; else fail "falta $f"; fi
done

# 2) AGENTS.md < 180 líneas ------------------------------------------------
if [ -f AGENTS.md ]; then
  L=$(wc -l < AGENTS.md | tr -d ' ')
  if [ "$L" -lt 180 ]; then ok "AGENTS.md tiene $L líneas (<180)"; else fail "AGENTS.md tiene $L líneas (>=180)"; fi
fi

# 3) Subagentes de Claude --------------------------------------------------
echo "-- .claude/agents/*.md --"
shopt -s nullglob
claude_agents=(.claude/agents/*.md)
if [ ${#claude_agents[@]} -eq 0 ]; then fail "no hay subagentes en .claude/agents/"; fi
for f in "${claude_agents[@]}"; do
  opens_frontmatter  "$f" && ok "$f abre con ---"           || fail "$f NO abre con ---"
  closes_frontmatter "$f" && ok "$f cierra frontmatter ---" || fail "$f sin cierre ---"
  for field in name description tools; do
    has_field "$f" "$field" && ok "$f tiene $field:" || fail "$f sin $field:"
  done
done

# 4) Subagentes de OpenCode ------------------------------------------------
echo "-- .opencode/agent/*.md --"
oc_agents=(.opencode/agent/*.md)
if [ ${#oc_agents[@]} -eq 0 ]; then fail "no hay agentes en .opencode/agent/"; fi
for f in "${oc_agents[@]}"; do
  opens_frontmatter  "$f" && ok "$f abre con ---"           || fail "$f NO abre con ---"
  closes_frontmatter "$f" && ok "$f cierra frontmatter ---" || fail "$f sin cierre ---"
  for field in description mode; do
    has_field "$f" "$field" && ok "$f tiene $field:" || fail "$f sin $field:"
  done
done

# 5) Codex skills (si existen) --------------------------------------------
echo "-- .codex/skills/**/SKILL.md --"
found_skill=0
if [ -d .codex/skills ]; then
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    found_skill=1
    [ -s "$f" ] && ok "$f existe y no está vacío" || fail "$f vacío"
  done < <(find .codex/skills -name SKILL.md | sort -u)
fi
[ "$found_skill" -eq 0 ] && echo "  [info] no hay SKILL.md de Codex (opcional)"

# 6) backlog.json válido ---------------------------------------------------
echo "-- backlog --"
if [ -n "$PY" ]; then
  if "$PY" -c "import json,sys; json.load(open('tasks/backlog.json'))" 2>/dev/null; then
    ok "tasks/backlog.json es JSON válido"
  else
    fail "tasks/backlog.json NO es JSON válido"
  fi
else
  echo "  [info] python no disponible; se omite validación JSON"
fi

# 7) CAVELOG con entrada reciente (heading con año) -----------------------
echo "-- reglas vivas --"
if grep -Eq '^## 20[0-9][0-9]' docs/CAVELOG.md 2>/dev/null; then
  ok "docs/CAVELOG.md tiene entrada fechada"
else
  fail "docs/CAVELOG.md sin entrada fechada (## YYYY...)"
fi

# 8) NEXT_ACTION con UNA sola próxima acción clara ------------------------
if [ -f progress/NEXT_ACTION.md ]; then
  N=$(grep -c '^## Acción' progress/NEXT_ACTION.md)
  if [ "$N" -eq 1 ]; then
    ok "progress/NEXT_ACTION.md tiene exactamente 1 acción (## Acción)"
  else
    fail "progress/NEXT_ACTION.md tiene $N secciones '## Acción' (debe ser 1)"
  fi
fi

# --- resultado ------------------------------------------------------------
echo
if [ "$FAILED" -eq 0 ]; then
  echo "validate-harness: OK (harness usable)"
  exit 0
else
  echo "validate-harness: $FAILED fallo(s). Harness NO listo."
  exit 1
fi
