# Spec 005 — Orquestación Multi-CLI del Pipeline RAG

Estado: activa · Fecha: 2026-05-29 · Owner: arquitecto

## 1. Verdad honesta de orquestación

No hay magia: **un CLI no puede invocar a otro CLI de otro proveedor desde dentro de su propia sesión.** Lo que existe es lo siguiente.

### (a) Workflow de Claude = solo subagentes Claude
El subsistema de subagentes de Claude Code (`.claude/agents/`) **solo lanza más instancias de Claude**. El `coordinator` delega en `spec-planner`, `rag-implementer`, `evaluator`, etc., pero todos son Claude. No puede llamar a Kimi, Qwen, DeepSeek ni MiniMax. Usar esto cuando quieres paralelizar *dentro* del mismo proveedor con roles distintos.

### (b) Multi-proveedor real = OpenCode o dispatcher de archivos
Para usar Kimi / Qwen / DeepSeek / MiniMax de verdad hay dos caminos honestos:
- **OpenCode con varios agentes/sesiones**: OpenCode soporta múltiples proveedores; abres una sesión por modelo (o un agente por modelo) y cada uno toma tareas de la cola. La selección de proveedor es configuración de OpenCode, no una llamada de Claude.
- **Dispatcher de archivos**: cada CLI (Claude, Codex, OpenCode) corre como *worker* independiente, lee su tarea de `tasks/queue.json`, produce un artefacto en disco y hace handoff. La coordinación es **asíncrona vía archivos**, no vía llamadas inter-CLI.

### (c) Patrón híbrido recomendado
- **Claude** = arquitecto/integrador: planifica specs, escribe la cola, corre el gate (`verify.sh`), integra. Internamente usa sus subagentes para subtareas Claude.
- **OpenCode (multi-modelo)** = pool de workers para micro-actividades de implementación; cada modelo barato/especializado toma una actividad atómica.
- **Codex** = revisor/segunda opinión adversarial sobre diffs.
- **Memoria compartida = el filesystem** (`progress/`, `tasks/`, artefactos en `data/`). Ningún CLI confía en el estado mental de otro; todo pasa por archivos + tests.

## 2. Micro-subagentes atómicos del pipeline RAG

Regla: **una actividad por subagente**. Cada uno consume un archivo y emite un archivo, y solo se da por bueno si pasa su test de aceptación.

| Subagente | Entrada | Salida (archivo) | CLI sugerido | Test de aceptación |
|---|---|---|---|---|
| `pdf-loader` | `data/raw/*.pdf` | `data/interim/docs.jsonl` (1 obj/página: `{doc_id,page,text}`) | OpenCode (Qwen) | unit: cada línea es JSON válido con campos requeridos; integration: nº páginas == nº páginas del PDF |
| `chunker` | `data/interim/docs.jsonl` | `data/interim/chunks.jsonl` (`{chunk_id,doc_id,page,text,n_tokens}`) | OpenCode (DeepSeek) | unit: `n_tokens<=max` y solape correcto; integration: 0 chunks vacíos, IDs únicos |
| `embedder` | `data/interim/chunks.jsonl` | `data/interim/embeddings.npy` + `ids.json` | Claude / OpenCode (Kimi) | unit: shape `(n_chunks, dim)`, sin NaN; integration: `len(ids)==n_chunks` |
| `indexer` | `embeddings.npy` + `ids.json` | `data/index/faiss.index` + `meta.json` | Claude | unit: índice carga y `ntotal==n_chunks`; integration: query dummy devuelve k vecinos |
| `retriever` | query + `faiss.index` | `data/interim/retrieved.jsonl` (`{query,chunk_ids,scores}`) | OpenCode (Qwen) | unit: devuelve exactamente top-k; integration: recall@k sobre set dorado >= umbral |
| `router` | query | `data/interim/route.json` (`{query,route,reason}`) | OpenCode (MiniMax) | unit: ruta ∈ enum permitido; integration: queries dorados se enrutan correctamente |
| `reranker` | `retrieved.jsonl` | `data/interim/reranked.jsonl` (orden re-puntuado) | OpenCode (DeepSeek) | unit: misma cardinalidad, scores monótonos; integration: nDCG@k mejora vs retriever |
| `grounder` | query + `reranked.jsonl` | `data/interim/answers.jsonl` (`{query,answer,citations[]}`) | Claude | unit: toda afirmación tiene >=1 `citation` con `chunk_id` existente; integration: 0 citas huérfanas |
| `evaluator` | `answers.jsonl` + set dorado | `progress/eval/report.json` (`{metric,value}[]`) | Claude (evaluator) | unit: métricas presentes y en `[0,1]`; integration: corre sobre N casos sin crash |

Contrato de datos = esquema JSON de cada salida (ver tests). Cambiar un esquema obliga a actualizar el test de su consumidor.

## 3. Cola de tareas en archivos

`tasks/queue.json` — array de tareas. Campos:

```json
[
  {
    "id": "T-001",
    "phase": "ingest",
    "owner_cli": "opencode:qwen",
    "status": "todo",
    "depends_on": [],
    "test_cmd": "pytest tests/test_pdf_loader.py -q"
  }
]
```

- `id`: único, ordenable.
- `phase`: `ingest|index|retrieve|generate|eval`.
- `owner_cli`: `claude` | `codex` | `opencode:<modelo>` (kimi/qwen/deepseek/minimax).
- `status`: `todo` → `doing` → `done` | `blocked` | `failed`.
- `depends_on`: lista de `id`; una tarea solo es elegible si todas sus dependencias están `done`.
- `test_cmd`: comando exacto del gate de esa tarea.

Dispatcher `scripts/next-task.sh`:
- Lee `tasks/queue.json`.
- Filtra tareas `status==todo` cuyas `depends_on` estén todas `done`.
- Opcional: filtra por `--cli <owner>` para que cada worker reclame solo lo suyo.
- Imprime la siguiente tarea (id + test_cmd) y la marca `doing` (escritura atómica: tmp + `mv`).
- Sin tareas elegibles → exit 0 con mensaje "no eligible tasks".

## 4. Gate de validación (ningún CLI se "cree")

Cada micro-actividad tiene dos niveles, ambos obligatorios:
1. **Unit test (contrato de datos)**: valida el esquema/forma de la salida (campos, tipos, rangos, unicidad de IDs). Barato y determinista.
2. **Integration test (end-to-end del módulo)**: el módulo corre sobre datos reales/dorados y cumple su métrica mínima (recall@k, nDCG, 0 citas huérfanas, etc.).

`scripts/verify.sh`:
- Corre todos los `test_cmd` de las tareas `done` (o el suite completo `pytest -q`).
- Si algo falla, revierte la tarea a `failed` y bloquea integración.
- **El "lo hice" de un worker no cuenta**: solo cuenta `verify.sh` verde. La confianza vive en los tests, no en el reporte del CLI.

## 5. Flujo de trabajo

1. Worker (cualquier CLI) abre `docs/START_HERE.md` → contexto mínimo.
2. Lee `progress/NEXT_ACTION.md` (o corre `scripts/next-task.sh --cli <suyo>`).
3. Reclama la tarea (`status: doing`) y **produce solo su artefacto** (la salida de archivo de su micro-subagente).
4. Corre su `test_cmd`. Verde → continúa; rojo → arregla o marca `failed` con nota.
5. Escribe handoff en `progress/runs/YYYY-MM-DD-HHMM-<title>.md` (objetivo, archivos tocados, comandos, resultados, problemas, próximos pasos) y deja la tarea `done` solo si su test pasó.
6. **Claude (integrador) integra solo si `verify.sh` pasa el gate completo.** Si pasa, avanza la fase; si no, devuelve la tarea al pool.

## 6. Reglas de operación

- **Una actividad por subagente**: nada de "haz todo el RAG". Cada tarea = un nodo del pipeline.
- **Lenguaje seguro / honesto**: nunca afirmar que Claude invoca a Kimi/Qwen/DeepSeek/MiniMax directamente. La multi-proveedor pasa por OpenCode o por el dispatcher de archivos.
- **Archivos como memoria**: el estado canónico es el filesystem (`tasks/`, `progress/`, `data/`). Ningún CLI asume el estado interno de otro.
- **Idempotencia**: re-correr una tarea sobre la misma entrada produce la misma salida (o sobreescribe limpio).
- **Escrituras atómicas** en `queue.json` y artefactos (tmp + `mv`) para evitar carreras entre workers.
- **El gate manda**: integración solo tras tests verdes.
