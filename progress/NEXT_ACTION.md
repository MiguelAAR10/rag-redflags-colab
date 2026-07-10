# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**F17b — Poblar Qdrant Cloud desde el notebook Colab con embeddings Gemini y validar recall.**

- **Branch:** `v2`
- **Owner:** Humano (credenciales) + Claude (celdas + validación)
- **Base:** F17a completada (`8d8142b`): adapter en SDK `google-genai`, modelo `gemini-2.5-flash`. Proyecto GCP personal `rag-redflags-v2` creado con Generative Language API habilitada.

## Prerrequisitos del humano (bloquean F17b)

1. Crear la API key de Gemini y guardarla en `.env` sin mostrarla (correr en la sesión con `!`):
   ```bash
   bash -c 'echo "GOOGLE_API_KEY=$(gcloud services api-keys create --display-name=rag-redflags-v2-gemini --api-target=service=generativelanguage.googleapis.com --project=rag-redflags-v2 --account=migarias907@gmail.com --format="value(response.keyString)")" >> .env'
   ```
2. Crear cluster **free** en https://cloud.qdrant.io (login con migarias907@gmail.com) y añadir a `.env`:
   `QDRANT_URL=...` y `QDRANT_API_KEY=...`

## Objetivo

Celdas nuevas en `notebooks/redflags_rag_colab.ipynb` (sección V2): embedear el corpus estándar (299 chunks) con `gemini-embedding-001`, crear colección `standard_kb` en Qdrant Cloud con payload (`chunk_id`, `indicator_code`, `family`, `page_start/end`, `text`), upsert, y correr recall vs goldset comparando E5/FAISS vs Gemini/Qdrant. Gate: recall no se degrada; si cae, plan B = E5 en el contenedor.

## Criterios de aceptación

- [ ] Colección `standard_kb` con 299 puntos en Qdrant Cloud.
- [ ] Recall@5 goldset Gemini/Qdrant ≥ E5/FAISS (o desviación justificada por escrito).
- [ ] Smoke real de `analyze()` con Gemini 2.5 Flash (`generate_fn` API) sin GPU.
- [ ] `bash scripts/verify.sh` sigue verde (169 passed baseline).

## NO hacer

- No borrar las celdas E5/FAISS del notebook (entregable académico V1 intacto).
- No hardcodear credenciales en celdas ni código; solo env/Colab secrets.
- No usar el proyecto GCP `neoc-hr` (es del trabajo); todo en `rag-redflags-v2`.
- No afirmar corrupción ni ilegalidad; mantener lenguaje seguro.

## Después de F17b (tareas registradas #3–#7)

F18 backend→Qdrant + Neon + dedupe · F19 multi-formato + reindexación inteligente · F20 multi-query + Self-RAG · F21 Cloud Run · F22 frontend React (al final).
