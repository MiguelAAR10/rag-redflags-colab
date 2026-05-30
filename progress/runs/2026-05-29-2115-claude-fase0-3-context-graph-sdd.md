# Handoff — 2026-05-29-2115 — fase0-3-context-graph-sdd

## CLI usado
Claude

## Objetivo
Dar "memoria/navegación inteligente" del repo (grafo de docs que el agente alcanza) sin romper el principio de archivos planos, y formalizar SDD nativo.

## Archivos tocados
- scripts/build_context_graph.py + scripts/build-context-graph.sh (nuevos)
- progress/context-graph.json + docs/CONTEXT_GRAPH.md (generados)
- specs/_TEMPLATE-feature.md (plantilla SDD spec→plan→tasks)
- docs/MEMORY_PROTOCOL.md (§5bis grafo) + docs/MEMORY_INDEX.md (fila grafo)
- docs/CAVELOG.md (entrada 0.3) + progress/CURRENT_STATE.md

## Decisiones
- Navegación = grafo determinista de NUESTROS docs (opción C), no Graphiti/Neo4j (A) ni grafo MCP (B).
- SDD nativo; no se instala GitHub Spec Kit (evitar 2.ª estructura paralela).

## Comandos ejecutados
```bash
bash scripts/build-context-graph.sh   # 32 nodos, 124 aristas, 0 huérfanos
bash scripts/verify.sh                # exit=0
bash scripts/handoff.sh "fase0-3-context-graph-sdd" claude
```

## Resultado
El agente puede "alcanzar" un grafo navegable del proyecto (`progress/context-graph.json`) y un diagrama (`docs/CONTEXT_GRAPH.md`), regenerable con un comando, legible por cualquier CLI. Trade-offs Graphiti/MCP/CodeGraph-lite documentados en CAVELOG.

## Evidencia
- context-graph: 32 nodos, 124 aristas, 0 huérfanos.
- verify.sh exit=0; validate-harness OK.

## Riesgos
- Regenerar el grafo tras cambios estructurales (no acoplado a verify).

## Próxima acción exacta
Fase 1 — colocar PDF en data/raw/ y procesarlo en ≥100 unidades documentales (ver progress/NEXT_ACTION.md). CLI: OpenCode/Codex; reviewer: Claude.
