# Handoff — 2026-05-30-2140 — fase12-auditor-prompt-4bit-minimax

## CLI usado

Claude

## Objetivo

Mejorar la salida final del RAG para que parezca un análisis de auditor senior, activar carga opcional de Qwen en 4-bit para Colab T4 y dejar MiniMax como segunda opinión opcional sin reemplazar a Qwen.

## Archivos tocados

- `packages/rag_core/agent.py`
- `packages/rag_core/tests/test_model_cache.py`
- `packages/rag_core/tests/test_grounding.py`
- `notebooks/redflags_rag_colab.ipynb`
- `docs/CAVELOG.md`
- `tasks/queue.json`

## Decisiones

- `SYSTEM_PROMPT` pasa a formato de auditor senior estructurado: evaluación preliminar, nivel de riesgo, señales con evidencia, qué faltaría validar y conclusión.
- Se conserva lenguaje seguro obligatorio: no afirmar corrupción, usar señales de riesgo/red flags potenciales/posible irregularidad y cerrar con revisión humana.
- `_build_prompt` ya no duplica el system prompt; el system viaja como rol system del chat template.
- `_load_qwen` soporta `RAG_QWEN_4BIT=1` con `BitsAndBytesConfig` NF4/double quant/fp16 y fallback limpio.
- MiniMax queda como segunda opinión opcional mediante cliente OpenAI-compatible; Qwen sigue siendo el LLM principal obligatorio.

## Comandos ejecutados

```bash
bash scripts/init.sh
python -m pytest packages/rag_core/tests/test_model_cache.py -q
python -m pytest packages/rag_core/tests/test_grounding.py -q
python -m pytest packages/rag_core/tests/test_notebook_smoke.py -q
bash scripts/verify.sh
```

## Resultado

F12 quedó implementada: el sistema genera con prompt de auditor estructurado, soporta Qwen 4-bit opcional para Colab T4 y mantiene MiniMax como segunda opinión opt-in. El pipeline principal sigue siendo Qwen + grounding + citas.

## Evidencia

- `test_model_cache`: 5/5 PASS, incluyendo check estático de 4-bit.
- `test_grounding`: 15/15 PASS, incluyendo lenguaje seguro en prompt.
- `test_notebook_smoke`: 7/7 PASS.
- `bash scripts/verify.sh`: 105 passed, 6 skipped según `docs/CAVELOG.md`.

## Riesgos

- Falta ejecutar el notebook completo en Colab T4 con `RAG_QWEN_4BIT=1`.
- Las métricas locales de grounding/eval usan fallback o muestras; la evidencia final debe venir de Colab con Qwen real.
- MiniMax es opcional y no sustituye el requisito de Qwen.

## Próxima acción exacta

Ejecutar `notebooks/redflags_rag_colab.ipynb` en Google Colab T4 con `RAG_QWEN_4BIT=1`, `HF_TOKEN`, `rank_bm25`, Qwen real y guardar evidencia final en `progress/evidence/`.
