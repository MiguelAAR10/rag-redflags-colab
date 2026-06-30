# V2 — Vigilancia activa de licitaciones con detección de Red Flags

> **Para quien lee esto (humano o agente):** este es el roadmap y la justificación de
> arquitectura de la V2. La V1 (el RAG que analiza texto contra la guía OCP de *red flags*)
> está **completa y testeada**. La V2 le añade un aparato de **ingesta activa + detección de
> cambios (CDC) + despliegue web**. Lee primero la sección 1 ("Razonamiento") — explica *por
> qué* el diseño es este y no otro.
>
> Estado: **propuesta aprobada, branch `v2`.** Aún no implementada. Punto de entrada para
> colaboradores. Antes de tocar código, ejecutar la **Fase 0 (Spike de datos)**.

## 0. Resumen ejecutivo

Construir, sobre el RAG existente, un sistema que **vigila licitaciones públicas peruanas
vivas** (SEACE/OSCE), detecta **cuándo cambian sus TDR/bases** sin re-scrapear todo, las pasa
por el motor de red flags, y publica los hallazgos en un **dashboard web desplegado**.

**Esfuerzo realista:** MVP desplegado en **~3-4 semanas a tiempo parcial**, condicionado al
*Spike de datos* (Fase 0). Los dos riesgos que pueden recortar alcance son el acceso a datos y
el hosting del LLM; el resto es ingeniería estándar sobre una base sólida.

---

## 1. Razonamiento de arquitectura (el "por qué", no solo el "qué")

### 1.1 Insight central: hay DOS corpus, y V1 solo tiene uno
El sistema mezcla conceptualmente dos cosas que conviene separar:

- **Base de conocimiento (estándar):** la guía OCP de red flags, ya chunked e indexada en
  FAISS (`data/index/redflags_flatip.index`, 299 vectores). Es contra lo que se *juzga*.
- **Sujetos a analizar (evidencia):** los TDR/licitaciones reales. Hoy **no existen** en el
  sistema; se inyectan a mano como texto en el notebook.

El RAG *recupera del estándar* para fundamentar un veredicto sobre *un sujeto*. Por tanto la V2
**no toca el índice FAISS del estándar**: añade un pipeline que trae sujetos nuevos y los
empuja al motor. Consecuencia práctica: **el cerebro ya está hecho**; el riesgo de la V2 está
en los bordes (ingesta, datos, deploy), no en el núcleo de IA. Esto es lo que hace el proyecto
viable en semanas y no en meses.

### 1.2 Por qué el LLM se desacopla (y por qué eso ya es casi gratis)
`packages/rag_core/agent.py` **ya** acepta un `generate_fn` inyectable (se usa hoy para tests
sin modelo). El motor no está casado con Qwen. Decisión de arquitecto:
- **Notebook/demo académico:** Qwen2.5-3B 4-bit en GPU T4 (gratis en Colab, reproducible para
  el evaluador).
- **Producción web:** un **LLM por API** detrás del mismo `generate_fn` → sin GPU, sin gestionar
  pesos, escala trivial y barato a bajo volumen.

Hostear Qwen en la nube con GPU (HF Spaces/Modal/RunPod) es posible pero introduce costo fijo y
complejidad de ops que **no aporta valor** a un MVP. Se deja como alternativa documentada, no
como camino principal.

### 1.3 Por qué CDC por hashing (y no algo más sofisticado)
Requisito: "detectar modificaciones en el TDR sin re-scrapear todo". La solución correcta y
*barata* es **Change Data Capture por contenido**: hash del documento + watermark de fecha.
- `loaders.py` **ya** calcula un `hash` por unidad documental → se reutiliza el patrón.
- Por cada `(licitación, documento)` se guarda `version_hash`, `etag`/`last_modified` si la
  fuente los da, y `fetched_at`.
- Cada corrida pide solo metadata ligera (o HEAD/etag). Si el hash cambió → re-descargar,
  re-analizar y **registrar un `change_event`**. Si no → no se hace nada.
- No hace falta CDC de base de datos (Debezium, binlogs): eso es para fuentes transaccionales
  propias, no para una fuente externa que consultamos. Sería sobre-ingeniería.

### 1.4 Por qué fuente abstraída (`TenderSource`)
El acceso a datos es el **mayor desconocido** (ver Fase 0). La ingesta se diseña detrás de una
interfaz `TenderSource` con tres implementaciones intercambiables: API OCDS, descarga bulk
CSV/JSON, y scraping HTML como último recurso. Así el resto del sistema (CDC, análisis, web) se
construye **sin depender** de cuál resulte viable. Es el patrón Adapter donde más
incertidumbre hay.

---

## 2. Evaluación realista de dificultad

| Componente | Dificultad | Justificación |
|---|---|---|
| **Acceso a datos SEACE/OSCE** | ⚠️ **RIESGO #1 — sin verificar** | API OCDS / datos abiertos bulk → fácil. Solo portal HTML con formularios/captcha → frágil. **Validar en Fase 0 antes de comprometer alcance.** |
| CDC por hashing | 🟢 Fácil (2-3 d) | Reusa `hash` de `loaders.py`. Watermark + comparación. |
| Cablear ingesta → RAG | 🟢🟡 Fácil-Medio (2-3 d) | `agent.py` ya recibe texto + `generate_fn`. Trabajo real = robustez extracción PDF de TDR. |
| Persistencia (DB) | 🟢 Fácil (2 d) | SQLite (demo) → Postgres (prod), SQLModel. |
| Backend web | 🟡 Medio (3-4 d) | Extender stub FastAPI (`apps/api/app/main.py`, hoy solo `/health`). |
| Frontend dashboard | 🟡 Medio (4-5 d) | Listado + detalle con citas + feed de cambios. |
| Despliegue LLM | 🟡🔴 Medio-Duro (3-5 d) | API LLM (recomendado, sin GPU) vs GPU hosting (caro/complejo). |

**Lo que puede matar el alcance:** (1) datos solo accesibles por scraping hostil/ilegal;
(2) exigir LLM local en prod (fuerza GPU). Mitigación de ambos ya prevista en el diseño.

---

## 3. Arquitectura

```
┌─ SCHEDULER (cron / GitHub Action) — la parte "activa" ───────┐
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ packages/ingest/ (NUEVO) ──────────────────────────────────┐
│  TenderSource (interfaz)                                      │
│   ├─ OCDSApiSource     (preferido si existe)                  │
│   ├─ BulkCSVSource     (datos abiertos descargables)          │
│   └─ SeaceHtmlScraper  (fallback, rate-limit + cache)         │
│  → convocatorias del mes + refs a documentos (TDR)            │
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ CDC (NUEVO) ───────────────────────────────────────────────┐
│  (tender_id, doc_id) → version_hash, etag, fetched_at         │
│  hash cambió → re-descarga + re-analiza + change_event        │
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ Análisis (REUSA rag_core) ─────────────────────────────────┐
│  loaders.py (texto TDR) → agent.py (red flags)                │
│  → risk_findings + citas a guía OCP + grounding_ratio         │
│  LLM vía generate_fn: API (prod) / Qwen (notebook)            │
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ Persistencia ── SQLite(demo)/Postgres(prod) ───────────────┐
│  tenders · documents · doc_versions · change_events · findings│
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ Web (deploy) ──────────────────────────────────────────────┐
│  Backend FastAPI (apps/api, extender)                         │
│  Frontend dashboard (Next.js/React o FastAPI+HTMX)            │
│   · licitaciones vigiladas + nivel de riesgo                  │
│   · detalle: señales + citas + grounding                      │
│   · feed "qué cambió" (CDC)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Esquema de datos (mínimo)
- `tenders(id, source, entity, title, amount, status, first_seen, last_seen)`
- `documents(id, tender_id, kind[TDR/bases/addenda], url)`
- `doc_versions(id, document_id, version_hash, etag, fetched_at, text_ref)`
- `change_events(id, document_id, from_hash, to_hash, detected_at, summary)`
- `risk_findings(id, tender_id, doc_version_id, signals_json, grounding_ratio, refusal, created_at)`

---

## 4. Fases

**Fase 0 — Spike de viabilidad de datos (GATE, 1-2 d) ⚠️ PRIMERO**
Confirmar fuente real: ¿OCDS / API en `datosabiertos.gob.pe` o `contratacionesabiertas`?
¿Bulk CSV/JSON mensual? ¿PDF de TDR descargables o solo UI? ¿Registros de addenda/modificación?
ToS y rate-limits. Proyectos open-source previos. **Entregable:** qué `TenderSource` se
implementa primero. Si solo hay scraping hostil → reducir a "subida manual de TDR + CDC sobre
lo subido".

**Fase 1 — Ingesta + persistencia (3-4 d):** `packages/ingest/{sources,models}.py`, DB SQLModel,
tests de contrato con fixtures (sin red en CI).

**Fase 2 — CDC (2-3 d):** `packages/ingest/cdc.py`; tests deterministas (mismo doc → 0 eventos;
doc modificado → 1 evento).

**Fase 3 — Wiring al motor (2-3 d):** `packages/ingest/analyze.py`: TDR → `rag_core.agent` →
persistir findings. `generate_fn` API en prod / Qwen en notebook. Reusar `evals/ragas_metrics.py`.

**Fase 4 — Backend (3-4 d):** extender `apps/api`: `GET /tenders`, `/tenders/{id}`, `/changes`,
`POST /ingest/run`, `POST /analyze`. Lógica en capa de servicios, no en endpoints.

**Fase 5 — Frontend (4-5 d):** dashboard con tabla + badges de riesgo, detalle con citas a la
guía OCP, feed de cambios. Next.js+Tailwind (o FastAPI+HTMX si se quiere mínimo).

**Fase 6 — Deploy + scheduler (3-5 d):** Dockerizar API; Postgres gestionada; LLM por API;
scheduler (GitHub Action / cron → `POST /ingest/run`); frontend en Vercel/Netlify, backend en
Fly.io/Render/Railway.

---

## 5. Archivos

**Nuevo:** `packages/ingest/{__init__,sources,models,cdc,analyze}.py` + `tests/`;
`apps/api/app/{routes,services,db}.py`; `apps/web/`; `Dockerfile`, `docker-compose.yml`,
`.github/workflows/ingest.yml`.

**Reutilizar (no reescribir):** `rag_core/agent.py` (`generate_fn`), `rag_core/loaders.py`
(PDF + hash), `rag_core/{retrievers,rerankers,verifier,citations}.py`, `evals/ragas_metrics.py`.

---

## 6. Verificación end-to-end
1. **F0:** doc con fuente confirmada + `TenderSource` elegido.
2. **Ingesta+CDC:** `pytest packages/ingest/tests -q` verde; correr ciclo 2× → 2ª vez sin
   `change_events` salvo cambios reales.
3. **Análisis:** licitación de prueba → `risk_findings` con citas y `grounding_ratio`; RAGAS
   local en umbrales actuales.
4. **API:** endpoints responden con datos de la DB.
5. **Deploy:** URL pública; el scheduler corre y aparece una licitación/cambio sin intervención.
6. `bash scripts/verify.sh` verde en cada fase.

---

## 7. Nota sobre la "burocracia" del repo
La maquinaria de proceso aporta **~70% de valor real** (coordina 5 CLIs, gatea tests con
`verify.sh`, registra decisiones en CAVELOG) y **~30% es ceremonia consolidable** (3 archivos de
estado solapados, specs ~1 mes atrasadas). Para V2, sin reescribir el harness: crear
`specs/006-ingest-cdc-deploy.md` para que la spec no quede detrás, y **reusar** las capas de
tracking existentes en vez de inventar nuevas.
