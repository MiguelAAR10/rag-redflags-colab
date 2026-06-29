---
run_id: 2026-06-29-001-minimax-repo-audit
created_at: 2026-06-29T00:00:00
agent: minimax
model: MiniMax-M3
role: read-only repository auditor
mode: read-only
status: sent
source: dante-os
related_task: none
related_spec: specs/004-redflags-rag.md
---

# REQUEST

## Objetivo

Auditar el estado real del repositorio y detectar desincronizaciones entre memoria operacional, tareas, handoffs, documentacion y spec activa.

## Contexto obligatorio a leer

1. `AGENTS.md`
2. `docs/MEMORY_INDEX.md`
3. `progress/CURRENT_STATE.md`
4. `progress/NEXT_ACTION.md`
5. `progress/HANDOFF.md`
6. `docs/CAVELOG.md`
7. `specs/004-redflags-rag.md`
8. `tasks/queue.json`
9. `README.md`
10. `docs/PROYECTO.md`
11. `docs/COLAB.md`
12. `docs/RUBRICA.md`

## No leer completo

- `data/raw/*.pdf`
- `data/processed/*.jsonl`
- `data/index/*`
- `notebooks/redflags_rag_colab.ipynb`

## Preguntas

1. Cual es el estado real del proyecto hoy?
2. Que esta completo, incompleto o desincronizado?
3. Que riesgos bloquean la entrega final?
4. Que evidencia existe para sostener cada afirmacion?
5. Cual debe ser la proxima unica accion recomendada?

## Formato esperado

1. Resumen ejecutivo
2. Estado confirmado
3. Contradicciones o desincronizaciones
4. Riesgos bloqueantes para entrega
5. Brechas contra la spec 004
6. Proxima unica accion recomendada
7. Evidence packet
8. Limites de la auditoria

## Reglas

- No modificar archivos.
- No inventar metricas.
- Citar rutas exactas.
- Separar confirmado, inferido, desconocido y bloqueante.
- Si algo requiere Colab, marcarlo como no verificado localmente.
- No imprimir secretos.
