# Handoff — 2026-06-29-1354 — fase13-ragas-metrics

## CLI usado

OpenCode

## Objetivo

Implementar métricas RAGAS locales deterministas (faithfulness, answer_relevance, context_relevance, evaluate_ragas) con TDD, sin APIs externas ni dependencias pesadas, protegidas las superficies sensibles (notebook, goldset, data/processed, data/index, .env).

## Archivos tocados

- `packages/evals/ragas_metrics.py` (nuevo)
- `packages/rag_core/tests/test_ragas_metrics.py` (nuevo)
- `docs/CAVELOG.md` (entrada F13)
- `progress/runs/2026-06-29-1354-opencode-fase13-ragas-metrics.md` (este handoff)

## Decisiones

- Aproximación **léxica local** (sin LLM ni embeddings): cada métrica es una fracción de tokens informativos compartidos, determinista, robusta a `None`/vacíos.
- `faithfulness` usa umbral `0.25` alineado con `verifier.DEFAULT_GROUNDING_THRESHOLD` (coherencia con el grounding ya implementado en F6).
- `answer_relevance` devuelve `0.0` ante refusal seguro (marcadores `"no hay evidencia suficiente"` / `"insufficient evidence"` / `"requires human review"`) para reflejar coherencia con la política de lenguaje seguro del proyecto.
- Cero impacto sobre archivos protegidos (no se tocó `notebooks/`, `data/eval/goldset.jsonl`, `data/processed/*`, `data/index/*`, `.env`).
- 37 tests cubren: rango `[0,1]`, vacíos, refusal, pregunta trampa, determinismo, casos perfectos/opuestos/parciales, y la agregación de `evaluate_ragas`.

## Comandos ejecutados

```bash
python3 -m pytest packages/rag_core/tests/test_ragas_metrics.py -q
bash scripts/verify.sh
bash scripts/handoff.sh "fase13-ragas-metrics" opencode
```

## Resultado

- 4 funciones públicas implementadas en `packages/evals/ragas_metrics.py` con las firmas exactas exigidas por `progress/NEXT_ACTION.md`.
- Gate `test_ragas_metrics.py` con 37 tests, todos verdes.
- `verify.sh` en verde (143 passed / 6 skipped / exit 0), `validate-harness` OK.

## Evidencia

- `python3 -m pytest packages/rag_core/tests/test_ragas_metrics.py -q` → **37 passed in 0.06s**.
- `bash scripts/verify.sh` → **143 passed, 6 skipped in 47.25s**, exit 0.
- Diff de tests: 0 → 37 nuevos en Fase 13 (106 → 143 totales).
- CAVELOG: entrada `2026-06-29 — Fase 13: Métricas RAGAS locales deterministas (DeepSeek)`.

## Riesgos

- Las métricas son **aproximaciones léxicas locales** de RAGAS oficial (que usa LLM/embeddings semánticos). Aceptables como "RAGAS local para Colab" según el prompt, pero conviene etiquetarlas como tales en notebook/slides para no prometer equivalencia total con la librería.
- `faithfulness` puede subestimar soporte cuando hay paráfrasis sin tokens compartidos; si llega a ser un problema, considerar exponer `method="embedding"` reutilizando `packages.rag_core.embeddings`.
- No se integró aún al notebook `Run all` ni al gold set: queda pendiente para la próxima fase.

## Próxima acción exacta

Cablear las métricas RAGAS a la sección 9 del notebook `notebooks/redflags_rag_colab.ipynb` (Evaluación), ejecutarlas sobre el gold set real (`data/eval/goldset.jsonl`) y reportar `mean_faithfulness / mean_answer_relevance / mean_context_relevance` con al menos 2 preguntas trampa explícitas, sin tocar `data/processed/*`, `data/index/*` ni `.env`.