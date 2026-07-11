# F18 — VectorStore + Qdrant en backend + grounding Gemini + dedupe (COMPLETA)

- **Fecha:** 2026-07-11
- **Rama:** v2 (commit `ab7e415`; sync Colab `072198c`)

## Objetivo
Fase completa: el backend web consume la base vectorial de producción
(Qdrant Cloud), el grounding funciona cross-lingüe (cierra V1.2), y el
dedupe por sha256 cumple la spec 006.

## Qué se construyó
1. **`rag_core/vector_store.py`** — interfaz `VectorStore`:
   `FaissVectorStore` (local, envuelve hybrid_search; notebook/tests
   intactos) y `QdrantVectorStore` (producción; client/embed_fn inyectables
   para tests sin red). Factory `make_vector_store("faiss"|"qdrant")`.
2. **`rag_core/gemini_embeddings.py`** — embeddings API reutilizables
   (Vertex ADC o API key; RETRIEVAL_QUERY/DOCUMENT/SEMANTIC_SIMILARITY).
3. **`verifier.py` method="gemini"** — grounding semántico multilingüe en
   2 llamadas batch + matriz numpy. Resuelve respuesta-ES vs corpus-EN.
4. **`agent.py`** — refusal fuera-de-dominio FORZADO deterministamente
   (marcadores de la regla 0) + citas vacías en refusal.
5. **Config** — `RAG_VECTOR_STORE`, `RAG_GROUNDING_METHOD`,
   `grounding_threshold_semantic=0.72`, `rag_retrieval_k`.
6. **Orchestrator** — retrieval vía VectorStore seleccionable; dedupe por
   versión (misma sha256 completada → mismo run; `force=True` re-analiza;
   runs fallidos no bloquean reintento).

## Calibración que definió el diseño (evidencia empírica)
Similitud gemini-embedding-001 contra chunks reales de standard_kb:
- Señales relacionadas (ES): max **0.74–0.81**
- Fuera de dominio (París, cocina): max **0.66–0.69** → umbral **0.72**
- **La propia frase de refusal: 0.757** (menciona "contratación pública")
  → el grounding NO puede ser la única defensa → refusal forzado por
  patrón determinista en `agent.py`. Sin este hallazgo, el texto fuera de
  dominio pasaba con grounding 1.0 (falló la primera contraprueba).

## Resultados E2E (modo producción qdrant+gemini, Gemini 2.5 Flash real)
- TDR con riesgo: grounding **1.0** (antes 0.09 léxico), 3 señales
  aceptadas, evidence sufficient, risk Medio. Dedupe verificado en vivo.
- Fuera de dominio: refusal True, evidence insufficient. ✅
- Evidencia: `progress/evidence/f18-e2e-dossier-qdrant-gemini-grounding.json`
  y `f18-e2e-contrapruebas.json`.

## Gate
`bash scripts/verify.sh` → **187 passed, 6 skipped** (18 tests nuevos).
Fixtures de pipeline/dedupe ahora herméticos (fuerzan faiss/lexical aunque
el `.env` local diga qdrant/gemini).

## Alcance movido
- **Neon Postgres** → F21 (deploy): requiere que el usuario cree la base
  en neon.tech; localmente SQLite funciona idéntico vía SQLModel. Solo es
  cambiar `DATABASE_URL`.

## Pendientes
1. Usuario: **Run all en Colab T4** (V1.1) — todo pusheado, incluido este fix.
2. Usuario (para F21): cuenta Neon + `DATABASE_URL`.
3. F19: intake multi-formato + reindexación inteligente (siguiente fase).
