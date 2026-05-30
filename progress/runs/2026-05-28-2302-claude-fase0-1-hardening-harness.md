# Handoff — 2026-05-28-2302 — fase0-1-hardening-harness

## CLI usado
Claude

## Objetivo
Endurecer la verificación del harness (evitar "verde falso") antes de Fase 1: validar que agentes y reglas sean USABLES, no solo que existan.

## Archivos tocados
- scripts/validate-harness.sh (nuevo)
- scripts/verify.sh (integra validate-harness.sh tras init.sh)
- docs/CAVELOG.md (entrada Fase 0.1)
- progress/CURRENT_STATE.md (Fase 0+0.1 completadas; lista validate-harness)
- tasks/backlog.json (nueva tarea F0.1-HARDENING = done)

## Errores encontrados / corregidos
- **Frontmatter de subagentes:** NINGÚN error real. Lo reportado como `---ls: Read...` era visualización UTF-8 de acentos (é/ñ/ó) bajo `cat -A`, no corrupción. Todos los `.claude/agents/*.md` y `.opencode/agent/worker.md` tienen frontmatter válido.
- **Bug propio detectado y corregido:** el glob `.codex/skills/**/SKILL.md` contaba el SKILL.md dos veces (bash sin globstar). Cambiado a `find ... | sort -u`.

## Comandos ejecutados
```bash
bash scripts/init.sh              # OK
bash scripts/validate-harness.sh  # OK (harness usable)
bash scripts/verify.sh            # exit=0
bash scripts/handoff.sh "fase0-1-hardening-harness" claude
```

## Resultado
`validate-harness.sh` valida: AGENTS.md <180 líneas; MEMORY_INDEX/CURRENT_STATE/NEXT_ACTION/HANDOFF presentes; frontmatter (apertura/cierre `---` + campos) de cada agente Claude (name/description/tools) y OpenCode (description/mode); SKILL.md Codex no vacío; backlog JSON válido; CAVELOG fechado; NEXT_ACTION con exactamente 1 `## Acción`. Integrado en `verify.sh`. Todo en verde.

## Evidencia
- Salida: 30+ checks `[OK]`, 0 `[FAIL]`, "validate-harness: OK (harness usable)".
- `verify.sh` exit=0.

## Riesgos
- "CAVELOG reciente" solo comprueba que exista heading fechado, no la fecha exacta.
- PDF aún no está en `data/raw/` → Fase 1 sigue bloqueada.

## Próxima acción exacta
Fase 1 — colocar el/los PDF(s) en `data/raw/` y procesarlos en ≥100 unidades documentales lógicas → `data/processed/redflags_units.jsonl` (ver `progress/NEXT_ACTION.md`). CLI: OpenCode/Codex; reviewer: Claude.
