# Handoff — 2026-07-14-2222 — colega-ragas-ci-pdfs-demo

## CLI usado
OpenCode

## Objetivo
Auditar el notebook externo, recuperar el camino Colab roto, fortalecer RAGAS/seguridad y publicar PDFs de demostración descargables sin lenguaje acusatorio.

## Archivos tocados
- `data/raw/`, `data/processed/`, `data/index/` (cinco artefactos Colab restaurados)
- `data/eval/{goldset,abstention_set}.jsonl`, `packages/evals/metrics.py`
- `notebooks/redflags_rag_colab.ipynb`, `progress/evidence/ragas-report.json`
- `.github/workflows/ci.yml`, `pyproject.toml` y tests Python/Next.js
- `apps/web/src/app/documentos/**`, `data/samples/README.md`
- `docs/CAVELOG.md`, `progress/{CURRENT_STATE,NEXT_ACTION,HANDOFF}.md`

## Decisiones
- No integrar `trabajo-colega/redflags_rag_colab.ipynb` completo; adaptar únicamente casos útiles.
- Mantener 15 preguntas: 11 respondibles y 4 de seguridad, con métricas separadas.
- Descargar demos desde GitHub raw/main; no duplicar 19 MB en Vercel.
- CI ejecuta Python, Vitest, lint y build; modelos neuronales son extra opcional.

## Comandos ejecutados
```bash
bash scripts/init.sh
bash scripts/verify.sh
npm --prefix apps/web test
npm --prefix apps/web run lint
npm --prefix apps/web run build
# instalación editable + pytest en venv limpio
```

## Resultado
El clone de GitHub vuelve a contener PDF, procesados e índice para Colab. El gold set tiene oráculos y seguridad separada. `/documentos` mantiene seis descargas aunque falle la API. CI ya no puede quedar verde sin ejecutar pytest y frontend.

## Evidencia
- `bash scripts/verify.sh`: 271 passed, 6 skipped.
- Entorno limpio: 260 passed, 16 skips opcionales, 0 fallos.
- Vitest: 1 passed; ESLint y Next.js build exit 0.
- `progress/evidence/ragas-report.json`: baseline offline con `n=15`, `n_answerable=11`, `traps=4`.
- Seis PDFs con firma `%PDF-` y catálogo accesible.

## Riesgos
- Falta `Run all` neural real en Colab T4 autenticado.
- Los enlaces raw deben comprobarse tras el push; antes del push los cinco artefactos Colab aún no existen en remoto.
- Persistencia SQLite web continúa siendo efímera.

## Próxima acción exacta
Ejecutar `Run all` en Colab T4 y reemplazar el baseline offline por el reporte neural definitivo.
