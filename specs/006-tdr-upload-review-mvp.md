# Spec 006 — TDR Upload Review MVP

Estado: ACTIVA
SDD: esta spec es la **fuente de verdad** para convertir el RAG actual en una interfaz web desplegable y publicable para el proyecto final de curso.

## 1. Specify — qué y por qué

El proyecto ya tiene un RAG especializado en red flags de contratación pública: guía OCP/OCDS indexada, retrieval híbrido, reranking, Qwen, grounding, citas, refusal y evaluación RAGAS local. El siguiente paso de producto no es scraping SEACE ni una arquitectura pesada, sino una web simple donde una persona pueda subir un TDR/bases de contratación y recibir un dossier de revisión preliminar.

Usuario objetivo:
- Evaluador del curso que necesita ver un producto funcionando, no solo notebook.
- Auditor, periodista, ciudadano o empresa que quiere una lectura preliminar de señales de riesgo potenciales en un TDR.
- Portafolio público: demo clara, segura y explicable en X/LinkedIn.

Resultado esperado:
- Subir un PDF/texto de TDR.
- Extraer texto y calcular hash de versión.
- Ejecutar el RAG existente sobre el texto del TDR.
- Mostrar un dossier con señales de riesgo potenciales, evidencia, citas a la guía OCP/OCDS, grounding, nivel de riesgo preliminar e incertidumbre.
- Mantener lenguaje seguro: no afirmar corrupción, fraude ni ilegalidad; cerrar con revisión humana.

Inspiración y límite:
- Agente Perry demuestra una arquitectura objetivo más grande: classifier, OCR, retrieval, planner, evidence critic, risk scoring, CDC y graph enrichment.
- Esta spec toma esa dirección, pero implementa una versión manual, verificable y multiagent-ready.
- SEACE automático, Neo4j, OCR avanzado y LangGraph real quedan fuera de esta primera etapa.

## 2. Plan — cómo (alto nivel)

### 2.1 Decisión de despliegue del LLM

El riesgo principal no es FastAPI ni SQLite, es desplegar modelos locales pesados. Qwen-3B, e5-base, bge-reranker y FAISS no caben cómodamente en un tier gratis CPU de Render/Railway/Fly.

Decisión F16.1:
- La web desplegada debe usar `generate_fn` con un LLM por API para generación.
- Qwen local queda como respaldo técnico en Colab/notebook.
- Los tests y CI deben usar `generate_fn` falso/determinista.
- El reranker puede omitirse en la ruta desplegada si el costo de memoria lo exige; debe quedar documentado como modo demo-web vs modo notebook-full.

### 2.2 Arquitectura multiagent-ready

No se crean varios procesos ni varias llamadas LLM al inicio. Se definen contratos de agentes reemplazables, implementados primero como funciones/servicios deterministas.

```text
Upload TDR
  ↓
TdrIntakeAgent
  - guarda archivo/texto
  - extrae texto
  - calcula sha256/version_hash
  ↓
AnalysisAgent
  - llama packages.rag_core.agent.analyze(tdr_text, generate_fn=...)
  ↓
EvidenceCriticAgent
  - feature visible del dossier
  - acepta/rechaza señales según citations, grounding_ratio y refusal
  ↓
RiskScoringAgent
  - Bajo / Medio / Alto / Evidencia insuficiente
  ↓
DossierAgent
  - JSON primero
  - HTML después
```

Contratos iniciales:
- `TdrIntakeAgent`: input archivo/texto; output texto extraído, hash, metadata y limitaciones detectadas.
- `AnalysisAgent`: input texto TDR; output dict real de `agent.analyze`: `answer`, `sentences`, `citations`, `grounding_ratio`, `refusal`, `retrieved`.
- `EvidenceCriticAgent`: input resultado de análisis; output `accepted_findings`, `rejected_findings`, `evidence_status`, `notes`.
- `RiskScoringAgent`: input análisis + crítica; output `risk_level`, `risk_reason`.
- `DossierAgent`: input todo lo anterior; output JSON/HTML seguro para usuario final.

### 2.3 EvidenceCritic como feature principal

El dossier debe mostrar explícitamente el gate anti-alucinación. Esto diferencia el producto de un RAG genérico.

Ejemplo de UI/dossier:
- `3 señales aceptadas con cita`.
- `1 señal rechazada por evidencia insuficiente`.
- `Grounding ratio: 0.72`.
- `Citas recuperadas: R031 p.XX-YY, R024 p.XX-YY`.
- `No se determina corrupción ni ilegalidad. Requiere revisión humana.`

Reglas V1:
- Si `refusal` no está vacío: `evidence_status = insufficient`.
- Si `grounding_ratio < 0.25`: `evidence_status = weak`.
- Si no hay `citations`: `evidence_status = weak`.
- Si hay citas y grounding suficiente: `evidence_status = sufficient`.
- Una señal sin cita literal no debe presentarse como aceptada.

### 2.4 Procesamiento asíncrono desde el modelo de datos

El análisis puede tardar 20-90 segundos. No debe bloquear el request de upload.

V1 simple:
- `POST /tdrs/upload` crea TDR y versión, estado `uploaded`.
- `POST /tdrs/{id}/analyze` crea `analysis_run` con estado `queued` o `running`.
- En implementación inicial puede ejecutarse sin cola externa, pero el modelo de datos y API deben exponer estados.
- La UI debe mostrar `uploaded`, `running`, `completed`, `failed`.

No introducir Celery/Redis en F16. Si hace falta background real, usar `BackgroundTasks` de FastAPI como paso intermedio.

### 2.5 Persistencia mínima

SQLite para demo local/despliegue sencillo.

Tablas conceptuales:
- `tdrs`: `id`, `filename`, `uploaded_at`, `status`.
- `tdr_versions`: `id`, `tdr_id`, `sha256`, `file_path`, `text_path`, `created_at`, `parser_notes`.
- `analysis_runs`: `id`, `tdr_version_id`, `status`, `model_name`, `grounding_ratio`, `refusal`, `risk_level`, `risk_reason`, `created_at`, `completed_at`, `error_message`.
- `risk_findings`: `id`, `analysis_run_id`, `title`, `severity`, `evidence_quote`, `citation`, `explanation`, `accepted`, `rejection_reason`, `requires_human_review`.
- `evidence_reviews`: `id`, `analysis_run_id`, `evidence_status`, `accepted_count`, `rejected_count`, `notes`.

Este hash/versionado deja preparada la transición a CDC:
- mismo hash: no reanalizar por defecto.
- nuevo hash: nueva versión, nuevo análisis.

### 2.6 API mínima

Extender `apps/api/app/main.py` o modularizar bajo `apps/api/app/` sin reescritura amplia.

Endpoints V1:
- `GET /` landing HTML simple.
- `GET /health` existente.
- `POST /tdrs/upload` subir PDF/texto.
- `GET /tdrs` lista de TDRs.
- `GET /tdrs/{id}` detalle operativo.
- `POST /tdrs/{id}/analyze` dispara análisis.
- `GET /tdrs/{id}/dossier` dossier JSON/HTML.

Orden de entrega:
1. Dossier JSON end-to-end.
2. HTML simple.
3. Polish visual si queda tiempo.

### 2.7 UI mínima

FastAPI + HTML server-rendered. No Next.js en F16.

Pantallas:
- Landing: qué hace, límites, lenguaje seguro.
- Upload: PDF/texto, disclaimer de PDFs de texto.
- Lista: archivo, fecha, estado, riesgo.
- Dossier: señales aceptadas/rechazadas, citas, grounding, incertidumbre y próximos pasos.

### 2.8 PDFs soportados

F16 soporta preferentemente PDFs basados en texto y/o texto pegado. OCR queda diferido.

Disclaimer obligatorio:
- `Esta demo funciona mejor con PDFs basados en texto. Los documentos escaneados pueden requerir OCR y revisión manual.`

Si el extractor no obtiene texto suficiente:
- estado `failed` o `needs_text_input`.
- mostrar instrucción para pegar texto manualmente.

## 3. Tasks — descomposición

- [ ] F16.1: definir `generate_fn` de producción por API y fake determinista para tests; documentar modo notebook-full vs demo-web.
- [ ] F16.2: crear persistencia SQLite mínima para TDRs, versiones, analysis_runs, risk_findings y evidence_reviews.
- [ ] F16.3: implementar intake de PDF/texto con hash, guardado local y notas de parser.
- [ ] F16.4: implementar `AnalysisAgent` como wrapper de `packages.rag_core.agent.analyze` sin reescribir el RAG.
- [ ] F16.5: implementar `EvidenceCriticAgent` V1 con reglas deterministas y salida visible para dossier.
- [ ] F16.6: implementar `RiskScoringAgent` V1.
- [ ] F16.7: implementar endpoints JSON y tests API.
- [ ] F16.8: shippear dossier JSON end-to-end antes de tocar HTML.
- [ ] F16.9: implementar HTML server-rendered mínimo.
- [ ] F16.10: preparar deploy simple y README/demo para portafolio.

## 4. Criterios de aceptación (verificables)

- [ ] `bash scripts/init.sh` pasa antes de modificar código.
- [ ] `bash scripts/verify.sh` pasa al cierre.
- [ ] Tests API cubren `/health`, upload, lista, análisis fake y dossier.
- [ ] Se puede subir un TDR PDF textual o texto pegado.
- [ ] El sistema calcula y persiste `sha256` por versión.
- [ ] Re-subir el mismo contenido no debe crear un análisis nuevo por defecto, o debe marcar duplicado explícitamente.
- [ ] `POST /tdrs/{id}/analyze` usa `agent.analyze(..., generate_fn=...)`.
- [ ] El análisis no depende de GPU en tests ni en la demo-web desplegada.
- [ ] El dossier muestra `grounding_ratio`, `citations`, `refusal` si existe, y estado del EvidenceCritic.
- [ ] El dossier separa señales aceptadas de señales rechazadas por evidencia insuficiente.
- [ ] Todo output usa lenguaje seguro: señales de riesgo, posibles irregularidades a revisar, no se determina corrupción, requiere revisión humana.
- [ ] La UI incluye disclaimer de PDFs basados en texto y limitación OCR.
- [ ] Existe una URL local o desplegada con landing, upload y dossier.

## 5. Fuera de alcance

- Scraping o ingesta automática de SEACE/OSCE.
- Seguimiento automático de ganador/adjudicación.
- OCR avanzado para PDFs escaneados.
- Neo4j, grafo de proveedores o enrichment por RUC.
- LangGraph/orquestador multiagente real.
- Next.js o frontend separado.
- Celery, Redis o colas externas.
- Librería oficial `ragas` o APIs externas para evaluación RAGAS.
- Afirmar corrupción, fraude, ilegalidad o responsabilidad.

## 6. Roadmap posterior

- F17: EvidenceCritic con retry/retrieval reformulation cuando la evidencia sea débil.
- F18: CDC manual sobre nuevas versiones del TDR.
- F19: spike de viabilidad SEACE/OSCE con evidencia legal/técnica.
- F20: `TenderSource` para SEACE solo si el spike confirma acceso viable.
- F21: seguimiento de adjudicación/proveedor.
- F22: graph enrichment inspirado en Agente Perry.
