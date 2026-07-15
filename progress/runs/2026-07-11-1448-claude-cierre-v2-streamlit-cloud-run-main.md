# Handoff — 2026-07-11-1448 — cierre-v2-streamlit-cloud-run-main

## CLI usado
OpenCode

## Objetivo
Cerrar V2, verificar la plataforma pública y dejar notebook/documentación listos para publicar en `main`.

## Archivos tocados
- `README.md`, `docs/COLAB.md`, `docs/CAVELOG.md`
- `specs/007-v2-production.md`
- `notebooks/redflags_rag_colab.ipynb`
- `packages/rag_core/tests/test_notebook_smoke.py`
- `progress/CURRENT_STATE.md`, `progress/NEXT_ACTION.md`

## Decisiones
- Streamlit reemplaza Next.js y comparte contenedor con el orquestador; hay una URL pública única.
- Self-RAG queda fuera del alcance final.
- SQLite efímero se acepta para la demo y se declara como limitación; Qdrant conserva embeddings.
- `HF_TOKEN` es opcional y no puede bloquear `Run all` con entrada manual.

## Comandos ejecutados
```bash
bash scripts/init.sh
bash scripts/verify.sh
python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py -q
gcloud run services describe tdr-risk-auditor --region us-central1
# QA browser sobre la URL pública y prueba texto -> dossier
```

## Resultado
Cloud Run sirve la interfaz Streamlit y el flujo real con Vertex AI + Qdrant produce un dossier. README, spec y guía Colab reflejan la arquitectura final. El notebook ya no contiene prompts interactivos.

## Evidencia
- Cloud Run revision `tdr-risk-auditor-00001-6mq`, ready, tráfico 100%, root y health HTTP 200.
- E2E público: 449 caracteres, TDR #1, run #1, 3 señales aceptadas, 0 rechazadas, grounding 1.00.
- `bash scripts/verify.sh`: 209 passed, 6 skipped.
- `test_notebook_smoke.py`: 8 passed; JSON y `git diff --check` válidos.

## Riesgos
- Colab T4 no se pudo ejecutar sin iniciar sesión Google; el baseline RAGAS offline sigue pendiente de reemplazo.
- La prueba E2E mostró una cita R003 de plazo corto asociada también a la señal de oferente único; requiere revisión humana/hardening.
- La metadata SQLite puede perderse al desplegar una nueva revisión de Cloud Run.

## Próxima acción exacta
Iniciar sesión en Colab, ejecutar `Run all` en T4 y traer el `ragas-report.json` generado.
