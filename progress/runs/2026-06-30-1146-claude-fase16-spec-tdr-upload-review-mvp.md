# Handoff — 2026-06-30-1146 — fase16-spec-tdr-upload-review-mvp

## CLI usado
OpenCode

## Objetivo
Abrir F16 con una spec de producto web desplegable para subir TDR y generar dossiers verificables, incorporando el feedback CTO sobre deploy sin GPU, análisis asíncrono y EvidenceCritic visible.

## Archivos tocados
- `specs/006-tdr-upload-review-mvp.md`
- `progress/NEXT_ACTION.md`
- `progress/CURRENT_STATE.md`
- `docs/MEMORY_INDEX.md`
- `docs/CAVELOG.md`
- `progress/HANDOFF.md`
- `progress/runs/2026-06-30-1146-claude-fase16-spec-tdr-upload-review-mvp.md`

## Decisiones
- F16 queda abierta con spec activa `specs/006-tdr-upload-review-mvp.md`.
- El MVP será una web FastAPI + SQLite + HTML simple donde se sube un TDR PDF/texto y se genera un dossier de señales de riesgo potenciales.
- No se implementa SEACE, Neo4j, LangGraph, OCR avanzado ni Next.js en F16.
- La demo-web no debe intentar correr Qwen-3B/e5/reranker en tier gratis CPU; F16.1 debe definir `generate_fn` por API/fake y tests deterministas.
- EvidenceCritic es feature visible del dossier: señales aceptadas/rechazadas por evidencia, citas, `grounding_ratio`, `refusal`.
- El análisis se modela con estados asíncronos desde el inicio, aunque V1 use una ejecución simple.

## Comandos ejecutados
```bash
bash scripts/init.sh
bash scripts/verify.sh
bash scripts/handoff.sh "fase16-spec-tdr-upload-review-mvp"
```

## Resultado
Quedó definida la siguiente etapa de producto para el final de curso: TDR Upload Review MVP multiagent-ready. La memoria operacional apunta a F16.1 como siguiente acción única.

## Evidencia
- `specs/006-tdr-upload-review-mvp.md` creada con alcance, arquitectura, contratos de agentes, modelo de datos conceptual, API mínima, criterios de aceptación y fuera de alcance.
- `progress/NEXT_ACTION.md` tiene exactamente una acción: F16.1 demo-web sin GPU.
- `bash scripts/verify.sh` → 148 passed, 6 skipped.

## Riesgos
- F15.3 Colab Run all sigue pendiente como evidencia neural del notebook.
- F16.1 debe resolver temprano la decisión de `generate_fn` API/fake para no descubrir el problema de deploy al final.
- PDFs escaneados/OCR quedan diferidos; la demo debe declarar que funciona mejor con PDFs basados en texto.

## Próxima acción exacta
Implementar F16.1: contrato demo-web sin GPU usando `agent.analyze(..., generate_fn=...)`, tests con fake determinista y estados de análisis `uploaded|queued|running|completed|failed`.
