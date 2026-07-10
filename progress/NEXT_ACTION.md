# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**Fase 16.2 — Desplegar TDR Risk Review MVP con `GOOGLE_API_KEY` real y validar un TDR del corpus OCP.**

- **Branch:** `feature/final-evaluation-ragas`
- **Owner:** Humano + DANTE-OS
- **Base:** `specs/006-tdr-upload-review-mvp.md` aceptada; código F16 implementado en `apps/api/`.

## Objetivo

Levantar el servidor con `GOOGLE_API_KEY` real, subir un TDR de prueba (texto de los TDR que usa el notebook), capturar el dossier JSON final y documentar el resultado en `progress/evidence/f16_real_gemini_dossier.json`. Confirmar que el flujo `intake → analysis → critic → scoring → dossier` produce señales aceptadas/rechazadas con grounding_ratio > 0.

## Archivos a tocar

- `apps/api/` solo si se necesita un ajuste mínimo por Gemini real.
- `progress/evidence/f16_real_gemini_dossier.json` (evidencia del dossier real).
- `progress/runs/<stamp>-<cli>-fase16-2-real-gemini.md` (handoff).
- `docs/CAVELOG.md` (append cierre de F16.2).

## Archivos protegidos

- `notebooks/redflags_rag_colab.ipynb`
- `data/processed/*`, `data/index/*`, `.env`
- `packages/rag_core/*.py`
- `progress/evidence/ragas-report.json` salvo que sea F15.3 Colab explícito.

## Criterios de aceptación

- [ ] Servidor uvicorn corriendo con `GOOGLE_API_KEY` configurada.
- [ ] Upload de un fragmento real del corpus OCP/OCDS genera dossier con al menos una señal aceptada.
- [ ] `grounding_ratio > 0` y `evidence.status` consistente con la evidencia recuperada.
- [ ] `progress/evidence/f16_real_gemini_dossier.json` registrado.
- [ ] `bash scripts/verify.sh` sigue verde.

## NO hacer

- No desplegar a Cloud Run / Render todavía (eso es F16.3).
- No añadir OCR ni SEACE.
- No introducir otra LLM distinta a Gemini.
- No afirmar corrupción ni ilegalidad; mantener lenguaje seguro.
