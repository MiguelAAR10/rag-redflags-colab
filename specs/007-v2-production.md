# Spec 007 — V2 Producción: Qdrant + Gemini + Next.js/Vercel + Cloud Run

- **Estado:** ACTIVA (V2). Complementa `specs/006-tdr-upload-review-mvp.md` (F16, base web) y
  NO sustituye a `specs/004-redflags-rag.md` (núcleo RAG académico).
- **Rama:** `v2`
- **Decisión clave (2026-07-10):** el notebook académico `notebooks/redflags_rag_colab.ipynb`
  queda **autosuficiente** (E5 + FAISS + Qwen). Ningún componente del entregable de la UNI
  depende de servicios externos de V2 (Qdrant/Neon). La población de la base vectorial se hace
  con un **script local versionado**, no con celdas de notebook.

## 1. Objetivo

Llevar el TDR Risk Review (F16) a una demo pública: subida multi-formato,
retrieval en una base vectorial gestionada, reindexación inteligente por versión,
Gemini vía Vertex AI, un frontend Next.js en Vercel y una API FastAPI en Cloud Run. Streamlit queda como respaldo. Se elimina Self-RAG
del alcance final porque la base actual con grounding y EvidenceCritic cumple los requisitos.

## 2. Arquitectura

```
Usuario ─▶ Next.js (Vercel) ─HTTP JSON─▶ FastAPI (Cloud Run)
                                          │
                                          ▼
                                     Orquestador Python
          LLM: Gemini 2.5 Flash vía google-genai (F17a ✅)
          Embeddings de query: gemini-embedding-001 (dim 768)
              │
       ┌──────┴──────────┐
       ▼                 ▼
 SQLite /tmp         Qdrant Cloud (free 1GB)
 metadata efímera    · standard_kb — guía OCP (299 chunks)
                     · subject_docs — documentos subidos, versionados
```

### Decisiones y alternativas descartadas
| Decisión | Elección | Descartado / por qué |
|---|---|---|
| Vector DB | Qdrant Cloud free (1 GB) | pgvector/Cloud SQL (costo+ops), Vertex Vector Search (caro) |
| Metadata | SQLite efímero para la demo final | Neon diferido: no fue necesario para demostrar el flujo; el historial visible puede reiniciarse en redeploy |
| Embeddings | `gemini-embedding-001`, `output_dimensionality=768` | `text-embedding-004` (generación anterior, rumbo a deprecación); E5 en contenedor (torso ~2.5GB) — queda como plan B si el recall cae |
| Población del índice | `scripts/build_qdrant_index.py` local | Celdas en notebook (riesgo Run all académico); Colab (innecesario sin GPU) |
| Archivos originales | **No se guardan en MVP**; solo texto extraído en SQLite y chunks en Qdrant | Deuda técnica: el original es evidencia de auditoría; upgrade GCS/R2 en hardening |
| Reranker web | Apagado; recuperación vectorial Qdrant con filtro por familia | bge-reranker CPU (lento); LLM-rerank opcional futuro |
| Frontend | Next.js en Vercel; Streamlit como respaldo | Jinja/Streamlit como interfaz principal: menor separación entre producto y API |

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

### F20 — Cancelada por simplificación
- Sin Self-RAG. Se conserva retrieval Qdrant, grounding semántico, abstención determinista
  y EvidenceCritic. Añadir reflexión no mejora un requisito evaluado y aumenta latencia/costo.

### F21 ✅ — Deploy (proyecto GCP `rag-redflags-v2`, NUNCA `neoc-hr`)
- Dockerfile sin torch; Cloud Run; Vertex AI por identidad del proyecto y secretos Qdrant.
- URL pública y health verificados. Los vectores persisten en Qdrant; la metadata SQLite
  no persiste entre revisiones y queda declarada como limitación.

### F22 ✅ — Frontend de producto + respaldo Streamlit
- Next.js en Vercel: landing, análisis, documentos y explicación del sistema.
- API FastAPI pública en Cloud Run con CORS para el frontend.
- Streamlit permanece disponible como respaldo operativo.
- Flujo público verificado contra Vertex AI + Qdrant.

## 5. Fuera de alcance (V2)
SEACE/OSCE scraping, OCR de escaneados, auth multiusuario, LangGraph, Self-RAG,
RAGAS oficial y almacenamiento de archivos originales.

## 6. Riesgos
| Riesgo | Mitigación |
|---|---|
| Recall cae con gemini-embedding-001 | Gate F17b con goldset; plan B: E5 en contenedor |
| Free tiers (Qdrant 1GB, Neon 500MB, Gemini quota) | Volumen MVP muy por debajo; monitorear en F21 |
| Latencia Gemini en request síncrono | BackgroundTasks en F21; UI con polling |
| Originales no guardados | Deuda registrada; R2/GCS en hardening |
