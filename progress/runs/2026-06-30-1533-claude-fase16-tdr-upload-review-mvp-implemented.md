# Handoff — 2026-06-30-1533 — fase16-tdr-upload-review-mvp-implemented

## CLI usado
OpenCode

## Objetivo
Implementar el MVP web TDR Risk Review multiagent-ready definido en `specs/006-tdr-upload-review-mvp.md`, reutilizando el RAG core existente con `generate_fn` inyectable y exponiendo UI server-rendered + API JSON.

## Archivos tocados
- `pyproject.toml` (deps nuevas: jinja2, python-multipart, pydantic-settings, sqlmodel, google-generativeai).
- `.env.example` (Google API key + DATABASE_URL + UPLOAD_DIR + RAG_GEMINI_MODEL).
- `apps/api/app/config.py` (settings con pydantic-settings).
- `apps/api/app/db.py` (SQLModel engine + init_db).
- `apps/api/app/models.py` (tablas: Tdr, TdrVersion, AnalysisRun, RiskFinding, EvidenceReview).
- `apps/api/app/schemas.py` (Pydantic request/response).
- `apps/api/app/services/intake.py` (PDF/texto + SHA-256 + persistencia).
- `apps/api/app/services/analysis.py` (wrapper de `packages.rag_core.agent.analyze` con `generate_fn`).
- `apps/api/app/services/evidence.py` (EvidenceCritic V1).
- `apps/api/app/services/scoring.py` (RiskScoring V1).
- `apps/api/app/services/dossier.py` (DossierAgent con disclaimers seguros).
- `apps/api/app/services/orchestrator.py` (queue + run + persistencia + dossier).
- `apps/api/app/adapters/google_llm.py` (adapter Gemini + stub determinista).
- `apps/api/app/adapters/llm_factory.py` (resolver LLM por env).
- `apps/api/app/routes/tdrs.py` (rutas HTML + JSON API).
- `apps/api/app/templates/` (base, home, upload, list, detail, run_status, dossier, dossier_pending).
- `apps/api/app/main.py` (FastAPI app + startup init_db).
- `apps/api/tests/test_health.py` (actualizado).
- `apps/api/tests/test_intake.py` (nuevo).
- `apps/api/tests/test_evidence_scoring.py` (nuevo).
- `apps/api/tests/test_pipeline.py` (nuevo).
- `progress/NEXT_ACTION.md` (apunta a F16.2).
- `progress/CURRENT_STATE.md` (refleja F16 implementado).
- `progress/HANDOFF.md` (apunta a este handoff).
- `docs/CAVELOG.md` (entrada F16).

## Decisiones
- Stack Google: `google-generativeai` con `gemini-1.5-flash` por API; fallback fake determinista si no hay `GOOGLE_API_KEY`.
- Embeddings e índice FAISS del notebook se mantienen; el wrapper solo invoca `agent.analyze(query=tdr_text, generate_fn=...)`.
- Arquitectura multiagent-ready por contratos: `TdrIntakeAgent` → `AnalysisAgent` (wrapper RAG) → `EvidenceCriticAgent` V1 (reglas deterministas) → `RiskScoringAgent` V1 (reglas deterministas) → `DossierAgent`.
- EvidenceCritic es feature visible del dossier: separa señales aceptadas (con cita) vs rechazadas (sin cita), y muestra grounding ratio, evidencia_status y refusal.
- Lenguaje seguro mantenido en todos los outputs y templates: "señales de riesgo potenciales", "Requiere revisión humana", "No es una acusación ni determina responsabilidad".
- Persistencia SQLite para demo, SQLModel 0.0.x sin relaciones bidireccionales (consultas manuales por FK).
- Frontend Jinja2 server-rendered + Tailwind CDN; sin build step.

## Comandos ejecutados
```bash
bash scripts/init.sh
python3 -m pip install --break-system-packages sqlmodel google-generativeai pydantic-settings python-multipart jinja2 httpx
bash scripts/verify.sh
python3 -m uvicorn app.main:app --port 8771 --host 127.0.0.1   # smoke real
curl -X POST http://127.0.0.1:8771/api/tdrs/upload -F pasted_text=... -F auto_analyze=true
curl http://127.0.0.1:8771/api/runs/{id}
curl http://127.0.0.1:8771/api/tdrs/{id}/dossier
bash scripts/handoff.sh "fase16-tdr-upload-review-mvp-implemented"
```

## Resultado
TDR Risk Review MVP funcional end-to-end:
- Upload de TDR (PDF/texto pegado) → hash SHA-256 por versión.
- Análisis automático con `agent.analyze` y `generate_fn` Gemini.
- Dossier con riesgo preliminar, grounding ratio, evidencia aceptada/rechazada, incertidumbre, próximos pasos y disclaimer.
- HTML server-rendered para todas las pantallas (home, upload, list, detail, run_status, dossier, dossier_pending).
- JSON API completo (`/api/tdrs/...`, `/api/runs/...`) para integraciones.
- Estados asíncronos del modelo: `uploaded | queued | running | completed | failed`.

## Evidencia
- `bash scripts/verify.sh` → **169 passed, 6 skipped** (exit 0).
- Smoke real con uvicorn en `127.0.0.1:8771`:
  - `POST /api/tdrs/upload` con texto pegado → `tdr_id=6`, `version_id=6`, `analysis_run_id=6`.
  - `GET /api/runs/6` → `status=completed`, `risk_level="Evidencia insuficiente"`, `grounding_ratio=0.2143`, `refusal` seguro.
  - `GET /api/tdrs/6/dossier` → JSON con `summary`, `evidence`, `uncertainty`, `next_steps`, `disclaimer`.
  - `GET /` → HTTP 200 con HTML renderizado.
  - `GET /tdrs/upload` → HTTP 200 con HTML renderizado.
  - `GET /tdrs/6/dossier` → HTTP 200 con HTML renderizado del dossier.

## Riesgos
- F15.3 Colab Run all (evidencia neural del notebook académico) sigue pendiente como entregable paralelo de la UNI.
- Sin OCR para PDFs escaneados: el intake devuelve mensaje claro y sugiere pegar el texto manualmente.
- El deploy real en Cloud Run / Render requiere configurar `GOOGLE_API_KEY` real y `UPLOAD_DIR` persistente; mientras no haya key, el fallback fake permite que la app arranque.

## Próxima acción exacta
Levantar uvicorn con `GOOGLE_API_KEY` real, subir un fragmento real del corpus OCP/OCDS, guardar el dossier JSON en `progress/evidence/f16_real_gemini_dossier.json` y documentar el cierre en `docs/CAVELOG.md`.
