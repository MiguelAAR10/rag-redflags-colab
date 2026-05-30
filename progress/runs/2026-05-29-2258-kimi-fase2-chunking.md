# Handoff — 2026-05-29-2258 — fase2-chunking

## CLI usado
kimi

## Objetivo
Implementar chunking comparativo con overlap sobre las 237 unidades documentales del dataset, con gate de tests.

## Archivos tocados
- `packages/rag_core/chunkers.py` — creado desde cero
- `packages/rag_core/tests/test_chunking.py` — gate de Fase 2 (12 tests)
- `data/processed/redflags_chunks.jsonl` — 299 chunks recomendados
- `progress/evidence/fase2-chunking-report.json` — reporte comparativo
- `docs/CAVELOG.md` — entrada de decisión añadida

## Decisiones
- Chunking por límite de palabra (busca último espacio antes del corte) para evitar palabras cortadas.
- Overlap configurado entre chunks consecutivos del mismo padre: los últimos N chars del chunk previo se solapan con el siguiente.
- Configuraciones comparativas: small (512/64), medium (1024/128), large (2048/256).
- Configuración recomendada: medium (1024/128) por equilibrio granularidad/coherencia (16.9% fragmentación vs 54.9% en small).
- Metadata heredada completa: cada chunk conserva family, indicator_code, indicator_name, block_type, page_start/end.

## Comandos ejecutados
```bash
python3 packages/rag_core/chunkers.py
python3 -m pytest packages/rag_core/tests/test_chunking.py -q
bash scripts/verify.sh
bash scripts/handoff.sh "fase2-chunking" kimi
```

## Resultado
✅ **Todos los criterios de aceptación pasaron:**
- `chunk_units` respeta `size` (ningún chunk excede el tamaño) ✓
- Overlap > 0 verificado entre chunks contiguos del mismo padre ✓
- Metadata heredada completa en cada chunk ✓
- Comparación de ≥2 tamaños documentada en reporte ✓
- `pytest packages/rag_core/tests/test_chunking.py -q` → 12 passed ✓
- `bash scripts/verify.sh` → verde (23 passed total: 10 dataset + 12 chunking) ✓

**Métricas comparativas:**
- Small (512/64): 472 chunks, avg 368.8 chars, 130 unidades fragmentadas (54.9%)
- Medium (1024/128): 299 chunks, avg 558.8 chars, 40 unidades fragmentadas (16.9%) ← recomendado
- Large (2048/256): 249 chunks, avg 650.8 chars, 10 unidades fragmentadas (4.2%)

## Evidencia
- `data/processed/redflags_chunks.jsonl`: 299 líneas (configuración medium)
- `progress/evidence/fase2-chunking-report.json`: métricas de las 3 configuraciones
- `packages/rag_core/tests/test_chunking.py`: 12 tests en verde
- `verify.sh`: gate de pytest pasa (23/23)

## Riesgos
- Tamaño 1024/128 elegido heurísticamente; métrica final (Recall@k en Fase 7) puede sugerir ajuste.
- Unidades de metodología (family="metodologia") también se chunkifican; podrían excluirse del índice final si no son relevantes para retrieval.

## Próxima acción exacta
**Fase 3 — Embeddings + FAISS:** crear `packages/rag_core/embeddings.py` (generación con `BAAI/bge-m3` o `intfloat/multilingual-e5-base`) e `indexing.py` (FAISS `IndexFlatIP` baseline). Leer spec + último run en `progress/runs/` antes de implementar.