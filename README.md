# 🚩 RAG Agéntico para Señales de Riesgo en Contratación Pública

Sistema **Retrieval-Augmented Generation (RAG) agéntico** que analiza un contrato/licitación y emite **señales de riesgo potenciales** (red flags) fundamentadas en la guía *OCP 2024 — Red Flags for Procurement*, citando la fuente y el dato del contrato.

> ⚠️ El sistema **no afirma corrupción**: señala *riesgos potenciales* y toda salida **requiere revisión humana**.

Proyecto final de maestría (GenAI). Entregable: **notebook de Google Colab** con Qwen.

## Arquitectura

```
CONTRATO
  → router (familia: planeación / competencia / adjudicación / ejecución)
  → retrieval híbrido (BM25 + FAISS) top-20
  → reranker cross-encoder (bge-reranker-v2-m3) → top-5
  → generación Qwen2.5-3B-Instruct (grounded en los chunks)
  → verificación de grounding (soporte por frase) + citas por frase
  → REPORTE: señales de riesgo + severidad + citas + "requiere revisión humana"
```

**Modelos (HuggingFace):** `intfloat/multilingual-e5-base` · `BAAI/bge-reranker-v2-m3` · `Qwen/Qwen2.5-3B-Instruct`.

## Cómo correrlo (Google Colab)

El entregable es [`notebooks/redflags_rag_colab.ipynb`](notebooks/redflags_rag_colab.ipynb). Pasos detallados en [`docs/COLAB.md`](docs/COLAB.md):
1. Colab → Runtime → **GPU T4**.
2. Editar `REPO_URL` (celda 1.2) + añadir secret `HF_TOKEN`.
3. Subir el PDF de la guía OCP cuando lo pida.
4. **Run all.**

## Estructura

| Carpeta | Contenido |
|---|---|
| `packages/rag_core/` | Pipeline: `loaders, chunkers, embeddings, indexing, retrievers, rerankers, agent, verifier, citations` |
| `packages/evals/` | Métricas (Recall@k, Precision@k, grounding, ROUGE/BLEU) + gold set |
| `notebooks/` | Notebook de Colab (entregable) |
| `data/` | `raw/` PDF (no versionado) · `processed/` unidades+chunks · `index/` FAISS · `eval/` gold set |
| `specs/` · `docs/` · `progress/` · `tasks/` | Arnés de ingeniería (specs, decisiones, estado, cola de tareas) |

## Desarrollo multi-CLI (harness)

Construido por fases con varios CLIs coordinados por archivos: **Claude** coordina/integra/revisa; **Kimi K2 / DeepSeek / MiniMax** implementan; cada fase se valida con un **gate de tests** (`bash scripts/verify.sh`, hoy 95 tests). Ver `docs/MULTI_CLI_PROTOCOL.md`, `docs/MEMORY_PROTOCOL.md` y `docs/LOOP.md`.

```bash
bash scripts/init.sh      # valida estructura
bash scripts/verify.sh    # gate de calidad (estructura + pytest)
```

## Cobertura de la rúbrica

Dataset real · chunking comparado + análisis · embeddings justificados · FAISS (Flat + **HNSW**) · pipeline completo + diagrama · grounding · evaluación. **Bonus:** HNSW, Hybrid BM25+FAISS, cross-encoder reranker, citation-per-sentence, comparación de métodos, ROUGE/BLEU.
