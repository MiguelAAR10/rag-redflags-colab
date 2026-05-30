# Handoff — 2026-05-29-2132 — fase0-4-fleet-onboarding

## CLI usado
Claude

## Objetivo
Adaptar el harness a la flota real (Claude + Kimi/Qwen/MiniMax/DeepSeek) y permitir arrancar workers sin pegar prompts largos.

## Archivos tocados
- docs/START_HERE.md (nuevo): bootstrap universal de workers; el humano solo dice "Lee docs/START_HERE.md y ejecuta lo pendiente".
- docs/MULTI_CLI_PROTOCOL.md (§1 flota real + roles + ahorro de tokens)
- AGENTS.md (roles flota + puntero a START_HERE)
- scripts/validate-harness.sh (exige START_HERE)
- docs/CAVELOG.md, progress/CURRENT_STATE.md, progress/NEXT_ACTION.md (PDF recibido)

## Decisiones
- Roles: Claude coordina/integra; Kimi/DeepSeek implementan; MiniMax/Qwen worker barato; Qwen = LLM del RAG.
- La actividad pendiente vive SIEMPRE en NEXT_ACTION.md; START_HERE no cambia.

## Comandos ejecutados
```bash
bash scripts/build-context-graph.sh   # 33 nodos, 138 aristas, 0 huérfanos
bash scripts/verify.sh                # exit=0
bash scripts/handoff.sh "fase0-4-fleet-onboarding" claude
```

## Resultado
Cualquier worker (Kimi/DeepSeek/MiniMax/Qwen) arranca leyendo docs/START_HERE.md → ejecuta NEXT_ACTION → verify → handoff, sin re-explicar el proyecto y sin pegar prompts. PDF OCP (~100 pp) recibido.

## Evidencia
- verify.sh exit=0; validate-harness OK; START_HERE enforced.

## Riesgos
- Workers necesitan CLI con acceso a archivos (OpenCode) o paste de context-pack.
- ~100 pp vs ≥100 unidades: segmentar fino o parte 2.

## Próxima acción exacta
Fase 1 — Kimi o DeepSeek: PDF data/raw/OCP2024-RedFlagProcurement-1.pdf → ≥100 unidades en data/processed/redflags_units.jsonl (instalar pymupdf primero). Ver progress/NEXT_ACTION.md.
