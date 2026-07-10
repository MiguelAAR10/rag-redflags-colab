# Spec 007 — V2 Producción: Qdrant + Neon + Gemini 2.5 Flash + Cloud Run + Next.js

- **Estado:** ACTIVA (V2). Complementa `specs/006-tdr-upload-review-mvp.md` (F16, base web) y
  NO sustituye a `specs/004-redflags-rag.md` (núcleo RAG académico).
- **Rama:** `v2`
- **Decisión clave (2026-07-10):** el notebook académico `notebooks/redflags_rag_colab.ipynb`
  queda **autosuficiente** (E5 + FAISS + Qwen). Ningún componente del entregable de la UNI
  depende de servicios externos de V2 (Qdrant/Neon). La población de la base vectorial se hace
  con un **script local versionado**, no con celdas de notebook.

## 1. Objetivo

Llevar el TDR Risk Review (F16) a producción real, gratis en free tiers:
subida multi-formato de documentos, embeddings y retrieval sobre una base vectorial
gestionada, reindexación inteligente por versión, técnicas avanzadas nuevas
(multi-query + Self-RAG), backend en Cloud Run y frontend Next.js en Vercel.

## 2. Arquitectura

```
Usuario ─▶ Frontend Next.js 14 + Tailwind + shadcn/ui (Vercel)
              │  fetch /api/*
              ▼
          FastAPI (Cloud Run, contenedor liviano sin torch)
          LLM: Gemini 2.5 Flash vía google-genai (F17a ✅)
          Embeddings de query: gemini-embedding-001 (dim 768)
              │
       ┌──────┴──────────┐
       ▼                 ▼
  Neon Postgres      Qdrant Cloud (free 1GB)
  (metadata:          · standard_kb  — guía OCP (299 chunks, poblada por script)
   tdrs, versions,    · subject_docs — chunks de documentos subidos, versionados
   runs, findings,
   doc_chunks meta,
   change_events)
```

### Decisiones y alternativas descartadas
| Decisión | Elección | Descartado / por qué |
|---|---|---|
| Vector DB | Qdrant Cloud free (1 GB) | pgvector/Cloud SQL (costo+ops), Vertex Vector Search (caro) |
| Metadata | Neon Postgres free | SQLite (FS efímero en Cloud Run), payload-only en Qdrant (pierde relaciones) |
| Embeddings | `gemini-embedding-001`, `output_dimensionality=768` | `text-embedding-004` (generación anterior, rumbo a deprecación); E5 en contenedor (torso ~2.5GB) — queda como plan B si el recall cae |
| Población del índice | `scripts/build_qdrant_index.py` local | Celdas en notebook (riesgo Run all académico); Colab (innecesario sin GPU) |
| Archivos originales | **No se guardan en MVP**; solo texto extraído en Neon | ⚠️ DEUDA TÉCNICA registrada: el original es evidencia de auditoría; upgrade GCS/R2 en hardening |
| Reranker web | Apagado (RRF híbrido + multi-query) | bge-reranker CPU (lento); LLM-rerank opcional futuro |
| Frontend | Next.js 14 + shadcn/ui en Vercel, **solo presentación** | Toda la lógica queda en FastAPI; Jinja2 actual queda como fallback demo |

### Regla invariante
El modelo de embeddings del corpus y el de las queries deben ser EL MISMO
(`gemini-embedding-001` @768) — validado por test de contrato.

## 3. Esquema de datos (Neon, extiende los 5 modelos F16)

- Existentes: `tdrs`, `tdr_versions`, `analysis_runs`, `risk_findings`, `evidence_reviews`.
- Nuevos:
  - `doc_chunks(id, tdr_version_id FK, chunk_hash, ord, text, qdrant_point_id, embedded_at)`
  - `change_events(id, tdr_id FK, from_version_id, to_version_id, chunks_added,
    chunks_removed, chunks_kept, detected_at)`

## 4. Fases y criterios de aceptación

### V1.x — Cierre del entregable académico (ANTES de seguir con V2)
- **V1.1** Run all Colab T4 limpio: fix celda 8 (repo remoto→público o datos embebidos),
  celda 10 (sin upload manual), celda 29 (`grounding_method="lexical"`), celda 39
  (`share=False`/no bloquear). Guardar `progress/evidence/ragas-report.json` definitivo.
- **V1.2** Slides (8 diapositivas de `docs/PROYECTO.md`). Owner: humano.
- **V1.3** Segundo integrante en ficha técnica. Owner: humano.
- ✔️ Aceptación: Run all sin intervención, ragas-report con n=15/traps=2, slides en repo o URL.

### F17a ✅ (hecha, `8d8142b`) — google-genai SDK + gemini-2.5-flash. Gate 169 passed.

### F17b — Script de indexación a Qdrant
- `scripts/build_qdrant_index.py`: lee `data/processed/redflags_chunks.jsonl`, embedea con
  `gemini-embedding-001`@768, upsert a colección `standard_kb` (payload: chunk_id,
  indicator_code, family, page_start/end, text). Idempotente (re-correr no duplica).
- ✔️ 299 puntos en `standard_kb`; Recall@5 goldset Gemini/Qdrant ≥ E5/FAISS local
  (script de comparación; desviación solo con justificación escrita); credenciales solo por env.

### F18 — Backend consume Qdrant + Neon + dedupe
- Interfaz `VectorStore` en `packages/rag_core/vector_store.py`:
  `search(query: str, k, family_filter) -> List[chunk]`. Impls: `FaissVectorStore`
  (envuelve actual; notebook/tests intactos) y `QdrantVectorStore` (query embebida vía API,
  filtro payload por familia). Selección por `VECTOR_STORE_URL`/settings.
- `DATABASE_URL` → Neon; verificación con SQLModel (mismas tablas).
- Fix: `orchestrator.queue_analysis` no re-analiza si el `sha256` de la versión ya tiene
  run `completed` (devuelve el existente).
- ✔️ verify.sh verde sin red (Qdrant mockeado); smoke real end-to-end contra Qdrant+Neon+Gemini
  documentado en `progress/evidence/`.

### F19 — Intake multi-formato + reindexación inteligente
- Registro extractores por extensión: `.pdf` (PyMuPDF, existe), `.docx` (python-docx),
  `.txt`/`.md`. Validación MIME + límites existentes.
- Reindexación: hash doc (no-op si igual) → chunk + hash por chunk → diff vs versión
  anterior → embedear/upsert SOLO nuevos, borrar puntos stale de `subject_docs`,
  registrar `change_event`.
- ✔️ Test: re-subir doc idéntico ⇒ 0 embeddings nuevos; doc con 1 párrafo cambiado ⇒
  solo sus chunks se re-embedean; `change_events` refleja added/removed/kept.

### F20 — Multi-query + Self-RAG
- `expand_queries(query, generate_fn, n=3)` + fusión con `_rrf_fusion` existente; opt-in
  (`multi_query=False` default para no alterar V1).
- `analyze_with_reflection(query, max_iters=2)`: grounding < umbral ⇒ reescritura de query
  informada por oraciones no soportadas + retrieval ampliado ⇒ regenerar; si persiste ⇒
  refusal actual. `reflection_trace` en dossier.
- ✔️ RAGAS local re-corrido; comparación antes/después en `progress/evidence/`;
  las 2 trampas del goldset siguen produciendo refusal.

### F21 — Deploy backend (proyecto GCP `rag-redflags-v2`, NUNCA `neoc-hr`)
- Dockerfile sin torch; Cloud Run; Secret Manager (`GOOGLE_API_KEY`, `QDRANT_*`,
  `DATABASE_URL`); `_execute_run` a BackgroundTasks; unificar `/health`;
  CI/CD GitHub Actions → Artifact Registry → Cloud Run.
- ✔️ URL pública: upload→análisis→dossier real; redeploy no pierde datos (Neon/Qdrant).

### F22 — Frontend Next.js (al final)
- Next.js 14 + Tailwind + shadcn/ui en Vercel sobre `/api/*` existentes: upload
  (drag&drop multi-formato), lista, detalle con run status (polling), dossier con señales
  aceptadas/rechazadas + citas + grounding, feed de change_events. CORS en FastAPI.
- ✔️ Flujo completo desde la URL de Vercel contra Cloud Run.

## 5. Fuera de alcance (V2)
SEACE/OSCE scraping (V2-B, requiere spike de datos — `docs/V2_VIGILANCIA_ACTIVA.md`),
OCR de escaneados, auth multiusuario completa, LangGraph, ragas librería oficial,
almacenamiento de archivos originales (deuda registrada).

## 6. Riesgos
| Riesgo | Mitigación |
|---|---|
| Recall cae con gemini-embedding-001 | Gate F17b con goldset; plan B: E5 en contenedor |
| Free tiers (Qdrant 1GB, Neon 500MB, Gemini quota) | Volumen MVP muy por debajo; monitorear en F21 |
| Latencia Gemini en request síncrono | BackgroundTasks en F21; UI con polling |
| Originales no guardados | Deuda registrada; R2/GCS en hardening |
