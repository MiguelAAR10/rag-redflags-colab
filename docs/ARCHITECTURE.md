# Arquitectura — RAG Agentico

## Capas

```text
User / UI
  -> API Gateway
    -> Agent Runtime
      -> Planner
      -> Retriever
      -> Reranker
      -> Answerer
      -> Verifier
      -> Human Approval
    -> RAG Core
      -> Ingestion
      -> Chunking
      -> Embeddings
      -> Vector Store
      -> Metadata Store
      -> Citation Store
    -> Observability
      -> Runs
      -> Traces
      -> Evals
      -> Audit Log
```

## Diferencia entre RAG normal y RAG agentico

RAG normal:
- pregunta -> retrieval -> respuesta

RAG agentico:
- pregunta -> planner -> decide estrategia -> retrieval iterativo -> verifica evidencia -> responde o pide más datos

## Componentes mínimos

### Ingestion
- Carga documentos.
- Extrae texto.
- Normaliza metadata.
- Guarda versión, fuente y hash.

### Retrieval
- Búsqueda vectorial.
- Búsqueda keyword.
- Filtros por metadata.
- Reranking.
- Deduplicación.

### Answering
- Responde solo con evidencia.
- Expone citas.
- Declara incertidumbre.

### Verification
- Comprueba que cada claim tenga fuente.
- Evalúa cobertura.
- Detecta alucinaciones.
- Bloquea respuestas sin evidencia suficiente.

## Decisión inicial (genérica del starter)

Para un MVP de producción genérico se sugería:
- Backend: FastAPI o Node · Orquestación: LangGraph · DB: Postgres + pgvector · Frontend: Next.js · Testing UI: Playwright MCP.

## Stack REAL del proyecto (override — ver CAVELOG 2026-05-28)

Este proyecto es un **entregable académico en Google Colab**, no un servicio en producción. Por exigencia de la rúbrica, el stack es:

- **Entorno:** Google Colab (GPU T4).
- **LLM (obligatorio):** Qwen — `Qwen2.5-3B-Instruct`.
- **Vector store (obligatorio):** FAISS (`IndexFlatIP`; HNSW como bonus).
- **Embeddings:** multilingües pre-entrenados (`BAAI/bge-m3` o `intfloat/multilingual-e5-base`).
- **Retrieval:** híbrido BM25 + FAISS, con router por familia de red flags.
- **Reranker (bonus):** cross-encoder `BAAI/bge-reranker-v2-m3` (fallback a FAISS top-k).
- **Código reutilizable:** `packages/rag_core/` (importable desde el notebook).

FastAPI/pgvector/LangGraph/Next.js **no se usan** en este proyecto. La verdad funcional vive en `specs/004-redflags-rag.md`.

### Pipeline del proyecto

```
CONTRATO -> [1] extraccion estructurada (Qwen) -> [2] router de familias
         -> [3] retrieval hibrido BM25+FAISS top-20 -> [4] reranker -> top-5
         -> [5] Qwen observaciones con citas -> [6] grounding/verifier (citation-per-sentence)
         -> [7] reporte: senales de riesgo + severidad + citas + "requiere revision humana"
```
