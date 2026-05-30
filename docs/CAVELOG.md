# CAVELOG

Bitácora de decisiones, avances y evidencia. (Append-only; lo más reciente arriba.)

## 2026-05-30 — Fase 9: RAG con LangChain para validar la data (Claude)

### Decisión
- Añadida vía **LangChain** en paralelo a `rag_core`, para consultar/validar la data desde el notebook. API verificada vía Context7 (langchain_community.FAISS, langchain_huggingface.HuggingFaceEmbeddings, create_retrieval_chain, HuggingFacePipeline).
- Nuevo `packages/rag_core/langchain_rag.py` (imports perezosos): `chunks_to_documents`, `build_vectorstore` (save_local), `load_vectorstore`, `get_retriever` (filtro por familia), `quick_query`, `build_qa_chain`, `get_qwen_llm`. Prompt con lenguaje seguro.
- **Embeddings — dónde se guardan:** rag_core crudo en `data/index/redflags_flatip.index` (+ mapping); LangChain en `data/index/langchain_faiss/` (`index.faiss` + `index.pkl`) vía `FAISS.save_local`. Mismos chunks, mismo e5-base.
- Notebook: nueva **sección 11 (Validación con LangChain)** (retriever + cadena Qwen) + deps langchain en la celda de instalación.

### Evidencia
- Gate `test_langchain_rag.py`: 3 PASS (mapeo metadata, imports perezosos, lenguaje seguro) + 2 skip (integración LangChain → Colab). Smoke notebook 5/5. `queue.json` F9 = done.

### Riesgos
- LangChain no instalado en local (integración hace skip); se valida en Colab con `pip install langchain langchain-community langchain-huggingface`.

### Próximos pasos
- Correr el notebook en Colab (F8b) — ahora incluye la validación LangChain.



## 2026-05-30 — Fase 8: Notebook de Colab (Claude)

### Decisión
- **Notebook armado por Claude**: `notebooks/redflags_rag_colab.ipynb` (25 celdas, 10 secciones de la rúbrica), refleja las APIs reales de `rag_core` (load_pdf → chunk_units → embed_texts → build_index → hybrid_search/route_family → rerank → analyze(Qwen) → grounding/citas → evaluate_on_goldset/compare_methods) + diagrama + demo + lenguaje seguro.
- **Gate F8** `test_notebook_smoke.py` (5 tests): valida nbformat v4, 10 secciones, uso de APIs reales, Qwen2.5-3B + "revisión humana", celdas no vacías. 5/5 PASS.
- Estrategia de entrega: **GitHub + clone** (`docs/COLAB.md`); el notebook regenera datos/índice en Colab y pide subir el PDF (gitignored).
- Slides: **aparte** (decisión del usuario). F8 queda `in_progress` hasta correr en Colab T4 (humano).

### Próximos pasos
- Fase 8b — humano corre el notebook en Colab T4 (ver `progress/NEXT_ACTION.md`). Luego slides.

## 2026-05-30 — Review/Integración Fase 7 (Claude): APROBADA → F8 (implementación COMPLETA)

### Decisión
- **Fase 7 APROBADA**: gate `test_eval.py` 15/15 PASS. goldset 12 items (query/relevant_indicator_codes/relevant_families); `recall_at_k/precision_at_k/mean_grounding_ratio/compare_methods` + ROUGE/BLEU bonus. `verify.sh` = **90 passed, 4 skipped**, exit=0.
- Reporte: R@3=R@5=0.833, P@3=0.44, grounding 0.305 (léxico); ejemplo bueno (R@5=1.0) y malo (R@5=0.5) con explicación.
- `queue.json` F7 y `backlog` F7 → `done`. **Todas las fases de implementación (F1.1–F7) DONE.**
- F8 (notebook+slides) = entregable calificado, owner **claude**.

### Próximos pasos
- Fase 8 — notebook Colab (10 secciones) + slides (8, 7 min). Lo arma Claude.

## 2026-05-30 — Fase 7: Evaluación cuantitativa + cualitativa (DeepSeek)

### Decisión
- **Fase 7 IMPLEMENTADA**: 3 archivos creados:
  - `data/eval/goldset.jsonl`: 12 queries con `relevant_indicator_codes` verificados contra dataset (69 códigos únicos).
  - `packages/evals/metrics.py`: `recall_at_k`, `precision_at_k`, `mean_grounding_ratio`, `compare_methods`, BONUS `_try_rouge_bleu`.
  - `packages/rag_core/tests/test_eval.py`: 15 tests (11 unitarios deterministas + 2 gold set validation + 1 integración).
- Gold set validado: 12 items, cada código existe en el dataset de 69 indicadores.
- Comparación de métodos: FAISS, hybrid, hybrid+rerank top-5.
- Reporte JSON + MD con ejemplo BUENO (R@5=1.0) y MALO (R@5=0.5).
- Evaluación completa del gold set (12 items) pendiente para Colab (tiempo de embedding/cross-encoder).
- `verify.sh` = **90 passed, 4 skipped**, exit=0.

### Evidencia
- `progress/evidence/fase7-eval-report.json` y `.md`: R@3=0.833, R@5=0.833 en muestra de 3 queries (FAISS/hybrid/rerank idénticos sin BM25).
- Gold set: 12 items verificados, >10 requeridos.

### Riesgos
- Sin BM25 instalado, FAISS/hybrid/rerank producen métricas idénticas. En Colab con `rank_bm25`, la comparación tendrá más varianza.
- Evaluación de 3 queries por tiempo de reranker local. El gold set completo se corre en Colab.

### Próximos pasos
- Fase 8 — Notebook final de Colab + slides.

## 2026-05-30 — Fase 6: Qwen + Grounding + Citas (DeepSeek)

### Decisión
- **Fase 6 IMPLEMENTADA**: 3 módulos creados:
  - `packages/rag_core/agent.py` — `analyze(query, generate_fn=None, retrieved_chunks=None)` orquestra retrieve→rerank→generate→verify→cite. Acepta inyección de `generate_fn` para tests falsos y `retrieved_chunks` para saltar retrieval. Qwen2.5-3B-Instruct vía transformers como runtime (carga lazy).
  - `packages/rag_core/verifier.py` — `split_sentences` + `verify_grounding` (léxico y embedding) + `refusal_check` ("no hay evidencia suficiente").
  - `packages/rag_core/citations.py` — `build_citations` mapea frases soportadas a `chunk_id`, `indicator_code`, `indicator_name`, `page_start/end`.
- SYSTEM_PROMPT con lenguaje seguro incrustado: nunca afirmar corrupción, usar "señal de riesgo"/"red flag potencial"/"posible irregularidad", terminar con "Requiere revisión humana", citar fuentes.
- Gate `test_grounding.py`: 15 tests (12 unitarios deterministas con LLM fake + chunks dummy + 3 integración con FAISS real).
- `verify.sh` = **75 passed, 4 skipped**, exit=0.

### Evidencia
- `progress/evidence/fase6-grounding-report.json`: 3 contratos de prueba (bid_rigging, delays, clean). Router asigna familias correctamente. Fallback minimal_analysis genera salida segura (grounding_ratio bajo con léxico, esperado sin Qwen real — en Colab con Qwen será alto).
- Tests unitarios verifican: split_sentences, verify_grounding (supported/not/rejection), refusal_check, build_citations, safe language en SYSTEM_PROMPT, analyze con LLM fake inyectado.

### Riesgos
- Qwen2.5-3B (~6GB) no está descargado localmente. El fallback `_minimal_analysis` genera observaciones básicas desde los chunks recuperados.
- En Colab T4, Qwen cabrá y el grounding con embeddings (no léxico) dará ratios más realistas.
- El grounding léxico (determinista) es solo para tests; en producción usar `method="embedding"`.

### Próximos pasos
- Fase 7 — Evaluación cuantitativa y cualitativa (Recall@k, Precision@k, grounding_ratio, análisis comparativo).

## 2026-05-30 — Review/Integración Fase 5 (Claude): APROBADA → F6

### Decisión
- **Fase 5 APROBADA**: gate `test_reranker.py` 7 PASS + 1 skip; `rerank` con fallback graceful (try/except → candidatos originales), CrossEncoder bge-reranker-v2-m3, reordena top-5 (4/5 cambian en "bid rigging"). `verify.sh` = 60 passed, 4 skipped, exit=0.
- `queue.json` F5 y `backlog` F5 → `done`.
- **F6 reasignada `qwen` → `deepseek`** como IMPLEMENTADOR. Aclaración consignada: **Qwen2.5-3B es el LLM de runtime que el código invoca** (Colab), no el coder. Desbloquea F6.

### Próximos pasos
- Fase 6 — agent.py + verifier.py + citations.py (DeepSeek): generación Qwen + grounding por frase + citation-per-sentence + lenguaje seguro + refusal. Gate `test_grounding.py` con LLM fake (determinista) + skip Qwen real.

## 2026-05-30 — Fase 5: Reranker cross-encoder (MiniMax)

### Decisión
- **Fase 5 IMPLEMENTADA**: `packages/rag_core/rerankers.py` creado con `rerank(query, candidates, top_n=5)` usando `BAAI/bge-reranker-v2-m3`.
  - Fallback graceful: si el modelo no carga o predict falla, devuelve candidatos originales sin romper.
  - Cada resultado añade `rerank_score` y preserva toda la metadata del candidato.
- `load_candidates_from_faiss(query, k=20)` helper para cargar candidatos directamente desde retrievers.py (usado en integración).
- Gate `test_reranker.py`: 7 unitarios deterministas (SIEMPRE corren con fake cross-encoder) + 1 integración con modelo real.
- `verify.sh` = **60 passed, 4 skipped**, exit=0.

### Evidencia
- `progress/evidence/fase5-reranker-report.json`: 3 queries probadas; cross-encoder reordena el top-5 en todos los casos (diferencia visible entre hybrid y reranked).
  - "bid rigging": hybrid top-5 vs reranked top-5 difieren en 4/5 chunks.
  - "contract delays": difieren en 2/5 chunks.
  - "award selection": difieren en 3/5 chunks.

### Riesgos
- El modelo bge-reranker-v2-m3 (~390MB) carga en ~1-2s; el predict es rápido (~100ms para 20 pairs). Aceptable en Colab T4.
- Sin GPU el cross-encoder corre en CPU; en Colab con T4 es viable.

### Próximos pasos
- Fase 6 — Qwen + Grounding (`packages/rag_core/agent.py` + `verifier.py` + `citations.py`).

## 2026-05-30 — Fase 4: Retrieval híbrido + router de familias (Kimi K2)

### Decisión
- **Fase 4 IMPLEMENTADA**: `packages/rag_core/retrievers.py` creado con:
  - `bm25_search(query, k)` usando `rank_bm25.BM25Okapi` (opcional; graceful fallback si no instalado).
  - `faiss_search(query, k)` reutiliza `embeddings.py` + `indexing.py` con oversample cuando hay `family_filter`.
  - `hybrid_search(query, k, family=None, fusion_method='rrf'|'weighted')` combina ambos vía **Reciprocal Rank Fusion** (default) o suma ponderada normalizada.
  - `route_family(query) -> list[str]` clasificador determinista por keywords (EN/ES) con fallback a embeddings de descripciones de familia.
  - Cada resultado devuelve metadata completa: `chunk_id, score, family, indicator_code, indicator_name, page_start, page_end, text`.
- Gate `test_retrieval_router.py`: 14 tests unitarios deterministas (SIEMPRE corren) + 3 integration tests con skip graceful si faltan deps.
- `verify.sh` = **53 passed, 3 skipped** (exit=0).

### Evidencia
- `progress/evidence/fase4-retrieval-report.json`: 299 chunks, router mapea correctamente 5 queries de prueba a familias, FAISS real devuelve top-5 con scores 0.80–0.86.
- Filtrado por familia acota resultados (ej. `contract delays` → `planeacion`=1, `adjudicacion`=1).
- `run_phase4.py` genera reporte automático (similar a Fase 3 runner).

### Riesgos
- `rank_bm25` no está instalado en el entorno local → BM25 real desactivado; en Colab se instalará (`pip install rank_bm25`). El código ya lo maneja.
- FAISS search real con modelo e5-base tarda ~6–15s por query en CPU; en Colab T4 será más rápido.
- El filtro por familia en FAISS usa oversample (k*5); con 299 vectores es seguro, pero si el dataset escala se requiere sub-índices por familia o filtrado nativo de FAISS.

### Próximos pasos
- Fase 5 — Reranker cross-encoder (`packages/rag_core/rerankers.py`).

## 2026-05-29 — Review/Integración Fase 3 (Claude): APROBADA → F4

### Decisión
- **Fase 3 APROBADA**: gate `test_embeddings_faiss.py` 16/16 PASS + verificación Claude (índice real `data/index/redflags_flatip.index`, ntotal=299, d=768, `intfloat/multilingual-e5-base`, IndexFlatIP, mapping 299). `verify.sh` = **39 passed**, exit=0.
- `queue.json` F3 y `backlog` F3 → `done`. 
- **F4 reasignada de `claude` → `kimi`** para cuidar tokens de Claude (retrieval+router es código; el gate lo valida igual). Claude sigue como integrador/reviewer.

### Evidencia
- faiss 1.14.2 + sentence-transformers 5.5.1 instalados. `next-task.sh kimi` → F4-retrieval-router.

### Próximos pasos
- Fase 4 — retrieval híbrido (BM25+FAISS) + router de familias (Kimi) con gate `test_retrieval_router.py`.

## 2026-05-29 — Review/Integración Fase 2 (Claude): APROBADA → F3

### Decisión
- **Fase 2 APROBADA**: gate `test_chunking.py` 12/12 PASS + spot-check de Claude (299 chunks, 5 familias heredadas, overlap real verificado, chunk_index secuencial). `verify.sh` = 23 passed (10 dataset + 12 chunking + 1 health), exit=0.
- `queue.json` F2 y `backlog` F2 → `done`. Desbloquea **F3-embeddings-faiss** (DeepSeek).
- NEXT_ACTION reescrito para F3 (modelo multilingüe + FAISS Flat/HNSW; token HF leído desde `.env`, nunca hardcodear).

### Evidencia
- `next-task.sh deepseek` → F3 READY. Chunks input: `data/processed/redflags_chunks.jsonl` (1024/128).

### Próximos pasos
- Fase 3 — embeddings + FAISS (DeepSeek) con gate `test_embeddings_faiss.py`.

## 2026-05-29 — Fase 3: Embeddings + FAISS (DeepSeek)

### Decisión
- `packages/rag_core/embeddings.py` creado: `embed_texts(texts) -> np.ndarray` con `SentenceTransformer` + normalización L2.
  - Modelo: `intfloat/multilingual-e5-base` (278M, 768-dim, multilingüe EN/ES).
  - Prefijos `passage:` / `query:` automáticos para modelo e5.
  - Token HF leído de `HF_TOKEN` env var o `.env`, nunca hardcodeado.
- `packages/rag_core/indexing.py` creado: FAISS `IndexFlatIP` baseline + HNSW bonus.
  - `build_index`, `search`, `save_index`, `load_index`, `build_mapping`, `resolve_chunk_ids`.
  - Mapping `faiss_id → chunk_id` persistible.
- `packages/rag_core/tests/test_embeddings_faiss.py`: 16 tests (12 unitarios deterministas + 4 integración con modelo real).
  - Tests unitarios siempre corren (dummy numpy + FAISS), sin GPU ni modelo.
  - Round-trip: embed → index → search → resolve chunk_ids verificado.

### Evidencia
- `data/index/redflags_flatip.index`: 299 vectores 768-dim, IndexFlatIP.
- `data/index/chunk_id_mapping.json`: mapping faiss_id → chunk_id.
- `progress/evidence/fase3-embeddings-report.json`: modelo, dim=768, 299 vectores, 85.3s embedding, normas=1.0.
- `pytest -q` → 39 passed (16 F3 + 12 F2 + 10 F1 + 1 extra). `verify.sh` verde.

### Riesgos
- Modelo e5-base (278M) ocupa ~1.1 GB en RAM; en Colab T4 cabe holgadamente.
- IndexFlatIP es búsqueda exacta O(n·d); con 299 vectores es instantánea. HNSW sería útil si el dataset escala.

### Próximos pasos
- Fase 4 — Retrieval + Router: `packages/rag_core/retrievers.py` con BM25 + FAISS híbrido, router por familia.

## 2026-05-29 — Fase 2: Chunking comparativo con overlap (Kimi K2)

### Decisión
- `packages/rag_core/chunkers.py` creado con `chunk_units(units, size, overlap) -> list[dict]`.
  - Chunking por límite de palabra (no corta palabras).
  - Overlap configurado: texto compartido al final de chunk N y al inicio de chunk N+1.
  - Metadata heredada: cada chunk conserva `family`, `indicator_code`, `indicator_name`, `block_type`, `page_start/end` del padre.
  - `chunk_id` único por hash MD5 del texto; `chunk_index` secuencial por padre.
  - Textos cortos (≤size) generan un solo chunk sin trocear.
- Comparación de ≥2 tamaños documentada: small (512/64), medium (1024/128), large (2048/256).
  - Chunks generados: 472 (small), 299 (medium), 249 (large).
  - Fragmentación: 54.9% (small), 16.9% (medium), 4.2% (large) de unidades trozadas.
  - Overlap real promedio verificado entre chunks consecutivos.
- `packages/rag_core/tests/test_chunking.py` creado (12 tests) como gate de Fase 2.
  - Tests: respeto de size, existencia de overlap, herencia de metadata, índices secuenciales, ids únicos, parámetros inválidos, integración con dataset real.

### Evidencia
- `data/processed/redflags_chunks.jsonl`: 299 chunks (configuración recomendada 1024/128).
- `progress/evidence/fase2-chunking-report.json`: reporte comparativo con métricas por configuración.
- `pytest packages/rag_core/tests/test_chunking.py -q` → 12 passed.
- `bash scripts/verify.sh` → validate-harness OK + pytest 23 passed (10 dataset + 12 chunking).

### Riesgos
- Tamaño 1024/128 elegido como recomendado por equilibrio entre granularidad y coherencia; puede ajustarse en Fase 7 (evaluación) según Recall@k.

### Próximos pasos
- Fase 3 — Embeddings + FAISS: `packages/rag_core/embeddings.py` e `indexing.py`.

## 2026-05-29 — Orquestación multi-CLI + gate de tests; Fase 1.1 APROBADA

### Decisión
- Se formaliza la **orquestación multi-CLI** (spec `specs/005-multicli-orchestration.md`): verdad honesta (Workflow=solo Claude; multi-proveedor real=OpenCode o dispatcher de archivos), 9 micro-subagentes con contrato+test, cola `tasks/queue.json` + `scripts/next-task.sh`, y **gate de tests** como árbitro provider-agnóstico.
- **Gate de tests creado** (`packages/rag_core/tests/test_dataset_contract.py`, 10 tests) y **cableado en `verify.sh`** (corre pytest si hay tests; `pyproject` testpaths += `packages`). Doc: `docs/TESTING.md`.
- **Fase 1.1 (rework Kimi) APROBADA automáticamente**: `pytest` 10/10 PASS sobre 237 unidades → backlog F1 y `queue.json` F1.1 = `done`. Desbloquea **F2 chunking** (Kimi).
- Construido con un **Workflow de 4 subagentes Claude** (~104k tokens, una vez) que generó spec+tests+dispatcher+doc.

### Evidencia
- `python -m pytest packages/rag_core/tests/test_dataset_contract.py -q` → 10 passed. `next-task.sh kimi` ahora apunta a F2.
- Nuevos: `specs/005-multicli-orchestration.md`, `tasks/queue.json`, `scripts/next-task.sh`, `docs/TESTING.md`.

### Riesgos
- `verify.sh` ahora falla (exit≠0) si cualquier test falla → un worker no puede declarar éxito con gate en rojo (esto es deseado).
- Multi-proveedor simultáneo requiere OpenCode configurado; si no, dispatch por archivos + humano.

### Próximos pasos
- Fase 2 — chunking comparativo (Kimi) con su propio gate `test_chunking.py`.


## 2026-05-29 — Fase 1.1: Rework dataset (Kimi K2)

### Decisión
- `packages/rag_core/loaders.py` reescrito completamente con extracción lógica robusta:
  - `indicator_name`: extraído de spans de mayor tamaño de fuente (font≥16), uniendo líneas consecutivas; limpia Rxxx y headers conocidos.
  - `stage`: inferido desde el título del indicador mediante keywords específicas (planning/tender/award/contract).
  - `family`: mapeo stage→family obligatorio; 4 familias presentes (planeacion, competencia/licitacion, adjudicacion, ejecucion/contrato), 0 unknown.
  - Unidades lógicas: cada indicador se divide en bloques `core` (Definition+Why+Unit+Type+Stage+Source), `formula` (Methodology+Data fields+OCDS), `example` (Example). Metodología: 1 unidad por encabezado (`section`).
  - `parent_doc_id`: el primer bloque (core) es padre; formula/example apuntan a él.
  - Texto limpio: sin números de página sueltos ni etiquetas de layout.

### Evidencia
- 237 unidades generadas (195 indicator + 42 metodología) de 73 páginas de indicadores + 26 de metodología.
- Coverage indicator_name: 100% (195/195).
- Family distribution: planeacion=18, competencia/licitacion=80, adjudicacion=50, ejecucion/contrato=47, metodologia=42.
- Block types: core=102, formula=81, example=12, section=42.
- `verify.sh` verde (exit=0).

### Riesgos
- 12 unidades `example` (escasas): muchos indicadores no tienen sección Example en el PDF.
- Stage inferido por keywords del título: aproximación heurística. No hay stage explícito en el layout del PDF (el PDF lista todos los stages posibles en un bloque tipo tabla).

### Próximos pasos
- Fase 2 — Chunking comparativo (≥2 tamaños + overlap).

## 2026-05-29 — Review Fase 1 (Claude): RECHAZADA → Fase 1.1

### Decisión
- **El harness/sistema multi-CLI FUNCIONA**: MiniMax ejecutó Fase 1 de forma autónoma vía `START_HERE`→`NEXT_ACTION`→`verify`→handoff, sin prompts pegados. Validado.
- **Deliverable de datos RECHAZADO** por 3 defectos: (1) `indicator_name` None en 95/100; (2) `family` 30% `unknown` y falta `adjudicación`; (3) unidades = volcado por página con ruido de layout, conteo forzado a 100 (68 indicadores reales). Review: `progress/reviews/2026-05-29-claude-fase1-review.md`.
- **Fase 1.1 (rework)** asignada a Kimi/DeepSeek con criterios de aceptación verificables en `NEXT_ACTION.md` (segmentación lógica + sub-unidades core/formula/example, family por Stage OCDS, indicator_name desde título de página/ToC).

### Evidencia
- 100 unidades JSON válidas pero: indicator_name vacío 95%, family {competencia:53, planeacion:5, ejecucion:12, unknown:29, None:1}, 98/100 unidad=1 página.
- backlog F1 → status `rework`. `verify.sh` exit=0 (verde estructural, pero calidad insuficiente = "verde con observaciones").

### Riesgos
- ~100 pp vs ≥100 unidades: resolver con sub-unidades lógicas, no con char-split.

### Próximos pasos
- Fase 1.1 — rework dataset (Kimi/DeepSeek).


## 2026-05-29 — Fase 1: PDF → 100 unidades documentales (MiniMax)

### Decisión
- `packages/rag_core/loaders.py` creado: parseo PDF con PyMuPDF, extracción por página + split a 2000 chars.
- Umbral de split ajustado de 3000→2000 chars para alcanzar ≥100 unidades exactas.
- Metadata extraída: doc_id, source_file, page_start, page_end, section, family, indicator_code, indicator_name, hash, text.
- Familia map: collusion/bid-rigging → competencia/licitación, fraud/implementation → ejecución/contrato, low transparency → planeación.
- Sin OCR (texto nativo Adobe InDesign). Sin tables split (se preservan como texto).

### Evidencia
- 100 unidades generadas en `data/processed/redflags_units.jsonl` (71 indicator + 29 methodology).
- `progress/evidence/fase1-exploration-report.json`: family_dist={competencia:53, ejecucion:12, planeacion:5, unknown:1}, page_range=2-100.
- `verify.sh` pasa: validate-harness OK, compileall OK.
- Handoff: `progress/runs/2026-05-29-2139-minimax-fase1-dataset-pdf-units.md`.

### Riesgos
- Solo 100 unidades (frontera exacta); con PDF de ~100 pp vs ~500 pp de la spec, podría faltar contenido.
- Stage extraction no funciona (family es el axis principal de navegación).
- Indicator codes tienen gaps en numeración (detectado en exploración).

### Próximos pasos
- Fase 2 — Chunking: `packages/rag_core/chunkers.py` con chunking comparativo (≥2 tamaños + overlap).


## 2026-05-29 — Fase 0.4: Flota real + onboarding sin pegar prompts

### Decisión
- Flota de trabajo (sin GPT/Codex; cuidar tokens): **Claude** (coordina/integra/revisa, caro→poco) + **Kimi K2 / DeepSeek** (implementan) + **MiniMax / Qwen** (worker barato; Qwen además es el LLM obligatorio del RAG).
- **Onboarding sin prompts largos:** `docs/START_HERE.md` — el humano solo dice "Lee docs/START_HERE.md y ejecuta la actividad pendiente"; la tarea vive siempre en `progress/NEXT_ACTION.md`.
- PDF recibido: `OCP2024-RedFlagProcurement-1.pdf` (~100 pp). Riesgo ≥100 unidades registrado en CURRENT_STATE.

### Evidencia
- `docs/START_HERE.md` (nuevo, enforced por validate-harness). `MULTI_CLI_PROTOCOL.md` y `AGENTS.md` actualizados a la flota real.
- context-graph: 33 nodos, 138 aristas, 0 huérfanos. `verify.sh` exit=0.

### Riesgos
- Modelos abiertos necesitan un CLI con acceso a archivos (OpenCode) o el humano pega `context-pack.sh`.
- ~100 pp puede no llegar a ≥100 unidades → segmentación fina / parte 2.

### Próximos pasos
- Fase 1 (lista para ejecutar por Kimi/DeepSeek vía START_HERE): PDF → ≥100 unidades documentales.


## 2026-05-29 — Fase 0.3: Grafo de contexto (CodeGraph-lite) + SDD nativo

### Decisión
1. **Navegación inteligente del repo = grafo determinista generado de nuestros propios docs** (opción C), NO Graphiti/Neo4j (A) ni grafo MCP (B). Razón: A/B son 2.ª fuente de verdad y MCP-only; C es archivo plano, versionado, CLI-agnóstico, regenerable. (El usuario aclaró que buscaba un grafo de la *documentación* navegable por el agente, no GraphRAG del dominio.)
2. **SDD nativo** (no se instala GitHub Spec Kit): se añade `specs/_TEMPLATE-feature.md` con la tríada spec→plan→tasks.

### Evidencia
- `scripts/build_context_graph.py` + `scripts/build-context-graph.sh` → generan `progress/context-graph.json` (32 nodos, 124 aristas, 0 huérfanos) y `docs/CONTEXT_GRAPH.md` (Mermaid).
- Enlazado en `docs/MEMORY_PROTOCOL.md` (§5bis) y `docs/MEMORY_INDEX.md`.
- `specs/_TEMPLATE-feature.md` (plantilla SDD). `verify.sh` exit=0.

### Riesgos
- El grafo hay que regenerarlo tras cambios estructurales en docs (1 comando). No está acoplado a verify para no forzar escrituras.

### Próximos pasos
- Fase 1 — dataset (PDF → ≥100 unidades). Bloqueada hasta colocar el PDF en `data/raw/`.


## 2026-05-29 — Fase 0.2: Protocolo de memoria + decisión sobre Graphiti/CodeGraph/SDD

### Decisión
1. **Memoria del harness = archivos MD/JSON** (no BD de grafos). Formalizado en `docs/MEMORY_PROTOCOL.md`: capas L0–L4, presupuesto de contexto, write-through, "si no está en un archivo, no existe".
2. **Graphiti / Neo4j / FalkorDB: descartado como memoria del harness** (requiere BD de grafos + API LLM + ingesta continua → infra, costo, no-determinismo, segunda fuente de verdad). Anotado como posible **bonus de dominio (GraphRAG de red flags)**, fuera del MVP.
3. **CodeGraph: descartado** (el codebase es pequeño; `MEMORY_INDEX.md` + grep bastan).
4. **SDD: adoptado de forma nativa** en el harness (mapeo constitution/spec/plan/tasks/implement/verify documentado). Pendiente decidir si además se instala GitHub Spec Kit.

### Evidencia
- Nuevo `docs/MEMORY_PROTOCOL.md`; enlazado desde `AGENTS.md` y `docs/MEMORY_INDEX.md`.
- `scripts/validate-harness.sh` ahora exige CAVEMAN, MULTI_CLI_PROTOCOL y MEMORY_PROTOCOL. `verify.sh` exit=0.
- Doc consultada vía Context7: `/getzep/graphiti` (requisitos), `/github/spec-kit` (estructura SDD).

### Riesgos
- Si más adelante se instala Spec Kit, evitar duplicar estructura con `specs/` + `progress/` (mantener una sola fuente de verdad).

### Próximos pasos
- Decidir ruta SDD (Spec Kit tool vs nativo) y si se reserva el GraphRAG como bonus. Luego: Fase 1 — dataset.


## 2026-05-28 — Fase 0.1: Hardening de verificación del harness

### Decisión
Evitar el "verde falso": `verify.sh` no debe limitar­se a "el archivo existe / JSON válido", sino comprobar que el harness es **usable** (frontmatter de agentes legible, reglas vivas, próxima acción única).

### Evidencia
- Nuevo `scripts/validate-harness.sh` (integrado dentro de `scripts/verify.sh`). Valida: AGENTS.md <180 líneas; existencia de MEMORY_INDEX/CURRENT_STATE/NEXT_ACTION/HANDOFF; cada `.claude/agents/*.md` abre/cierra `---` y tiene `name/description/tools`; cada `.opencode/agent/*.md` abre/cierra `---` y tiene `description/mode`; SKILL.md de Codex no vacío; backlog.json válido; CAVELOG con entrada fechada; NEXT_ACTION con exactamente una `## Acción`.
- **Revisión de frontmatter:** se inspeccionaron los 6 subagentes Claude + worker OpenCode + SKILL Codex. **No se encontró frontmatter mal formado.** Lo que parecía `---ls: Read...` era visualización UTF-8 de acentos (é/ñ/ó) bajo `cat -A`, no corrupción.
- `bash scripts/validate-harness.sh` → "OK (harness usable)". `verify.sh` pasa con la validación integrada.

### Riesgos
- La comprobación de "entrada reciente" en CAVELOG solo verifica que exista un heading fechado, no la fecha exacta.

### Próximos pasos
- Sin cambios: sigue **Fase 1 — dataset** (bloqueada hasta colocar el PDF en `data/raw/`).


## 2026-05-28 — Fase 0: Harness multi-CLI + caso de uso Red Flags

### Decisión
1. **Caso de uso** definido (spec 004): RAG agéntico para detectar **señales de riesgo** en contratos públicos a partir de la guía OCP Red Flags (~500 pp).
2. **Override de stack**: el proyecto es **Colab + Qwen2.5-3B + FAISS + embeddings multilingües**, NO FastAPI/pgvector/LangGraph (ese era el sugerido genérico). Registrado en `docs/ARCHITECTURE.md`.
3. **Dataset**: el libro/PDF grande es dataset válido; "documento" = **unidad documental lógica** (≥100), luego chunking.
4. **Modelo de trabajo multi-CLI**: Claude coordina/integra, Codex implementa/audita, OpenCode worker barato (`docs/MULTI_CLI_PROTOCOL.md`).
5. **Lenguaje seguro** obligatorio: señales de riesgo / requiere revisión humana.

### Evidencia
- Nuevos: `docs/MEMORY_INDEX.md`, `docs/CAVEMAN.md`, `docs/MULTI_CLI_PROTOCOL.md`, `docs/RUBRICA.md`, `specs/004-redflags-rag.md`.
- `progress/` con CURRENT_STATE, NEXT_ACTION, HANDOFF, runs/, reviews/, evidence/.
- Scripts: `init.sh` (corregido: faltaba validar progress/ y usaba `python` inexistente → ahora `python3`), `verify.sh`, `handoff.sh`, `context-pack.sh`.
- Subagentes: `.claude/agents/` (+spec-planner, dataset-engineer, rag-implementer, evaluator), `.opencode/agent/worker.md`.
- `tasks/backlog.json` reescrito por fases F0–F8.

### Riesgos
- OpenCode usa `.opencode/agent/` (singular); convención verificada vía Context7 pero puede cambiar entre versiones.
- El PDF aún no está en `data/raw/` (lo aporta el humano) → Fase 1 bloqueada hasta entonces.

### Próximos pasos
- Colocar PDF en `data/raw/` y arrancar **Fase 1 — dataset** (ver `progress/NEXT_ACTION.md`).


## 2026-05-29 01:06 — Bootstrap del harness RAG agentico

### Decisión
Se crea estructura base para un proyecto RAG agentico usando harness engineering.

### Evidencia
- `AGENTS.md` define reglas de trabajo.
- `scripts/init.sh` valida estructura antes de iniciar.
- `scripts/verify.sh` centraliza quality gates.
- `progress/` guarda memoria fuera del chat.
- `agents/` separa roles para evitar contexto inflado.

### Riesgos
- Sobrecargar `AGENTS.md`.
- Confundir RAG agentico con chatbot simple.
- Permitir herramientas MCP sin política.
- Responder sin evidencia.

### Próximos pasos
1. Definir caso de uso del RAG.
2. Elegir stack backend/frontend.
3. Crear primer pipeline de ingesta.
4. Crear primer dataset de evaluación.
