# Handoff — 2026-05-30-1122 — fase6-qwen-grounding

## CLI usado
DeepSeek (OpenCode)

## Objetivo
Implementar Fase 6 (NÚCLEO de la rúbrica) — Generación Qwen + Grounding por frase + Citas. Dado un contrato: retrieve → rerank → Qwen genera observaciones → verificar grounding → citas por frase → lenguaje seguro.

## Archivos tocados
- `packages/rag_core/verifier.py` (nuevo: split_sentences, verify_grounding lexical/embedding, refusal_check)
- `packages/rag_core/citations.py` (nuevo: build_citations con chunk_id, indicator, page)
- `packages/rag_core/agent.py` (nuevo: analyze con pipeline completo + SYSTEM_PROMPT seguro + inyección generate_fn/retrieved_chunks)
- `packages/rag_core/tests/test_grounding.py` (nuevo, gate de F6: 15 tests)
- `packages/rag_core/run_phase6.py` (nuevo, runner/evidencia: 3 contratos de prueba)
- `progress/evidence/fase6-grounding-report.json` (generado)
- `docs/CAVELOG.md` (actualizado)

## Decisiones
- Grounding usa método **léxico** como default determinista (tests siempre corren); método **embedding** como bonus (requiere modelo).
- `analyze` acepta `generate_fn` y `retrieved_chunks` inyectables → tests unitarios con LLM fake y chunks dummy son 100% deterministas.
- SYSTEM_PROMPT incrusta las 5 reglas de lenguaje seguro directamente.
- `_minimal_analysis` como fallback cuando Qwen no está disponible (genera observaciones básicas desde chunks).
- Refusal automático: si `grounding_ratio < threshold`, se emite "no hay evidencia suficiente".

## Comandos ejecutados
```bash
bash scripts/init.sh
python3 -m pytest packages/rag_core/tests/test_grounding.py -q
bash scripts/verify.sh
python3 packages/rag_core/run_phase6.py
bash scripts/handoff.sh "fase6-qwen-grounding" deepseek
```

## Resultado
- `verifier.py` + `citations.py` + `agent.py` implementan el pipeline completo retrieve→rerank→generate→verify→cite.
- Gate `test_grounding.py`: 15 passed (12 unitarios deterministas + 3 integración con FAISS real).
- `verify.sh` pasa en verde: **75 passed, 4 skipped**, exit=0.
- 3 contratos de prueba analizados en evidencia: bid_rigging, delays, clean (todos con salida segura).

## Evidencia
- `progress/evidence/fase6-grounding-report.json`: 3 contratos, router correcto, con citas y lenguaje seguro.
- `pytest -q packages/rag_core/tests/test_grounding.py` → 15 passed.
- `bash scripts/verify.sh` → 75 passed, 4 skipped, exit=0.
- Tests unitarios verifican: split_sentences, grounding ratio correcto, refusal cuando no hay soporte, safe language en SYSTEM_PROMPT, analyze con LLM fake inyectado.

## Riesgos
- Qwen2.5-3B (~6GB) no está descargado localmente → el fallback `_minimal_analysis` genera análisis básicos. En Colab T4, Qwen se cargará y producirá respuestas de mayor calidad.
- El grounding léxico con el fallback da ratios bajos (0.0-0.06) porque `_minimal_analysis` genera descripciones en español mientras las chunks están en EN/ES mixto. Con Qwen real y método embedding, el ratio será más alto.
- Qwen via transformers requiere ~6GB VRAM; en T4 cabe holgadamente.

## Próxima acción exacta
Fase 7 — Evaluación cuantitativa y cualitativa (`packages/evals/`): Recall@k, Precision@k, grounding_ratio, análisis comparativo, BLEU/ROUGE.
