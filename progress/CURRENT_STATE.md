# CURRENT_STATE — Estado actual del proyecto

_Actualizar al cerrar cada sesión._

- **Fecha:** 2026-05-29
- **Fase actual:** F0–F0.4 ✅ · F1.1–F7 ✅ · **F8 notebook autorado (Claude) + smoke gate 5/5** → `in_progress`. Falta: **correr en Colab T4** (humano, `docs/COLAB.md`) + slides aparte.
- Entregable: `notebooks/redflags_rag_colab.ipynb` (10 secciones + **sección 11: validación con LangChain**, 28 celdas).
- **F9 (LangChain) ✅**: `packages/rag_core/langchain_rag.py` + gate (3 PASS, 2 skip). Embeddings LangChain en `data/index/langchain_faiss/`.
- **FIX cache de modelos ✅**: `lru_cache` en loaders (anti-recarga/OOM). Notebook limpiado para Colab (token único, LangChain en 11.0, 11.2 opt-in, 10.2 resumen).
- **F10 chat (Gradio) ✅** sobre analyze() (Qwen); MiniMax opcional; FAISS/HNSW con benchmark honesto. `verify.sh` = **104 passed, 6 skipped**.
- **README** reescrito como documento de investigación (foco RAG avanzado, no harness; logo/docente placeholders). **Próxima: F11** — worker escribe `docs/PROYECTO.md` (base para slides).
- **Sistema multi-CLI por archivos FUNCIONA y se autovalida**: worker vía START_HERE → next-task → produce → `verify.sh` corre el **gate de pytest** (hoy **75 passed, 4 skipped**) → handoff → Claude integra. Cola: `tasks/queue.json` + `scripts/next-task.sh`. Ciclo humano: `docs/LOOP.md`.
- **Modelos = HuggingFace**: e5-base (embeddings) + bge-reranker-v2-m3 (rerank) + Qwen2.5-3B (gen). Token en `.env`. Pendiente Colab: `pip install rank_bm25`.
- **Pendiente Colab:** `pip install rank_bm25` (activa BM25 híbrido); el resto corre local.
- **Spec activa:** `specs/004-redflags-rag.md`

## Qué existe

- Arnés multi-CLI: `AGENTS.md`, `docs/MEMORY_INDEX.md`, `docs/CAVEMAN.md`, `docs/MULTI_CLI_PROTOCOL.md`, `docs/MEMORY_PROTOCOL.md`, `docs/RUBRICA.md`.
- Decisión registrada (CAVELOG 2026-05-29): memoria = archivos (no Graphiti/Neo4j); SDD nativo; GraphRAG solo como bonus futuro.
- Spec del proyecto: `specs/004-redflags-rag.md`.
- Memoria externa: `progress/CURRENT_STATE.md`, `NEXT_ACTION.md`, `HANDOFF.md`, carpetas `runs/`, `reviews/`, `evidence/`.
- Scripts: `init.sh`, `verify.sh` (incluye validación), `validate-harness.sh`, `handoff.sh`, `context-pack.sh`, `build-context-graph.sh`.
- Grafo de contexto: `progress/context-graph.json` + `docs/CONTEXT_GRAPH.md` (32 nodos, 0 huérfanos). Plantilla SDD: `specs/_TEMPLATE-feature.md`.
- Subagentes definidos: `.claude/agents/`, `.opencode/agent/`, `.codex/skills/`.
- Estructura de datos: `data/raw|processed|index/` (vacías).

## Dataset recibido (2026-05-29)

- `data/raw/OCP2024-RedFlagProcurement-1.pdf` — guía OCP 2024 Red Flags, **~100 páginas**, 2 MB. (El sufijo `-1` sugiere posible parte 2 aún no entregada.)
- **Riesgo abierto:** con ~100 pp, alcanzar **≥100 unidades documentales lógicas** es ajustado. Fallback: segmentación fina (indicador + subsección + mapeo OCDS) y, si hace falta, pedir la parte 2 o complementar.
- Local sin librerías PDF (pymupdf/pdfplumber/pypdf) → instalar en Fase 1.

## Qué NO existe todavía (a propósito)

- `packages/rag_core/loaders.py` ✅ existe (1ª pasada; a corregir en F1.1). `data/processed/redflags_units.jsonl` existe (100 unidades, **rechazado**).
- Pipeline RAG restante: `chunkers.py`, `embeddings.py`, `indexing.py`, `retrievers.py`, `rerankers.py`, `verifier.py`, `citations.py`, `agent.py` (pendientes).
- Notebook final, slides.
- El PDF en `data/raw/` (lo aporta el usuario).

## Foco actual

Dejar el arnés listo para desarrollar por fases sin saturar contexto. **No** implementar el pipeline todavía.
