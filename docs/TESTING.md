# TESTING — Estrategia de tests

> El test es el **juez del trabajo**, sin importar qué CLI lo produjo. No se confía en el
> modelo (Claude, Kimi, Qwen, DeepSeek, MiniMax): se confía en que **el test pase**.
> Si no hay evidencia verificable, la fase no está hecha.

## Principio: gate provider-agnóstico

Cada fase del pipeline tiene un test que define su "contrato". El worker que toma la
tarea (cualquier CLI) escribe código hasta que **su test verde**. El coordinador integra
a `main` solo cuando el gate pasa. El criterio de aceptación vive en el test, no en la
explicación del modelo → el resultado es reproducible y comparable entre CLIs.

## Dispatcher de tareas

- `tasks/queue.json` — cola de fases. Cada entrada trae `id`, `phase`, `owner_cli`,
  `depends_on`, `status` y, clave, **`test_cmd`**: el comando exacto que valida esa fase.
- `scripts/next-task.sh` — dispatcher: selecciona la próxima tarea `todo`/`rework` cuyas
  dependencias están listas y entrega su `test_cmd` al worker.
- `docs/START_HERE.md` — arranque universal de workers (Kimi/Qwen/MiniMax/DeepSeek):
  cargan contexto mínimo, hacen UNA tarea, corren el gate, dejan handoff.

## Unit vs Integration por fase

- **Unit** (fases 1–5): lógica pura y determinista (loaders, chunking, embeddings/FAISS,
  retrieval/router, reranker). Sin red, sin pesos de LLM; fixtures pequeños y aserciones
  sobre estructura/metadata/forma de resultados.
- **Integration** (fases 6–8): pipeline acoplado (Qwen + grounding, evaluación
  end-to-end, smoke del notebook). Pueden mockear el LLM o usar muestras mínimas;
  validan contrato entre etapas, no calidad lingüística.

## Cómo correr

```bash
python -m pytest -q                  # toda la suite
python -m pytest packages/rag_core/tests/test_chunking.py -q   # una fase (test_cmd)
```

`pyproject.toml` fija `testpaths` y `pythonpath`. `verify.sh` ejecuta el gate **cuando
hay tests** (además de `init.sh` + `validate-harness.sh` + `compileall`); si una fase aún
no tiene su test, el harness valida estructura pero la fase no se da por cerrada.

## Fase → qué valida su test

| Fase | test_cmd | Tipo | Qué valida |
|------|----------|------|------------|
| 1.1 Dataset | `test_dataset_contract.py` | unit | Unidades documentales lógicas + metadata obligatoria (`doc_id`, `source_file`, `page_start/end`, `section`, `family`, `hash`) |
| 2 Chunking | `test_chunking.py` | unit | Chunking con overlap, ≥2 tamaños, normalización; preserva metadata |
| 3 Embeddings + FAISS | `test_embeddings_faiss.py` | unit | Embeddings multilingües + índice FAISS (`IndexFlatIP`), dims y búsqueda top-k |
| 4 Retrieval + Router | `test_retrieval_router.py` | unit | Router de familias de red flags + retrieval híbrido (BM25 + FAISS) top-20 |
| 5 Reranker | `test_reranker.py` | unit | Cross-encoder reordena candidatos → top-5 (bonus) |
| 6 Qwen + Grounding | `test_grounding.py` | integration | Generación con citas + verifier (citation-per-sentence), grounding ratio |
| 7 Evaluación | `test_eval.py` | integration | Recall@k / Precision@k + grounding ratio end-to-end |
| 8 Notebook | `test_notebook_smoke.py` | integration | Smoke del notebook de demo sin duplicar lógica de `rag_core` |

(El harness base incluye además `apps/api/tests/test_health.py` como unit de ejemplo.)
