# Handoff — 2026-07-14-2058 — merge-v2-main-presentacion

## CLI usado
OpenCode

## Objetivo
Verificar, publicar y promover la versión V2 a `main`, dejando producción y enlaces de presentación consistentes.

## Archivos tocados
- `apps/web/**`, `apps/api/app/main.py`, `scripts/deploy-api.sh`
- `notebooks/redflags_rag_colab.ipynb`, `packages/rag_core/notebook_rag.py`, `packages/rag_core/vector_store.py`
- `apps/api/app/services/orchestrator.py` y tests de integración herméticos
- `README.md`, `specs/007-v2-production.md`, `docs/CAVELOG.md`, `progress/**`
- `data/samples/**` con documentos públicos usados en la validación

## Decisiones
- Next.js/Vercel es el frontend principal; FastAPI/Cloud Run es la API y Streamlit queda como respaldo.
- La promoción a `main` preserva la historia mediante merge; no usa force-push.
- Los tests de orquestación inyectan chunks deterministas para no cargar el CrossEncoder real.
- `.env*` se excluye de Git y del contexto de despliegue de Google Cloud.

## Comandos ejecutados
```bash
bash scripts/init.sh
bash scripts/verify.sh
npm run lint
npm run build
gcloud meta list-files-for-upload
# smoke HTTP de Vercel, Cloud Run API y Streamlit
```

## Resultado
V2 quedó verificada y preparada para `main`: frontend de producto, API cloud, notebook dual RAG opcional y muestras reales documentadas. La demora del gate local fue eliminada sin cambiar la ruta de producción.

## Evidencia
- `bash scripts/verify.sh`: 258 passed, 6 skipped en 50.58 s.
- Next.js: lint y build OK; `/`, `/analizar`, `/como-funciona` y `/documentos` estáticas.
- Producción: frontend, API `/health` + `/api/tdrs` y Streamlit responden HTTP 200.
- `.env` no aparece en `gcloud meta list-files-for-upload`.

## Riesgos
- SQLite en `/tmp` es efímero y Cloud Run presenta 4-7 s de arranque en frío.
- El `Run all` académico en Colab T4 sigue requiriendo autenticación humana.
- Rotar las credenciales locales si se compartieron fuera del equipo.

## Próxima acción exacta
Abrir el notebook en Colab T4, ejecutar `Run all` sin intervención y guardar el `ragas-report.json` definitivo.
