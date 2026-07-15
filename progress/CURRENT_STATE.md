# CURRENT_STATE — Estado actual del proyecto

_Actualizar al cerrar cada sesión._

- **Fecha:** 2026-07-14
- **Fase actual:** promoción de V2 a `main` + cierre. El frontend principal Next.js está público en `https://tdr-risk-auditor.vercel.app`, la API FastAPI en `https://tdr-api-x42sfxhyha-uc.a.run.app` y Streamlit permanece como respaldo en `https://tdr-risk-auditor-x42sfxhyha-uc.a.run.app`. La API usa Vertex AI + Qdrant (`standard_kb` 299 puntos y `subject_docs` incremental).
- **Repo Colab (`MiguelAAR10/rag-redflags-colab`) listo para publicar en `main`:** PDF + datos + índice + `ragas_metrics.py` + notebook con fixes de Run all (token opcional no interactivo, celda 2.1 automática, RAGAS léxico, Gradio no bloqueante, ficha unificada, trazabilidad honesta) y ruta opcional Gemini/Qdrant (`RAG_BACKEND=qdrant`, `RAG_GENERATOR=gemini`) sin romper FAISS/Qwen default.
- **Siguiente acción única:** iniciar sesión en Google Colab y correr **Run all en T4** para reemplazar el baseline offline `ragas-report.json`. El agente abrió el notebook y confirmó que Colab exige autenticación para conectar T4.
- **Limitación web declarada:** Qdrant persiste embeddings, pero la metadata usa SQLite en `/tmp` y puede perderse al desplegar una nueva revisión.
- **Gate local de cierre:** `python3 -m pytest -q` → **258 passed, 6 skipped** en 35 s; `npm run lint && npm run build` → 4 rutas de producto + not-found compiladas correctamente.
- Base funcional: F0–F0.4 ✅ · F1.1–F7 ✅ · F8 notebook autorado + smoke gate ✅ · F9 LangChain ✅ · F10 chat Gradio ✅ · F11 `docs/PROYECTO.md` ✅ · F12 prompt auditor/Qwen 4-bit/MiniMax ✅ · F13/F14/F15 evaluación + RAGAS local + trazabilidad ✅.
- **F16 ✅**: TDR Risk Review MVP web desplegado localmente con FastAPI + SQLModel + Jinja2 + Tailwind CDN + Gemini. Contratos multiagente (intake/analysis/evidence/scoring/dossier) reutilizan `packages.rag_core.agent.analyze` con `generate_fn` inyectable. `bash scripts/verify.sh` → **169 passed, 6 skipped**.
- Brecha restante: F15.3 Colab Run all + `ragas-report.json` neural del notebook académico.
- Entregable: `notebooks/redflags_rag_colab.ipynb` con ficha técnica inicial, sección 9 de **RAGAS local**, tabla final de trazabilidad y secciones de instalación, dataset, chunking, embeddings, FAISS/HNSW, retrieval, rerank, Qwen, evaluación, conclusiones, LangChain, chat Gradio/MiniMax opcional, y demo cloud opcional Gemini/Qdrant.
- **F9 (LangChain) ✅**: `packages/rag_core/langchain_rag.py` + gate (3 PASS, 2 skip). Embeddings LangChain en `data/index/langchain_faiss/`.
- **FIX cache de modelos ✅**: `lru_cache` en loaders (anti-recarga/OOM). Notebook limpiado para Colab (token único, LangChain en 11.0, 11.2 opt-in, 10.2 resumen).
- **F10 chat (Gradio) ✅** sobre analyze() (Qwen); MiniMax opcional; FAISS/HNSW con benchmark honesto. `verify.sh` = **104 passed, 6 skipped**.
- **README** reescrito como documento de investigación. **F11 completada:** `docs/PROYECTO.md` existe como base para slides.
- **Agent IO ✅:** `progress/agent_io/` registra prompts/respuestas/reviews de agentes externos; primer run: auditoría MiniMax `2026-06-29-001-minimax-repo-audit`.
- **Sistema multi-CLI por archivos FUNCIONA y se autovalida**: worker vía START_HERE → next-task → produce → `verify.sh` corre el **gate de pytest** (hoy **75 passed, 4 skipped**) → handoff → Claude integra. Cola: `tasks/queue.json` + `scripts/next-task.sh`. Ciclo humano: `docs/LOOP.md`.
- **Modelos = HuggingFace**: e5-base (embeddings) + bge-reranker-v2-m3 (rerank) + Qwen2.5-3B (gen). Token en `.env`. Pendiente Colab: `pip install rank_bm25`.
- **Pendiente Colab:** cargar Qwen real con `RAG_QWEN_4BIT=1`, ejecutar notebook completo en T4, regenerar `progress/evidence/ragas-report.json` con `n=15`, `traps=2` y promedios en `[0,1]`, y guardar evidencia.
- **Spec activa:** `specs/006-tdr-upload-review-mvp.md` (producto web); `specs/004-redflags-rag.md` sigue siendo la fuente del núcleo RAG.

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

F16.2: validar el flujo end-to-end del MVP web con un TDR real usando Gemini y guardar el dossier en `progress/evidence/`. No desarrollar slides; el usuario se encarga.
