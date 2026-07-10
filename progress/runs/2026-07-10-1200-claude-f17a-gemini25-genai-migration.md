# F17a — Migración a google-genai SDK + Gemini 2.5 Flash + setup GCP

- **Fecha:** 2026-07-10
- **Rama:** v2

## Objetivo
Arrancar V2 (plan Qdrant Cloud + Gemini + Cloud Run): línea base commiteada,
adapter migrado al SDK vigente y modelo subido a Gemini 2.5 Flash.

## Archivos tocados
- `apps/api/app/adapters/google_llm.py` — SDK `google-genai` (genai.Client,
  `system_instruction` nativo; se elimina el turno falso "Entendido.").
  Default `gemini-2.5-flash`, `max_output_tokens=2048`.
- `apps/api/app/config.py` — `rag_gemini_model="gemini-2.5-flash"`.
- `.env.example` — `RAG_GEMINI_MODEL=gemini-2.5-flash` + `QDRANT_URL`/`QDRANT_API_KEY`.
- `pyproject.toml` — dep `google-generativeai` → `google-genai`.
- `.gitignore` — `data/tdr_review.db`, `data/uploads/`.

## Comandos ejecutados
- Commit línea base `3a941f6` (84 archivos F13–F16 pendientes) + commit F17a `8d8142b`.
- `bash scripts/verify.sh` → **169 passed, 6 skipped** (igual a baseline).
- GCP (cuenta migarias907@gmail.com ya autenticada en gcloud):
  `gcloud projects create rag-redflags-v2` ✅ y
  `gcloud services enable generativelanguage.googleapis.com` ✅.

## Problemas
- La creación automática de la API key Gemini fue bloqueada por el modo de
  permisos (credencial viva). La debe crear el usuario (comando en NEXT_ACTION).
- El proyecto gcloud activo por defecto es `neoc-hr` (trabajo) — NO usar para
  este proyecto; todo va a `rag-redflags-v2`.

## Próximos pasos
1. Usuario: crear API key Gemini (comando en NEXT_ACTION) → `.env` como `GOOGLE_API_KEY`.
2. Usuario: crear cluster free en https://cloud.qdrant.io → `QDRANT_URL`/`QDRANT_API_KEY` en `.env`.
3. F17b: celdas Colab → embeddings `gemini-embedding-001` + upsert a Qdrant
   (colección `standard_kb`) + validación de recall vs goldset.
4. F18–F22 según tareas registradas (Qdrant backend, multi-formato +
   reindexación inteligente, multi-query + Self-RAG, Cloud Run, React al final).
