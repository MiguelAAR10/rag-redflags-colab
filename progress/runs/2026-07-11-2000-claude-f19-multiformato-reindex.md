# F19 — Intake multi-formato + reindexación inteligente (COMPLETA)

- **Fecha:** 2026-07-11
- **Rama:** v2 (`bf3ecb3`)

## Qué se construyó
1. **Multi-formato**: registro `EXTRACTORS` en `intake.py` — PDF (existente),
   **DOCX nuevo** (python-docx, párrafos + tablas), TXT/MD. Formato no
   soportado → 400 con mensaje claro. Esto convierte en verdad la fila de
   trazabilidad que la auditoría V1 marcó como inconsistente.
2. **Reindexación inteligente** (`services/reindex.py` + modelos
   `DocChunk`/`ChangeEvent`):
   - Chunking determinista por párrafos SIN overlap (el overlap invalidaría
     los hashes vecinos al editar un párrafo).
   - Diff por sha256 de chunk vs versión anterior.
   - Solo los chunks NUEVOS se embeben (Gemini) y upsertean a `subject_docs`
     en Qdrant; los intactos reutilizan su punto; los eliminados se borran.
   - `ChangeEvent(from,to,added,removed,kept)` — el esquema CDC de spec 007
     que la V2-B (vigilancia SEACE) reutilizará tal cual.
3. **API**: `POST /api/tdrs/{id}/upload` (re-subida): mismo sha → `unchanged`
   no-op; distinto → versión + diff + evento (+ `auto_analyze` opcional).
4. Flag `RAG_INDEX_SUBJECT_DOCS` (off en tests/dev, on en prod .env).

## Verificación
- Tests: **10 nuevos** deterministas (chunking estable, diff localizado,
  DOCX real generado en test, no-op, evento con conteos, embeddings
  incrementales con fakes). Gate: **208 passed, 6 skipped**.
- E2E real contra Qdrant Cloud (`f19-e2e-reindex.json`): editar 1 cláusula
  de 15 → **1 solo chunk re-embebido**, 1 reutilizado, 1 punto borrado,
  ChangeEvent registrado; re-subida idéntica → no-op; `subject_docs` = 2
  puntos vigentes exactos.

## Estado de fases
F17a ✅ · F17b ✅ · F18 ✅ · **F19 ✅** · P0 auditoría ✅ ·
F20 (Self-RAG + dual grounding + abstention gate) → siguiente ·
F21 (deploy; requiere Neon del usuario) · F22 (React, al final) ·
V1.1 (Run all Colab) → usuario.
