# Handoff — 2026-05-29-2240 — fase1-1-dataset-rework

## CLI usado
kimi-k2

## Objetivo
Rework del dataset Fase 1 para corregir los 3 defectos bloqueantes del review de Claude: indicator_name vacío, family sin clasificar, unidades = páginas crudas.

## Archivos tocados
- `packages/rag_core/loaders.py` — reescrito completamente (extracción lógica robusta)
- `data/processed/redflags_units.jsonl` — regenerado con 237 unidades limpias
- `progress/evidence/fase1-exploration-report.json` — actualizado con métricas de calidad
- `docs/CAVELOG.md` — entrada de decisión añadida

## Decisiones
- Extracción de título: usar spans con font≥16, unir líneas consecutivas del mismo tamaño, limpiar Rxxx y headers conocidos.
- Inferencia de stage: heurística por keywords del título (planning/tender/award/contract).
- Family: mapeo stage→family obligatorio (planning→planeacion, tender→competencia/licitacion, award→adjudicacion, contract→ejecucion/contrato).
- Unidades lógicas: dividir indicadores en bloques `core` (Definition+Why+Unit+Type+Stage+Source), `formula` (Methodology+Data fields+OCDS), `example` (Example). Metodología: 1 unidad por encabezado (`section`).
- `parent_doc_id`: core es padre; formula/example apuntan a él.
- Texto limpio: remove standalone page numbers, normalize whitespace.

## Comandos ejecutados
```bash
# PyMuPDF ya instalado de Fase 1 anterior
python3 packages/rag_core/loaders.py
bash scripts/verify.sh
bash scripts/handoff.sh "fase1-1-dataset-rework" "kimi-k2"
```

## Resultado
✅ **Todos los criterios de aceptación pasaron:**
- `len(unidades) = 237 >= 100` ✓
- `indicator_name` no nulo en 100% (195/195) >= 95% ✓
- `family="unknown"` = 0; las 4 familias presentes: planeacion, competencia/licitacion, adjudicacion, ejecucion/contrato ✓
- `text` limpio sin números de página ni etiquetas de layout ✓
- reporte actualizado en `progress/evidence/fase1-exploration-report.json` ✓
- `bash scripts/verify.sh` verde ✓

**Distribución de unidades:**
- Indicator pages: 73 → 195 unidades (102 core + 81 formula + 12 example)
- Methodology pages: 26 → 42 unidades section
- Family: planeacion=18, competencia/licitacion=80, adjudicacion=50, ejecucion/contrato=47, metodologia=42
- Stage: planning=18, tender=80, award=50, contract=47

## Evidencia
- `data/processed/redflags_units.jsonl`: 237 líneas JSON válidas
- `progress/evidence/fase1-exploration-report.json`: conteos, distribuciones, sample units
- `verify.sh`: validate-harness OK, compileall OK

## Riesgos
- 12 unidades `example` (escasas): muchos indicadores del PDF no tienen sección Example.
- Stage inferido por heurística de keywords del título (no hay stage explícito en el layout del PDF; el PDF lista todos los stages posibles como opciones en un bloque tipo tabla).
- Código R021 en p.44 tiene título ambiguo que requirió limpieza manual en la extracción.

## Próxima acción exacta
**Fase 2 — Chunking comparativo:** crear `packages/rag_core/chunkers.py` con chunking comparativo (≥2 tamaños + overlap), analizar tradeoff, guardar en `data/processed/`. Leer spec + último run en `progress/runs/` antes de implementar.