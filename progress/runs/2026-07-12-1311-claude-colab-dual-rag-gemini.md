# Handoff — 2026-07-12-1311 — colab-dual-rag-gemini

## CLI usado
OpenCode

## Objetivo
Agregar al notebook Colab una ruta opcional Gemini/Qdrant sin romper el flujo académico predeterminado FAISS/Qwen.

## Archivos tocados
- `notebooks/redflags_rag_colab.ipynb`
- `packages/rag_core/notebook_rag.py`
- `packages/rag_core/vector_store.py`
- `apps/api/app/adapters/google_llm.py`
- `packages/rag_core/tests/test_notebook_smoke.py`
- `packages/rag_core/tests/test_notebook_rag.py`
- `packages/rag_core/tests/test_vector_store.py`
- `apps/api/tests/test_google_llm.py`
- `docs/COLAB.md`
- `docs/CAVELOG.md`
- `progress/CURRENT_STATE.md`
- `progress/NEXT_ACTION.md`

## Decisiones
- La ruta oficial del notebook sigue siendo `RAG_BACKEND=faiss` + `RAG_GENERATOR=qwen`.
- Gemini/Qdrant queda como demo opcional con Secrets y flags, no como dependencia del `Run all` base.
- Qdrant consulta `standard_kb`; la guía OCP no se sube manualmente desde el notebook.
- Las señales del modo Gemini se validan con doble evidencia: contrato literal + evidencia OCP.

## Comandos ejecutados
```bash
bash scripts/init.sh
python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py apps/api/tests/test_google_llm.py packages/rag_core/tests/test_notebook_rag.py packages/rag_core/tests/test_vector_store.py -q
bash scripts/verify.sh
```

## Resultado
- Notebook actualizado con configuración no interactiva (`RAG_BACKEND`, `RAG_GENERATOR`, `RUN_QDRANT_DEMO`, `RUN_DUAL_RAG_COMPARISON`).
- Sección `6.2` para retrieval dual FAISS/Qdrant.
- Sección `7.2` para generación Gemini opcional usando `generate_fn` y `analyze()`.
- Sección `9.1b` para comparación opcional FAISS vs Qdrant por Recall@5.
- Helper `notebook_rag.py` cubre envelopes `PASS/SKIPPED/ERROR`, comparación y validación dual.
- VectorStore Qdrant ahora valida colección y soporta vector anónimo o nombrado.
- Adaptador Gemini permite cliente falso, modo `strict=True` y errores controlados.

## Evidencia
- Focalizado: `64 passed`.
- Gate completo: `bash scripts/verify.sh` → `258 passed, 6 skipped`.
- `docs/COLAB.md` documenta modo default y Secrets opcionales.

## Riesgos
- No se ejecutó `Run all` real en Colab T4 porque requiere sesión Google autenticada.
- La ruta Qdrant/Gemini real requiere `GEMINI_API_KEY`/`GOOGLE_API_KEY`, `QDRANT_URL` y `QDRANT_API_KEY` en Colab Secrets.

## Próxima acción exacta
Abrir el notebook en Colab T4, correr `Run all` con el modo default FAISS/Qwen y guardar el `ragas-report.json` definitivo.
