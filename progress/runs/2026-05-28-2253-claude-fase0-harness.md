# Handoff — 2026-05-28-2253 — fase0-harness

## CLI usado
Claude

## Objetivo
Construir el harness multi-CLI (contexto, memoria, verificación, subagentes) para desarrollar el RAG de red flags por fases sin saturar contexto. NO implementar el pipeline.

## Archivos tocados
- AGENTS.md (reescrito: contrato común multi-CLI, lenguaje seguro, contexto mínimo)
- CLAUDE.md (orden de lectura → MEMORY_INDEX primero)
- docs/MEMORY_INDEX.md, docs/CAVEMAN.md, docs/MULTI_CLI_PROTOCOL.md, docs/RUBRICA.md (nuevos)
- docs/ARCHITECTURE.md (override de stack: Colab+Qwen+FAISS)
- docs/CAVELOG.md (entrada Fase 0)
- specs/004-redflags-rag.md (nuevo, spec activa)
- progress/CURRENT_STATE.md, NEXT_ACTION.md, HANDOFF.md, runs/_TEMPLATE.md (nuevos)
- scripts/init.sh (fix: valida progress/ + usa python3), verify.sh, handoff.sh, context-pack.sh
- .claude/agents/{coordinator(actualizado),spec-planner,dataset-engineer,rag-implementer,evaluator} (nuevos)
- .opencode/agent/worker.md (nuevo)
- tasks/backlog.json (reescrito por fases F0–F8)
- Carpetas: progress/{runs,reviews,evidence}, data/{raw,processed,index} con .gitkeep

## Decisiones
- Stack del proyecto = Colab + Qwen2.5-3B + FAISS (override del FastAPI/pgvector genérico). → CAVELOG.
- "documento" = unidad documental lógica (≥100) del PDF; chunking va después. → spec 004.
- Multi-CLI: Claude coordina/integra, Codex implementa/audita, OpenCode worker. → MULTI_CLI_PROTOCOL.
- Lenguaje seguro obligatorio (señales de riesgo / revisión humana).

## Comandos ejecutados
```bash
chmod +x scripts/*.sh
bash scripts/init.sh     # Structure OK / Backlog JSON OK / Init OK
bash scripts/verify.sh   # Verify completed
bash scripts/handoff.sh "fase0-harness" claude
```

## Resultado
Harness completo y verificable. `init.sh` (que antes fallaba por falta de `progress/runs` y por usar `python`) ahora pasa. `verify.sh` pasa. Subagentes y memoria externa listos.

## Evidencia
- Salida de init/verify: "Structure OK", "Backlog JSON OK", "Verify completed".
- Estructura creada confirmada con `find progress data .opencode`.

## Riesgos
- PDF aún no está en data/raw/ → Fase 1 bloqueada hasta que el humano lo coloque.
- Convención `.opencode/agent/` verificada vía Context7; revisar si cambia entre versiones de OpenCode.

## Próxima acción exacta
Fase 1 — procesar el PDF en ≥100 unidades documentales lógicas (ver progress/NEXT_ACTION.md). CLI: OpenCode/Codex; reviewer: Claude.
