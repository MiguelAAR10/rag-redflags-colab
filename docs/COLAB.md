# COLAB — Cómo entregar y correr el notebook

El entregable es `notebooks/redflags_rag_colab.ipynb`. Corre en **Google Colab con GPU T4**.

## 1. Abrir la versión publicada

- Repositorio: `https://github.com/MiguelAAR10/rag-redflags-colab`
- Colab: `https://colab.research.google.com/github/MiguelAAR10/rag-redflags-colab/blob/main/notebooks/redflags_rag_colab.ipynb`

El PDF autorizado para el proyecto, los `.jsonl` procesados y el índice FAISS están incluidos en esta entrega. El notebook no solicita subir archivos durante `Run all`.

## 2. Abrir en Colab
1. Inicia sesión en Google.
2. **Runtime → Change runtime type → GPU (T4)**.
3. Opcional: en **Secrets (🔑)** añade `HF_TOKEN`. Qwen2.5-3B es público y la celda no pide entrada manual si falta.
4. **Runtime → Run all.** No edites celdas durante la corrida.
5. Al terminar, descarga `progress/evidence/ragas-report.json` y reemplaza el baseline offline del repositorio.

### Modo predeterminado evaluado

El notebook corre por defecto con:

- `RAG_BACKEND=faiss`
- `RAG_GENERATOR=qwen`

Ese es el flujo académico principal: OCP automático → E5/FAISS → retrieval híbrido/rerank → Qwen → grounding/citas → RAGAS local.

### Modo cloud opcional: Qdrant + Gemini

Para probar la ruta opcional con API, añade en **Secrets (🔑)**:

- `GEMINI_API_KEY` o `GOOGLE_API_KEY`
- `QDRANT_URL` o `QDRANT_ENDPOINT`
- `QDRANT_API_KEY`

Y activa solo las celdas opcionales con variables de entorno:

- `RAG_GENERATOR=gemini` para generación Gemini sobre los chunks recuperados.
- `RAG_BACKEND=qdrant` para consultar `standard_kb` en Qdrant.
- `RUN_QDRANT_DEMO=1` para mostrar Qdrant aunque el backend principal sea FAISS.
- `RUN_DUAL_RAG_COMPARISON=1` para comparar Recall@5 FAISS vs Qdrant.

Si faltan Secrets, esas celdas imprimen `SKIPPED` y el `Run all` base sigue funcionando con FAISS/Qwen. No pegues claves en celdas ni en salidas.

## 3. Para los slides (aparte)
- Captura: el diagrama del pipeline (celda 0), la tabla de chunking (3.1), la comparación de métodos (9.1) y la demo final (10.1).
- Estructura de 8 secciones en `docs/RUBRICA.md`.

## Notas
- BM25 se activa porque Colab instala `rank_bm25` (celda 1.1); en local estaba desactivado.
- Qwen2.5-3B y el grounding `embedding` dan ratios realistas en GPU (en local se usa fallback).
- Gemini/Qdrant es una demostración cloud opcional; no reemplaza el requisito Qwen del notebook.
- La ejecución T4 requiere una sesión Google autenticada; los tests locales validan estructura y ausencia de prompts, pero no sustituyen el `Run all` completo.
