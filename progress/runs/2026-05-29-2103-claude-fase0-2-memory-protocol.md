# Handoff — 2026-05-29-2103 — fase0-2-memory-protocol

## CLI usado
Claude

## Objetivo
Endurecer la memoria del proyecto para no depender del contexto del LLM, y decidir sobre Graphiti / CodeGraph / SDD.

## Archivos tocados
- docs/MEMORY_PROTOCOL.md (nuevo): capas L0–L4, presupuesto de contexto, write-through, ciclo de sesión, SDD, nota GraphRAG.
- AGENTS.md (enlace al protocolo + context-pack)
- docs/MEMORY_INDEX.md (fila "Memoria / no saturar contexto")
- scripts/validate-harness.sh (exige CAVEMAN, MULTI_CLI_PROTOCOL, MEMORY_PROTOCOL)
- docs/CAVELOG.md (entrada Fase 0.2), progress/CURRENT_STATE.md

## Decisiones
- Memoria del harness = archivos MD/JSON (NO Graphiti/Neo4j/FalkorDB; NO CodeGraph).
- Graphiti reservado solo como posible bonus de dominio (GraphRAG de red flags), fuera del MVP.
- SDD adoptado nativo en el harness; pendiente decidir si se instala GitHub Spec Kit.

## Comandos ejecutados
```bash
bash scripts/verify.sh            # exit=0
bash scripts/handoff.sh "fase0-2-memory-protocol" claude
```

## Resultado
Protocolo de memoria documentado y enforced por validate-harness. Veredicto técnico sobre Graphiti/CodeGraph/SDD registrado en CAVELOG con base en docs actuales (Context7: /getzep/graphiti, /github/spec-kit).

## Evidencia
- verify.sh exit=0; validate-harness "OK (harness usable)".

## Riesgos
- Si se adopta Spec Kit, no duplicar estructura con specs/ + progress/.

## Próxima acción exacta
Decidir ruta SDD (Spec Kit tool vs nativo) y alcance de GraphRAG (bonus/no). Después: Fase 1 — dataset (PDF → ≥100 unidades). Ver progress/NEXT_ACTION.md.
