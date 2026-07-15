# CURRENT_STATE — Estado actual del proyecto

_Actualizar al cerrar cada sesión._

- **Fecha:** 2026-07-15
- **Colab hardening neural publicado:** `main` en `f582c9b`; la evaluación oficial falla si Qwen/GPU no están disponibles, registra backend/modelo/GPU/commit/tiempos y exporta JSON+CSV+HTML; gate **307 passed, 6 skipped**.
- **Brecha Colab aún abierta:** ejecutar `Run all` autenticado en T4 para reemplazar el baseline offline con outputs neuronales reales.
- **Fase actual:** chat RAG por documento implementado y desplegado. Cada archivo del historial ofrece preguntas aisladas, top de fragmentos, página/sección, grounding, abstención e historial por versión.
- **Chat documental:** `GET/POST /api/tdrs/{tdr_id}/chat`; generación Gemini con prompt específico, retrieval sujeto determinista y guardrail contra instrucciones dentro del documento.
- **Prueba pública del chat:** `ANSWER`, grounding 1.0, 2 citas del mismo archivo, historial 1/1 y `requires_human_review=true`.
- **Demos consultables:** Contraloría, PREDES y PRONIED cargados sin autoanálisis; los dos primeros tienen respuesta fundamentada con páginas y PRONIED demuestra abstención segura.
- **Review-Architect:** `PASS` para MVP académico/demo, **38/45**; no aprobado como plataforma jurídica o de auditoría productiva. Review completa en `progress/reviews/2026-07-15-review-architect-legal-activation.md`.
- **Matriz jurídica:** 6/6 casos PASS; 4 recuperaciones positivas en el régimen correcto y 2 abstenciones seguras. Reporte público JSON en `https://tdr-risk-auditor.vercel.app/legal-activation-report.json`.
- **Trazabilidad:** el contrato local del dossier conserva top-3, score, umbral, decisión, razón, corte de fuente y precisión temporal; `search_legal` excluye fuentes fuera de `valid_from`/`valid_to`.
- **Despliegue frontend:** Vercel deployment `dpl_6EzrF1trqBhJjzq8kzL2oyJ8n5NR`, alias de producción activo.
- **Despliegue API:** Cloud Run `tdr-api-00006-k5f`, 100 % del tráfico; cuenta de despliegue `migarias907@gmail.com`.
- **Integración reproducible:** `apps/api/tests/test_pipeline.py` atraviesa los endpoints HTTP reales y valida documento + OCP + norma temporal. `scripts/e2e_production.py` comprueba Vercel → Cloud Run → Gemini/Qdrant → dossier con autorización de escritura explícita.
- **E2E productivo final:** TDR #2/run #2, riesgo Medio, grounding 1.0, 1 aceptada/0 rechazadas, fecha 2024-03-15 y revisión humana obligatoria.
- **Hallazgo de review:** un caso con tres señales terminó 0/3 aceptadas por dilución del retrieval `top-k=5`; el critic se abstuvo correctamente. Se declara como riesgo de recall, no se oculta relajando citas.
- **Spec activa:** `specs/009-document-chat.md`; specs 008 y 004 continúan como contratos jurídico y académico.
- **Corpus jurídico:** 5 PDF oficiales OECE/OSCE verificados por SHA-256; 1.838 chunks en `data/legal/processed/legal_chunks.jsonl`; routing `LEY_30225` hasta 2025-04-21 y `LEY_32069` desde 2025-04-22.
- **Finding V2:** hecho literal + criterio OCP + fundamento jurídico candidato; prioridad de revisión separada de confianza; abstención explícita sin fecha o sin evidencia legal suficiente.
- **Demos/evaluación:** tres resoluciones del Tribunal son `reference_only` y no tienen botón de análisis; los documentos sujeto son exploratorios y no se usan como gold.
- **Producción:** Vercel `https://tdr-risk-auditor.vercel.app`; Cloud Run previo saludable en `https://tdr-api-x42sfxhyha-uc.a.run.app`.
- **Gate de cierre:** `bash scripts/verify.sh` → **301 passed, 6 skipped**; Vitest **5 passed**, ESLint y build Next.js verdes.
- **E2E público:** fecha 2024-03-15 persistida; R014 aceptado con cita literal; una señal sin R018 fue rechazada y no se reemplazó por R035; sin artículo suficientemente relacionado, la capa legal se abstuvo.
- **Repo Colab (`MiguelAAR10/rag-redflags-colab`) listo para publicar en `main`:** PDF + datos + índice + `ragas_metrics.py` + notebook con fixes de Run all (token opcional no interactivo, celda 2.1 automática, RAGAS léxico, Gradio no bloqueante, ficha unificada, trazabilidad honesta) y ruta opcional Gemini/Qdrant (`RAG_BACKEND=qdrant`, `RAG_GENERATOR=gemini`) sin romper FAISS/Qwen default.
- **Siguiente acción única:** construir el primer caso subject/gold completo sin fuga y publicar su informe de evaluación; detalle en `progress/NEXT_ACTION.md`.
- **Limitación web declarada:** Qdrant persiste embeddings, pero la metadata usa SQLite en `/tmp` y puede perderse al desplegar una nueva revisión.
- **Gate local de cierre:** `bash scripts/verify.sh` → **276 passed, 6 skipped**; entorno Python limpio → **266 passed, 16 skips opcionales**; Vitest, lint y build Next.js verdes.
- **Gate tras la mejora visual RAGAS:** `bash scripts/verify.sh` → **278 passed, 6 skipped**; notebook JSON válido y tres celdas §9.2 compiladas.
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
- **Pendiente Colab:** cargar Qwen real con `RAG_QWEN_4BIT=1`, ejecutar notebook completo en T4, regenerar `progress/evidence/ragas-report.json` con `n=15`, `n_answerable=11`, `traps=4`, promedios en `[0,1]` y outputs visibles por pregunta.
- **Spec activa:** `specs/008-legal-grounding-v2.md`; `specs/006-tdr-upload-review-mvp.md` documenta el MVP web y `specs/004-redflags-rag.md` el núcleo RAG.

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

## Pendiente real de cierre

- Publicar/integrar en `main` la rama de cierre y los cambios locales del notebook.
- Ejecutar `Run all` en Colab T4 y reemplazar el baseline offline por el reporte neural definitivo.
- Auditar la presentación final; el usuario la prepara fuera de este repositorio.

## Foco actual

Construir el primer caso de validación completo sin fuga. Chat, corpus jurídico top-3 y frontend ya están en producción.
