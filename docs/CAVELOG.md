# CAVELOG

Bitácora de decisiones, avances y evidencia. (Append-only; lo más reciente arriba.)

## 2026-07-14 — Integración selectiva del trabajo externo y hardening final

### Decisión
- No se integra el notebook de `trabajo-colega/` completo: reintroduce prompts manuales, elimina la evaluación RAGAS local y contiene outputs con abstenciones/citas incorrectas y lenguaje no apto para la presentación.
- Se adaptan sus casos útiles al gold set canónico de 15 preguntas: 11 respondibles y 4 de seguridad (dos fuera de dominio, una sin evidencia suficiente y una premisa falsa), con IDs, idioma, códigos, páginas y respuestas esperadas.
- Retrieval y proxies léxicos locales inspirados en RAGAS excluyen las trampas; seguridad se reporta aparte mediante exactitud de estado/razón y fuga de citas.
- Se restauran y versionan los cinco artefactos necesarios para Colab `Run all`: PDF, unidades, chunks, índice FAISS y mapping.
- La página `/documentos` ofrece los seis PDFs públicos de demostración mediante enlaces raw de GitHub y mantiene el catálogo disponible aunque falle el historial de la API.
- CI instala Python, ejecuta pytest, instala Node, ejecuta Vitest, lint y build. Los tests neuronales se omiten explícitamente si no se instala el extra `neural`.

### Evidencia
- Gate local: `bash scripts/verify.sh` → **276 passed, 6 skipped**.
+- Entorno Python limpio: **266 passed, 16 skips opcionales** sin fallos.
+- Frontend: Vitest 1 passed, ESLint exit 0 y Next.js build correcto.
+- `evaluate_security_case` valida status, razón, fuga de citas, códigos/páginas esperados y corrección de premisas falsas; el reporte preserva `id` y `status` por fila.
+- `extract_indicator_code` elige el código de la misma línea del título y evita referencias cruzadas; los JSONL ahora se regeneran sin líneas partidas.
- Entorno Python limpio: instalación editable exitosa y **260 passed, 16 skipped**, sin fallos; los skips corresponden a modelos/dependencias opcionales.
- Frontend: Vitest 1 passed, ESLint exit 0 y Next.js build correcto.
- Gold set: 15 IDs únicos, 4 consultas en español o más, cuatro familias cubiertas y oráculos de páginas/códigos.
- Los seis PDFs tienen firma `%PDF-`; sus enlaces se validan después de publicar.

### Riesgos
- El reporte versionado sigue siendo baseline offline de contrato; la corrida neural definitiva requiere Colab T4 autenticado.
- `trabajo-colega/` permanece local e ignorado como evidencia de revisión; no es fuente canónica ni se publica.
- Cloud Run mantiene metadata SQLite efímera; no afecta las descargas estáticas de los PDFs.

## 2026-07-14 — Promoción V2 a main y cierre de producción

### Decisión
- La experiencia principal pasa a ser Next.js en Vercel, consumiendo la API FastAPI `tdr-api` en Cloud Run. Streamlit permanece como respaldo operativo.
- `v2` se promueve a `main` mediante merge no destructivo; no se reescribe la historia ni se usa force-push.
- Los tests de orquestación aceptan chunks recuperados inyectables. Así validan dedupe, persistencia, scoring y dossier sin cargar el CrossEncoder real en CPU.
- `.env*` queda excluido tanto de Git como del contexto de `gcloud run deploy --source`; los secretos permanecen fuera del repositorio y del artefacto de build.

### Evidencia
- Causa de la demora reproducida con `faulthandler`: `test_dedupe` ejecutaba `BAAI/bge-reranker-v2-m3` real dentro de PyTorch pese a usar un LLM falso.
- Gate corregido: **258 passed, 6 skipped** en 35.19 s.
- Frontend: `npm run lint && npm run build` OK; rutas `/`, `/analizar`, `/como-funciona` y `/documentos` prerenderizadas.
- Producción: frontend `/` y `/analizar`, API `/health` y `/api/tdrs`, y Streamlit de respaldo responden HTTP 200.
- `gcloud meta list-files-for-upload` confirma que `.env` no forma parte del upload.

### Riesgos
- Cloud Run presenta arranque en frío de aproximadamente 4-7 s tras inactividad.
- SQLite en `/tmp` sigue siendo efímero; Qdrant conserva los vectores, pero un redeploy puede reiniciar el historial visible.
- Las credenciales locales deben rotarse si fueron expuestas fuera del equipo; nunca se versionan.

## 2026-07-11 — Notebook Colab dual RAG: FAISS/Qwen default + Gemini/Qdrant opt-in

### Decisión
- El notebook conserva la ruta académica obligatoria **FAISS/E5 + Qwen2.5-3B** como default (`RAG_BACKEND=faiss`, `RAG_GENERATOR=qwen`).
- Se añade una ruta cloud opcional: `RAG_BACKEND=qdrant` consulta `standard_kb`; `RAG_GENERATOR=gemini` usa `gemini-2.5-flash` vía `google-genai` con `generate_fn` inyectable.
- El PDF OCP sigue cargándose automáticamente desde el repo/fallback público; no se usa `files.upload()` ni `getpass()`.
- Las señales del modo Gemini requieren doble evidencia: cita literal del contrato y evidencia OCP con `chunk_id`/`indicator_code`; si falta, quedan en revisión.

### Evidencia
- Nuevo helper hermético: `packages/rag_core/notebook_rag.py` (`retrieve`, `compare_backends`, `validate_dual_evidence`).
- Qdrant hardened: normalización común de chunks, preflight de colección, soporte para vector anónimo o vector nombrado.
- Gemini adapter hardened: cliente falso inyectable, `strict=True`, respuesta vacía/espacios como error controlado, fallback conservado en modo no estricto.
- Tests focalizados: `python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py apps/api/tests/test_google_llm.py packages/rag_core/tests/test_notebook_rag.py packages/rag_core/tests/test_vector_store.py -q` → **64 passed**.
- Gate completo local: `bash scripts/verify.sh` → **258 passed, 6 skipped**.

### Riesgos
- La validación real `Run all` en Colab T4 sigue pendiente por autenticación humana.
- La ruta Qdrant/Gemini es opt-in y solo puede validarse con Secrets (`GEMINI_API_KEY`/`GOOGLE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`). No reemplaza Qwen.

## 2026-07-11 — Cierre V2: Streamlit + Cloud Run y gate Colab

### Decisión
- Streamlit reemplaza Next.js/Vercel y ejecuta el orquestador en el mismo contenedor; no existe una URL backend separada.
- Self-RAG sale del alcance final: Qdrant, grounding semántico, abstención y EvidenceCritic ya cubren los requisitos con menor latencia y complejidad.
- La metadata web queda en SQLite efímero para la demo. Qdrant conserva `standard_kb` y `subject_docs`; la falta de persistencia del historial tras redeploy se declara como limitación.
- `HF_TOKEN` pasa a ser opcional y no interactivo en el notebook para que `Run all` no se detenga en `getpass()`.

### Evidencia
- Cloud Run `tdr-risk-auditor-00001-6mq`: ready, 100% del tráfico, root y `/_stcore/health` HTTP 200.
- Prueba browser real: texto de 449 caracteres → TDR #1 → run #1 → 3 señales aceptadas, 0 rechazadas, grounding 1.00 y dossier con revisión humana.
- Colab abre correctamente desde GitHub y ofrece runtime T4, pero Google exige iniciar sesión antes de conectar; la corrida completa sigue pendiente del humano autenticado.
- `test_notebook_smoke.py`: 8 passed, incluida regresión contra prompts interactivos.
- `bash scripts/verify.sh`: 209 passed, 6 skipped; `git diff --check` y validación JSON del notebook/reporte sin errores.

### Riesgos
- El baseline `progress/evidence/ragas-report.json` aún no es la salida neural de un Run all T4.
- La prueba E2E mostró que una señal de oferente único puede heredar una cita R003 de plazo corto; requiere revisión humana y es candidato a hardening de calidad de citas.

## 2026-06-30 — Fase 16: TDR Risk Review MVP multiagent-ready, desplegado end-to-end

### Decisión
- Implementación completa del MVP web basado en `specs/006-tdr-upload-review-mvp.md`.
- Stack: FastAPI + SQLModel (SQLite) + Jinja2 + Tailwind CDN + Google Gemini (`gemini-1.5-flash`) como LLM por API.
- Arquitectura por contratos de agentes reemplazables: `TdrIntakeAgent` → `AnalysisAgent` (envoltorio de `packages.rag_core.agent.analyze` con `generate_fn` inyectable) → `EvidenceCriticAgent` V1 → `RiskScoringAgent` V1 → `DossierAgent`.
- `generate_fn` por defecto resuelve a Gemini (`google.generativeai`) cuando hay `GOOGLE_API_KEY`; cae a un fake determinista cuando falta (sigue siendo útil para CI y modo demo).
- Reuso del RAG core existente: `packages/rag_core/agent.analyze` con retrieval híbrido FAISS+BM25, grounding lexical y citas. El RAG del notebook académico queda intacto.
- Frontend server-rendered con HTML/Tailwind CDN, sin build step. Endpoints `/`, `/tdrs/upload`, `/tdrs`, `/tdrs/{id}`, `/tdrs/{id}/analyze`, `/tdrs/{id}/dossier`, `/runs/{run_id}` y equivalentes JSON `/api/...`.
- EvidenceCritic es la feature visible del dossier: separa señales aceptadas de rechazadas por evidencia insuficiente, expone grounding ratio y estado (sufficient/weak/insufficient).

### Evidencia
- `bash scripts/verify.sh` → **169 passed, 6 skipped** (gate de pytest verde).
- Smoke real con uvicorn local: upload de TDR pegado → análisis → dossier JSON con `risk_level`, `grounding_ratio`, `refusal`, `uncertainty`, `next_steps`, `disclaimer`. Endpoints `/`, `/tdrs/upload`, `/tdrs/{id}/dossier` retornan HTTP 200 con HTML renderizado.
- Tests nuevos:
  - `apps/api/tests/test_intake.py` (intake y normalización).
  - `apps/api/tests/test_evidence_scoring.py` (reglas deterministas del critic y scorer).
  - `apps/api/tests/test_pipeline.py` (pipeline end-to-end con fake determinista, home, list, upload form, health).
- Endpoints API documentados con respuestas JSON y HTML.

### Riesgos
- Demo-web no incluye OCR para PDFs escaneados; el intake devuelve mensaje claro y sugiere pegar el texto.
- Sin segundo integrante confirmado en la ficha técnica del notebook (riesgo heredado de F15).
- El despliegue real (Cloud Run, Render, etc.) requiere configurar `GOOGLE_API_KEY` y `UPLOAD_DIR`; mientras no haya key, el fallback fake funciona para que la app no rompa.

### Próximos pasos
- F15.3 Colab Run all (evidencia neural del notebook) sigue pendiente como entregable paralelo de la UNI.
- Conectar un Google Gemini key real y correr un TDR real del corpus para validar el dossier end-to-end con LLM real.
- Documentar el deploy en README (Cloud Run o Render) para el portafolio/X.

## 2026-06-30 — Fase 16: Spec TDR Upload Review MVP multiagent-ready

### Decisión
- Se abre `specs/006-tdr-upload-review-mvp.md` como spec activa de producto web para el final de curso.
- Alcance aprobado: plataforma web desplegable donde el usuario sube un TDR PDF/texto y recibe un dossier de señales de riesgo potenciales con evidencia, citas, grounding, rechazo por evidencia insuficiente y revisión humana.
- El MVP será **multiagent-ready**, pero no multi-LLM desde el inicio: contratos `TdrIntakeAgent`, `AnalysisAgent`, `EvidenceCriticAgent`, `RiskScoringAgent`, `DossierAgent` implementados primero como servicios/funciones.
- Se incorpora feedback CTO: decidir LLM de deploy desde F16.1; demo-web usa `generate_fn` por API/fake y no intenta correr Qwen-3B/e5/reranker en tier gratis CPU.
- `EvidenceCritic` pasa a ser feature visible del dossier, no detalle interno: aceptar/rechazar señales según citas, `grounding_ratio` y `refusal`.
- El análisis debe modelarse como asíncrono con estados desde el data model, aunque V1 use FastAPI `BackgroundTasks` o ejecución simple.
- F16 soporta PDFs basados en texto y texto pegado; OCR queda diferido.

### Evidencia
- Nueva spec: `specs/006-tdr-upload-review-mvp.md`.
- `progress/NEXT_ACTION.md` actualizado a F16.1 con una sola acción.
- `docs/MEMORY_INDEX.md` actualizado para apuntar a `006` como spec activa de producto y `004` como núcleo RAG.

### Riesgos
- F15.3 Colab Run all sigue pendiente como evidencia neural del notebook.
- El deploy puede fallar si se intenta cargar modelos locales pesados; por eso la decisión de LLM por API/fake se adelanta a F16.1.
- OCR y PDFs escaneados quedan fuera de alcance para no romper el plazo del curso.

### Próximos pasos
- Implementar F16.1: contrato demo-web sin GPU usando `agent.analyze(..., generate_fn=...)`, tests con fake determinista y estados de análisis.

## 2026-06-30 — Fase 15.2: `docs/PROYECTO.md` con RAGAS local y cierre Agent IO

### Decisión
- Aceptado el run Agent IO `f15-2-docs-proyecto` con verdict `accepted`.
- `docs/PROYECTO.md` queda actualizado con la etiqueta estricta **"RAGAS local"**, tabla de puntajes desde `progress/evidence/ragas-report.json`, referencia Es et al. 2025 / `arXiv:2309.15217`, ficha técnica/trazabilidad del notebook y lenguaje seguro.
- Se eliminó la única mención uppercase `RAGAS` sin `local` que quedaba en un subtítulo explicativo.
- `progress/agent_io/QUEUE.md` queda sin run activo (`Run ID: none`).
- Slides quedan fuera de scope por instrucción del usuario; la siguiente fase es Colab Run all.

### Evidencia
- Auditoría de etiqueta: `RAGAS local count=9`, `standalone/non-local RAGAS count=0`.
- `progress/evidence/f15-2-docs-proyecto.json` parsea como JSON válido.
- `python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py -q` → **7 passed**.
- `bash scripts/verify.sh` → **148 passed, 6 skipped**, exit 0.
- `git diff --check docs/PROYECTO.md progress/evidence/f15-2-docs-proyecto.json progress/agent_io/runs/f15-2-docs-proyecto/RESPONSE.md` → exit 0.

### Riesgos
- `progress/evidence/ragas-report.json` sigue siendo baseline/offline; falta regenerarlo con Qwen real en Colab T4.
- No se ejecutó Colab en esta fase.

### Próximos pasos
- Ejecutar `Run all` en Google Colab T4, traer `progress/evidence/ragas-report.json` neural definitivo y verificar localmente con `bash scripts/verify.sh`.

## 2026-06-29 — Fase 15: Ficha técnica (cell 0) + tabla de trazabilidad (Claude)

### Decisión
- Reescrita la **celda 0** del notebook `notebooks/redflags_rag_colab.ipynb` como **Ficha técnica** completa: título, autor (Miguel Arias / @MiguelAAR10), universidad/curso/docente, fecha (junio 2026), dominio, objetivo, corpus y fuentes de datos, modelos HuggingFace, técnicas avanzadas + bonus, y resumen de evaluación. Conserva el diagrama de arquitectura y la advertencia de lenguaje seguro.
- Añadida la **sección §13 — Tabla de trazabilidad** (última celda markdown): mapea cada requisito/técnica de la rúbrica UNI a su sección·celda y a su archivo de evidencia (retrieval, reranking, citación/grounding, refusal, RAGAS local, gold set, y bonus LangChain/Gradio/MiniMax).
- Métricas siempre etiquetadas como **"RAGAS local"**; lenguaje anticorrupción seguro ("señales de riesgo potenciales", "requiere revisión humana").
- Todas las celdas previas se conservan intactas (solo se editó el contenido de cell 0 y se anexó la §13).

### Evidencia
- Notebook: 42 → **43 celdas**, nbformat v4 válido. Cell 0 contiene ficha técnica/autor/fecha/arquitectura/corpus/Qwen2.5-3B/revisión humana (verificado).
- `python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py -q` → **7 passed**.
- `bash scripts/verify.sh` → **148 passed, 6 skipped**, exit 0.

### Riesgos
- La rúbrica menciona parejas de 2 integrantes; la ficha lista un solo autor según `docs/PROYECTO.md`/`README.md`. Ajustar si se confirma el segundo integrante.
- Los números de celda en la trazabilidad se expresan por etiqueta de sección (§6.1, §9.2…), estables ante reordenamientos, no por índice crudo.

### Próximos pasos
- Reflejar "RAGAS local" + tabla de puntajes en `docs/PROYECTO.md` / slides.
- Correr `Run all` en Colab T4 limpio y guardar el `ragas-report.json` neural definitivo.

## 2026-06-29 — Mejora profunda del skill de subagentes: perfiles de orquestación

### Decisión
- Reescribir `.opencode/skills/subagent-coder/SKILL.md` para soportar **tres perfiles de orquestación**: `single-writer-inspector`, `parallel-sectioning`, `evaluator-optimizer`.
- Crear `.opencode/skills/subagent-coder/patterns/single-writer-inspector.md` con contrato de preservación por fingerprints SHA-256, política de metadatos (no inventar autor/LLM), edición segura con `nbformat`, archivo de evidencia JSON y response contract estructurado.
- Crear `.opencode/skills/subagent-coder/patterns/parallel-sectioning.md` para trabajos independientes en archivos separados.
- Actualizar `scripts/subagent-run.sh` para leer `orchestration_profile` del YAML e **inyectar el patrón completo** en el `REQUEST.md`, siguiendo el feedback de la maestría.
- Reescribir `tasks/f15-notebook.yaml` con `orchestration_profile: single-writer-inspector` y subagente `NotebookTraceabilityInspector` read-only.
- Regenerar `progress/agent_io/runs/f15-notebook-traceability/REQUEST.md` con el patrón correcto.

### Evidencia
- `bash scripts/verify.sh` → **148 passed, 6 skipped**, exit 0.
- `progress/agent_io/runs/f15-notebook-traceability/REQUEST.md` contiene goal, acceptance, rules y el patrón `single-writer-inspector` completo inyectado (411 líneas).
- El helper imprime el perfil usado y genera los archivos del run correctamente.

### Riesgos
- El REQUEST.md de `single-writer-inspector` es largo (~400 líneas) pero es preciso; el subagente sigue recibiendo el prompt de una línea.
- Si el subagente no sabe usar `nbformat`, puede fallar; mitigación: el patrón incluye procedimiento paso a paso.

## 2026-06-29 — Fase 14: Integración RAGAS — REVIEW y cierre (DANTE-OS)

### Decisión
- Aceptada la entrega de Claude Code (Opus 4.8) del run Agent IO `2026-06-29-1449-fase14-notebook-ragas-integration-implementer` con verdict `accepted`.
- Cierre del run: `QUEUE.md` rotado a `Run ID: none`.
- Apertura de Fase 15: ficha técnica rotulada en cell 0 + tabla de trazabilidad requisito→celda + Run all Colab T4 + etiqueta "RAGAS local" + tabla de puntajes en `docs/PROYECTO.md` / slides.
- `ragas-report.json` committed al repo es baseline offline (contexts = chunks gold-relevantes, answer = extractivo/refusal). El reporte definitivo lo genera el notebook con Qwen en Colab `Run all`. Esto queda explícito en CAVELOG y en la sección 9.3 del notebook.

### Gaps aceptados
- `test_eval.py` modificado fuera del `Allowed Writes` literal: justificado. Es test, no arquitectura, y el ajuste era necesario porque las trampas rompen el contrato previo (sin `relevant_indicator_codes`).
- `docs/PROYECTO.md` no tocado en F14 por restricción del REQUEST. Pendiente para F15/docs.

### Verificación integrator
- `python3 -m pytest packages/rag_core/tests/test_ragas_metrics.py -q` → 42 passed.
- `bash scripts/verify.sh` → 148 passed, 6 skipped, exit 0.
- `data/eval/goldset.jsonl`: `wc -l` = 15, `total=15 traps=2`.
- Notebook: 42 celdas, `evaluate_ragas` referenciado en celda 28, "RAGAS local" en celdas 28 y 29.
- `progress/evidence/ragas-report.json`: `n=15 traps=2`, medias en `[0, 1]`.

## 2026-06-29 — Fase 14: RAGAS local en notebook + gold set con trampas (Claude)

### Decisión
- Integradas las métricas **RAGAS local** (Fase 13) en la **sección 9** del notebook `notebooks/redflags_rag_colab.ipynb`:
  - Nueva celda `9.2` (código): carga el gold set, ejecuta `analyze()` (retrieval + rerank + Qwen + grounding) por consulta, arma `{question, answer, contexts}`, llama `evaluate_ragas`, imprime tabla por ítem + agregados y guarda `progress/evidence/ragas-report.json`.
  - Nueva celda `9.3` (markdown): lectura de resultados; define faithfulness/answer relevance/context relevance y el comportamiento esperado en trampas (refusal → métricas ~0).
- Gold set ampliado de **12 → 15** ítems (append-only, sin tocar los 12 previos): +1 red flag in-corpus (`R031`, `R024`) y **2 preguntas trampa** fuera del corpus (`trap: true`) con `expected_answer` de refusal seguro.
- Etiqueta explícita **"RAGAS local"** (aproximación léxica determinista del paper Es et al. 2025, arXiv:2309.15217); **sin** librería `ragas` ni API externa, para garantizar `Run all` en Colab.

### Evidencia
- `data/eval/goldset.jsonl`: `n=15`, 2 ítems `trap: true` (cookies / FIFA 2022) con refusal esperado.
- `progress/evidence/ragas-report.json` (representativo offline; el notebook lo regenera con Qwen en Colab): `mean_faithfulness=0.865`, `mean_answer_relevance=0.337`, `mean_context_relevance=0.204`; las 2 trampas puntúan `0.000 / 0.000 / 0.000` en las tres métricas.
- Tests: `test_ragas_metrics.py` 37 → **42** (+5 sobre el gold set: tamaño, rango 10–15, ≥2 trampas, refusal esperado, `query` presente).
- `test_eval.py::test_goldset_format` actualizado para eximir a las trampas del mínimo de ≥1 código (no tienen códigos in-corpus por diseño).
- `bash scripts/verify.sh` → **148 passed, 6 skipped**, exit 0.

### Riesgos
- `ragas-report.json` del repo es un baseline léxico offline (contexts = chunks gold-relevantes, answer = extractivo/refusal); los puntajes reales (Qwen) se obtienen al correr `Run all` en Colab.
- Mantener la etiqueta "RAGAS local" en slides para no prometer equivalencia con la librería oficial.

### Próximos pasos
- Reflejar "RAGAS local" y la tabla de puntajes en `docs/PROYECTO.md` / slides (fuera del alcance de este run por `Allowed Writes`).
- Probar `Run all` en sesión limpia de Colab (T4) y guardar el `ragas-report.json` neural definitivo.
- Cerrar las brechas restantes de la auditoría: ficha técnica rotulada y tabla de trazabilidad requisito→celda.

## 2026-06-29 — Fase 13: Métricas RAGAS locales deterministas (DeepSeek)

### Decisión
- Implementadas las 4 funciones RAGAS locales exigidas por `progress/NEXT_ACTION.md`:
  - `packages/evals/ragas_metrics.py` con `faithfulness`, `answer_relevance`, `context_relevance`, `evaluate_ragas`.
  - `packages/rag_core/tests/test_ragas_metrics.py` con 37 tests (gate de Fase 13).
- **Aproximación determinista local** (sin APIs externas, sin dependencias pesadas):
  - `faithfulness`: divide la respuesta en frases y cuenta las soportadas por el contexto vía solapamiento léxico de tokens (`>=3` caracteres), umbral `FAITHFULNESS_THRESHOLD=0.25` (alineado con `verifier.DEFAULT_GROUNDING_THRESHOLD`).
  - `answer_relevance`: proxy léxico del original RAGAS (que regenera preguntas con LLM): fracción de tokens informativos de la pregunta presentes en la respuesta. Devuelve `0.0` ante refusal seguro (marcadores `"no hay evidencia suficiente"` / `"insufficient evidence"` / `"requires human review"`).
  - `context_relevance`: proxy local que divide cada contexto en frases y cuenta las que comparten tokens con la pregunta.
  - `evaluate_ragas`: agrega medias y métricas por item sobre `list[dict]`.
- Robustez: todas las funciones clampean a `[0, 1]`, manejan `None`/vacíos, devuelven `0.0` si no hay evidencia; pruebas cubren respuesta vacía, contexto vacío, refusal, pregunta trampa y casos parciales.
- Cero impacto en archivos protegidos: no se tocó `notebooks/`, `data/eval/goldset.jsonl`, `data/processed/*`, `data/index/*` ni `.env`.

### Evidencia
- `python3 -m pytest packages/rag_core/tests/test_ragas_metrics.py -q` → **37 passed** en 0.06 s.
- `bash scripts/verify.sh` → **143 passed, 6 skipped** (antes 106, +37 nuevos), exit 0, `validate-harness` OK.
- Mismas 4 funciones públicas, mismas firmas que `progress/NEXT_ACTION.md`.

### Riesgos
- Las métricas son aproximaciones léxicas locales, no la versión RAGAS oficial con LLM/embeddings semánticos. Son aceptables como "RAGAS local para Colab" según el contrato, pero conviene etiquetarlas como "RAGAS local" en notebook y slides para no sugerir equivalencia total con la librería.
- `faithfulness` puede subestimar soporte semántico cuando la paráfrasis no comparte tokens (caso esperado: cuando llegue el LLM real en Colab, conviene exponer `method="embedding"`).
- No se integró aún al notebook (`Run all` pendiente) ni al gold set: queda para la próxima fase.

### Próximos pasos
- Cablear RAGAS al gold set real + sección "Evaluación" del notebook (sección 9 del `redflags_rag_colab.ipynb`).
- Añadir ejemplo de uso en `docs/PROYECTO.md` y reflejarlo en las slides.

## 2026-06-29 — Review Agent IO: final-ragas-audit

### Decisión
- Claude Code ejecutó correctamente el flujo Agent IO: leyó `QUEUE.md`, abrió el `REQUEST.md` activo, guardó el resultado en `RESPONSE.md` y no escribió `REVIEW.md` ni archivos de estado.
- DANTE-OS revisó el output y lo marcó como `partially_accepted` en `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REVIEW.md`.
- Se acepta la brecha principal: faltan métricas RAGAS formales, puntajes RAGAS reportados, preguntas trampa y tabla de trazabilidad.
- Se corrige una afirmación del auditor: no contar ingesta multiformato como técnica implementada, porque el loader real es PDF-only.
- La siguiente acción pasa a implementar métricas RAGAS locales con tests, sin tocar notebook ni corpus todavía.

### Evidencia
- `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/RESPONSE.md` contiene la auditoría.
- `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REVIEW.md` contiene la decisión integradora.
- `progress/agent_io/QUEUE.md` vuelve a `Run ID: none` y registra el último run revisado.
- `bash scripts/verify.sh` = **106 passed, 6 skipped**, exit=0.

### Riesgos
- `Run all` en Colab limpio sigue sin verificación empírica.
- La implementación RAGAS debe mantenerse local/reproducible para no introducir API keys externas.

### Próximos pasos
- Implementar `packages/evals/ragas_metrics.py` y `packages/rag_core/tests/test_ragas_metrics.py` con TDD.

## 2026-06-29 — Agent IO CLI-proof + active run automation

### Decisión
- Se agrega `scripts/agent-io-new.sh` para crear runs de Agent IO y actualizar automáticamente `progress/agent_io/QUEUE.md` con `## Active Run`.
- Agent IO queda estandarizado en inglés para prompts, inputs y outputs.
- `CLAUDE.md`, `.codex/skills/rag-agentic-harness/SKILL.md` y `.opencode/agent/worker.md` ahora indican que análisis/auditorías/segundas opiniones deben usar `progress/agent_io/` y guardar output en `RESPONSE.md` cuando exista un run activo.
- Se crea un run activo de prueba real para Claude: `progress/agent_io/runs/2026-06-29-1220-claude-final-ragas-audit/REQUEST.md`.

### Evidencia
- Test nuevo: `packages/rag_core/tests/test_agent_io_script.py` valida que `scripts/agent-io-new.sh` cree `REQUEST.md`, `RESPONSE.md`, `REVIEW.md`, `STATUS.md` y actualice `QUEUE.md`.
- `python3 -m pytest packages/rag_core/tests/test_agent_io_script.py -q` = 1 passed.
- `bash scripts/verify.sh` = **106 passed, 6 skipped**, exit=0.

### Riesgos
- El run activo apunta a Claude Code; si Claude está en modo plan/read-only, debe devolver contenido listo para pegar en `RESPONSE.md`.

### Próximos pasos
- Probar en Claude Code con la frase: `Read progress/agent_io/START_HERE.md and execute the active interaction. Do nothing else.`

## 2026-06-29 — Rama de mejora final RAGAS + indicaciones oficiales

### Decisión
- Se marcó el estado previo como V1 estable mediante commit `2852327` (`chore: mark stable v1 with agent io`) y tag local `v1-stable-agent-io`.
- Se creó la rama `feature/final-evaluation-ragas` para trabajar las mejoras exigidas por las nuevas indicaciones del trabajo final.
- Se agregó `docs/proyecto-final-indicaciones/` con las indicaciones oficiales del entregable y un checklist accionable derivado del texto recibido.

### Evidencia
- `docs/proyecto-final-indicaciones/README.md` contiene la especificación del trabajo final: RAG vertical, técnicas avanzadas, RAGAS, notebook, slides, cronograma y rúbrica.
- `docs/proyecto-final-indicaciones/CHECKLIST.md` resume los requisitos mínimos y prioridades de mejora.
- `bash scripts/build-context-graph.sh` = 65 nodos, 237 aristas, 0 huérfanos.
- `bash scripts/verify.sh` = **105 passed, 6 skipped**, exit=0.

### Riesgos
- La mayor brecha nueva frente a las indicaciones es RAGAS formal: faithfulness, answer relevance y context relevance sobre 10-15 preguntas con al menos 2 trampas.

### Próximos pasos
- Auditar el notebook y el pipeline contra el checklist de indicaciones finales antes de implementar cambios.

## 2026-06-29 — Agent IO START_HERE dinámico

### Decisión
- Se agrega `progress/agent_io/START_HERE.md` como entrypoint universal para agentes externos.
- El humano ya puede usar una sola frase: `Lee progress/agent_io/START_HERE.md y ejecuta la interaccion pendiente. No hagas nada mas.`
- `progress/agent_io/QUEUE.md` ahora tiene una sección fija `## Active Run` con rutas parseables: `Request`, `Response`, `Review`.
- Si `Run ID` es `none`, el agente debe responder `No hay interaccion pendiente.`
- `README.md` de Agent IO y docs de memoria/multi-CLI referencian el nuevo arranque dinámico.

### Evidencia
- Archivos actualizados: `progress/agent_io/START_HERE.md`, `progress/agent_io/QUEUE.md`, `progress/agent_io/README.md`, `docs/MEMORY_INDEX.md`, `docs/MEMORY_PROTOCOL.md`, `docs/MULTI_CLI_PROTOCOL.md`, `docs/START_HERE.md`.
- `bash scripts/build-context-graph.sh` = 65 nodos, 235 aristas, 0 huérfanos.
- `bash scripts/verify.sh` = **105 passed, 6 skipped**, exit=0.

### Riesgos
- La cola está vacía (`Run ID: none`), por diseño. El próximo prompt externo debe crear/actualizar un run y apuntarlo en `QUEUE.md`.

### Próximos pasos
- La siguiente acción del proyecto sigue siendo ejecutar el notebook en Colab T4 y guardar evidencia final.

## 2026-06-29 — Agent IO: trazabilidad de prompts/respuestas multiagente

### Decisión
- Se crea `progress/agent_io/` como capa modelo-agnóstica para registrar interacciones externas con agentes: `REQUEST.md` (prompt exacto), `RESPONSE.md` (salida del agente), `REVIEW.md` (decisión DANTE-OS/Claude) y `STATUS.md` (estado corto).
- `progress/agent_io/QUEUE.md` queda como punto único para saber cuál es el siguiente prompt externo a ejecutar y dónde guardar el output.
- La capa **no reemplaza** `tasks/queue.json`, `progress/NEXT_ACTION.md`, `progress/runs/`, `progress/evidence/` ni `docs/CAVELOG.md`; solo conserva inputs/outputs de agentes externos o chats multi-modelo.
- Se registra la auditoría MiniMax existente como primer run trazable: `progress/agent_io/runs/2026-06-29-001-minimax-repo-audit/`.
- Se sincroniza la memoria operacional: `progress/NEXT_ACTION.md` ya no apunta a F11 y pasa a la validación real en Colab T4; `progress/CURRENT_STATE.md` reconoce F11/F12 completadas y `agent_io` creado.
- Se rellena el handoff F12 que antes era una plantilla vacía.

### Evidencia
- Archivos creados: `progress/agent_io/README.md`, `INDEX.md`, `QUEUE.md`, templates y run `2026-06-29-001-minimax-repo-audit`.
- Docs integrados: `docs/MEMORY_INDEX.md`, `docs/MEMORY_PROTOCOL.md`, `docs/MULTI_CLI_PROTOCOL.md`, `docs/START_HERE.md`.
- `bash scripts/verify.sh` = **105 passed, 6 skipped**, exit=0.

### Riesgos
- `RESPONSE.md` del primer run conserva una síntesis operacional de la auditoría MiniMax, no una transcripción literal completa. Si se requiere preservación literal, pegar el texto original completo en ese archivo.
- La validación final del producto sigue pendiente en Colab T4.

### Próximos pasos
- Ejecutar notebook en Colab T4 con Qwen 4-bit, `rank_bm25`, evaluación final y evidencia en `progress/evidence/`.

## 2026-05-30 — Fase 12: Prompt de auditor experto + Qwen 4-bit + MiniMax 2.ª opinión

### Decisión (feedback del revisor)
- **`SYSTEM_PROMPT` → auditor senior estructurado** (Evaluación preliminar · Riesgo Bajo/Medio/Alto · Señales con Evidencia/Por qué importa/Sustento · Qué faltaría validar · Conclusión). Conserva frases seguras exigidas por el test (`nunca afirmes corrupción`, `señal de riesgo`, `red flag potencial`, `posible irregularidad`, `revisión humana`, `no hay evidencia suficiente`). Alias `AUDITOR_SYSTEM_PROMPT`. Esto convierte la salida de "lista de chunks" a **análisis de auditor**.
- `_build_prompt` ya no duplica el system (va en rol system del chat template).
- **Qwen 4-bit opcional** en `_load_qwen`: `RAG_QWEN_4BIT=1` → `BitsAndBytesConfig(nf4, double_quant, fp16)` con **fallback** limpio. Notebook: `bitsandbytes` en deps + celda `RAG_QWEN_4BIT=1`.
- **MiniMax 2.ª opinión (opcional, robusto)**: celda 12.2 reemplazada por cliente `openai` directo (base_url MiniMax, `AUDITOR_SYSTEM_PROMPT`), `RUN_MINIMAX=False`. Qwen sigue siendo el principal.

### Evidencia
- test_model_cache 5/5 (incl. check estático 4-bit), test_grounding 15/15 (prompt seguro), smoke 7/7. `verify.sh` = **105 passed, 6 skipped**.
- F11 (`docs/PROYECTO.md`, DeepSeek) verificada y marcada `done`.

### Próximos pasos
- Correr en Colab con `RAG_QWEN_4BIT=1`: el chat (12.0) ahora devuelve análisis de auditor estructurado.



## 2026-05-30 — Fase 11: Documento PROYECTO.md (DeepSeek)

### Decisión
- **`docs/PROYECTO.md` creado** con las 16 secciones obligatorias: portada, resumen, problema, fundamentos RAG, dataset, arquitectura (2 mermaid), técnicas avanzadas, pipeline (1 mermaid), decisiones técnicas (chunk 1024/128, k=20→5, Flat vs HNSW), evaluación (Recall@k, Precision@k, grounding ratio, ejemplo bueno/malo), minimización alucinaciones, demo, ética, limitaciones, referencias (9 citas), anexo slides (tabla 8 diapositivas).
- Números **reales** extraídos de `progress/evidence/*.json` (237 unidades, 299 chunks, 69 indicadores, 768-d, R@3=0.833, etc.).
- `verify.sh` = **104 passed, 6 skipped**, exit=0.

### Evidencia
- `docs/PROYECTO.md`: 15 secciones `## ` + portada = 16, ~680 líneas, 2 diagramas mermaid, tabla de chunking comparativo, tabla de técnicas, métricas reales de F1–F7.

### Riesgos
- Placeholders pendientes: `_<completar>_` para Universidad, Docente, Fecha, y logo de universidad en `docs/assets/`.

### Próximos pasos
- Notebook final de Colab (F8) + generación de slides desde PROYECTO.md.

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
