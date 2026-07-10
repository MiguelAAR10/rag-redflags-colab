# F17b — Qdrant Cloud poblado + Vertex AI + smoke end-to-end

- **Fecha:** 2026-07-10
- **Rama:** v2

## Objetivo
Poblar la base vectorial de producción (Qdrant Cloud) con el corpus estándar,
resolver el acceso a Gemini y validar el pipeline completo en la nube.

## Decisión clave: Vertex AI en lugar de API key
La cuenta Google del usuario usa prepago de AI Studio **agotado**: toda API key
(incluso de proyecto nuevo) devuelve `429 prepayment credits depleted`. Con el
billing GCP vinculado a `rag-redflags-v2` por el usuario, la ruta **Vertex AI +
ADC** funciona de inmediato y es la ideal para Cloud Run (service accounts, sin
API keys). `.env`: `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`,
`GOOGLE_CLOUD_LOCATION`.

## Resultados
- **Qdrant Cloud**: colección `standard_kb` con **299 puntos**
  (gemini-embedding-001 @768, re-normalizado MRL, upsert idempotente uuid5).
- **Gate de recall@5** (13 consultas con indicadores esperados del goldset):
  Gemini/Qdrant **0.718** vs E5/FAISS local **0.718** sobre las MISMAS consultas
  → cero degradación. (El 0.833 de fase7 era una muestra de solo 3 ítems.)
- **Smoke end-to-end**: TDR → Qdrant top-5 (R018 y afines correctos) →
  Gemini 2.5 Flash (Vertex, thinking_budget=0) → analysis/evidence/scoring/
  dossier. Mecánicamente completo.
- **Hallazgo importante**: grounding léxico da 0.094 → refusal, porque la
  respuesta es ES y el corpus EN (solapamiento léxico ≈ 0). Comportamiento
  conservador por diseño, pero para producción el grounding del web debe ser
  por embeddings multilingües (Gemini) → **ítem obligatorio en F18/F20**.

## Archivos
- `scripts/build_qdrant_index.py` (+fix: no usar splitlines() con U+2028 en JSONL)
- `apps/api/app/adapters/google_llm.py` (ruta Vertex + thinking_budget=0)
- `apps/api/app/adapters/llm_factory.py`, `apps/api/app/config.py` (settings Vertex)
- Evidencia: `progress/evidence/f17b-qdrant-index-report.json`,
  `f17b-qdrant-recall.json`, `f17b-e5faiss-recall.json`,
  `f17b-e2e-dossier-gemini-qdrant.json`

## Comandos
`python3 scripts/build_qdrant_index.py` · `--eval` · smoke inline · `verify.sh`
→ **169 passed, 6 skipped**.

## Pendientes
1. Usuario: push del repo Colab (commit `e2384fc` listo en scratchpad).
2. Usuario: Run all en Colab T4 → ragas-report.json definitivo (V1.1).
3. F18: VectorStore interface + QdrantVectorStore en el backend + Neon +
   dedupe + **grounding por embeddings Gemini** (fix cross-lingual).
