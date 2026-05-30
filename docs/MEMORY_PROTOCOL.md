# MEMORY_PROTOCOL — Memoria inteligente sin saturar contexto

> Regla de oro: **"Si no está en un archivo, no existe."**
> La ventana de contexto del LLM es **volátil y cara**. La memoria real del proyecto vive en archivos MD/JSON versionados, legibles por **cualquier** CLI (Claude, Codex, OpenCode) **sin servidor ni claves**.

## 1. Por qué archivos y NO una base de datos de grafos

Evaluado y descartado para la memoria del harness (sí útil como bonus de análisis, ver §6):

- **Graphiti / Neo4j / FalkorDB**: requieren BD de grafos corriendo + API LLM para extraer entidades + embeddings. Aportan infra, costo, no-determinismo y una **segunda fuente de verdad**. Sobre-ingeniería para un proyecto académico acotado.
- **CodeGraph**: pensado para navegar codebases grandes. Aquí basta `docs/MEMORY_INDEX.md` + grep/glob.

Ventajas de archivos planos: deterministas, versionados en git (historia + diff), CLI-agnósticos, cero infra, auditables por el humano.

## 2. Capas de memoria (qué es cada archivo)

| Capa | Qué es | Archivos | Cambia |
|---|---|---|---|
| **L0 · Constitución** | reglas inviolables del proyecto | `AGENTS.md`, `docs/CAVEMAN.md` | casi nunca |
| **L1 · Spec (fuente de verdad)** | qué se construye y por qué | `specs/004-redflags-rag.md`, `docs/RUBRICA.md` | por decisión (con CAVELOG) |
| **L2 · Estado** | dónde estamos y qué sigue | `progress/CURRENT_STATE.md`, `progress/NEXT_ACTION.md`, `progress/HANDOFF.md` | cada sesión |
| **L3 · Historia** | qué pasó y por qué | `docs/CAVELOG.md`, `progress/runs/`, `progress/reviews/` | append-only |
| **L4 · Evidencia/Datos** | outputs reproducibles | `progress/evidence/`, `data/processed/`, `data/index/` | por fase |

## 3. Presupuesto de contexto (context budget)

Al **arrancar** cualquier sesión cargar **solo** el context-pack (≈6 archivos):

```bash
bash scripts/context-pack.sh
```

Eso carga L0 + L1 + L2 (AGENTS, MEMORY_INDEX, CURRENT_STATE, NEXT_ACTION, HANDOFF, spec activa). **Nada más.**

**Prohibido pegar al chat:** PDF, `.jsonl` grandes, índices FAISS, outputs de embeddings, notebooks ejecutados, logs largos. Si necesitas datos del PDF/JSONL, **trabájalos por código** y guarda un **reporte/muestra** en `progress/evidence/`; luego lee el reporte, no el archivo crudo.

## 4. Las 4 reglas operativas

1. **Write-through**: toda decisión/resultado se escribe a un archivo *en el momento*, no se "guarda en la cabeza" del modelo. Decisión → `CAVELOG`. Resultado → `progress/runs/`. Métrica → `progress/evidence/`.
2. **Delegación = aislar contexto**: las lecturas pesadas (PDF, exploración amplia) se delegan a un **subagente**; su contexto se descarta al terminar y solo devuelve un **resumen estructurado** que se escribe a archivo. El coordinador nunca carga el material pesado.
3. **Una actividad por sesión**: no mezclar fases. Si la ventana se llena → cerrar con handoff y abrir sesión nueva que reanuda **solo desde archivos**.
4. **Reanudación desde archivos**: cualquier CLI retoma leyendo L2 (`CURRENT_STATE` → `NEXT_ACTION` → `HANDOFF`). El chat anterior es irrelevante.

## 5. Ciclo de vida de una sesión

```
START → bash scripts/context-pack.sh        (cargar memoria mínima)
WORK  → ejecutar UNA actividad de NEXT_ACTION
WRITE → CAVELOG + progress/runs + evidence   (write-through)
VERIFY→ bash scripts/verify.sh               (incluye validate-harness)
HANDOFF→ bash scripts/handoff.sh "faseXX" <cli>
END   → actualizar CURRENT_STATE + NEXT_ACTION
```

La siguiente sesión (de cualquier CLI) arranca de cero en contexto y reconstruye todo desde los archivos. **El conocimiento no se pierde aunque se cierre el chat.**

## 5.bis Grafo de contexto (navegación inteligente del repo)

En vez de una BD de grafos (Graphiti/Neo4j) o un grafo MCP — que serían una 2.ª fuente de verdad y solo legibles por clientes MCP — el harness genera un **grafo determinista de su propia documentación**:

```bash
bash scripts/build-context-graph.sh
```

Produce `progress/context-graph.json` (nodos=archivos, aristas=referencias) y `docs/CONTEXT_GRAPH.md` (Mermaid). **Cualquier CLI** lo lee para saber qué abrir sin cargar todo, y detecta **docs huérfanos**. Regenerarlo tras cambios estructurales en docs/specs. Es un archivo versionado, no memoria del modelo.

## 6. (Opcional, futuro) Memoria/Analítica con grafo — solo como BONUS del dominio

Si más adelante quieres "memoria inteligente" de verdad, el lugar correcto **no** es el harness sino el **análisis de red flags como GraphRAG**: construir un grafo de entidades del dominio (comprador, proveedor, licitación, adjudicación, persona) y relaciones (`adjudicado_a`, `posee`, `oferta_en`) para detectar patrones relacionales (mismo proveedor ganando, oferentes con dueño común, clusters comprador–proveedor). Ahí Graphiti/Neo4j sí aportan. Queda como extensión avanzada fuera del MVP de la rúbrica (ver `specs/004` §5 bonus).

## 7. SDD (Spec-Driven Development) — cómo este harness ya lo implementa

SDD = la **spec es la fuente de verdad** y el código se valida contra ella.

| Etapa SDD | En este harness |
|---|---|
| Constitution | `AGENTS.md` + `docs/CAVEMAN.md` |
| Specify | `specs/004-redflags-rag.md` (+ `docs/RUBRICA.md`) |
| Plan | sección de fases en la spec / `docs/MULTI_CLI_PROTOCOL.md` |
| Tasks | `tasks/backlog.json` (F0–F8) |
| Implement | `packages/rag_core/`, notebook |
| Verify | `scripts/verify.sh` + `scripts/validate-harness.sh` |

Existe la opción de adoptar el toolkit estándar **GitHub Spec Kit** (`specify init`, comandos `/speckit.specify`, `/plan`, `/tasks`, `/implement`, estructura `.specify/`). Decisión pendiente: usarlo tal cual **o** mantener SDD nativo en este harness (una sola fuente de verdad). Ver `docs/CAVELOG.md`.
