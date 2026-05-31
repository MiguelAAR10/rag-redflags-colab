# Handoff — 2026-05-30-2102 — fase11-doc-slides

## CLI usado
DeepSeek (OpenCode)

## Objetivo
Crear `docs/PROYECTO.md`: documento de investigación detallado, base para los 8 slides, con 16 secciones, números reales de las fases 1–7, mermaid, tablas, lenguaje seguro.

## Archivos tocados
- `docs/PROYECTO.md` (nuevo, ~680 líneas, 16 secciones)
- `docs/assets/` (directorio creado para logo-lugarholder)
- `docs/CAVELOG.md` (actualizado)

## Decisiones
- Números reales extraídos de `progress/evidence/fase{1..7}-report.json` (no inventados).
- 2 diagramas mermaid: arquitectura de sistema y secuencia del pipeline.
- Secciones: portada, resumen, problema, fundamentos RAG, dataset (237 unidades, 299 chunks, 69 indicadores), arquitectura, técnicas avanzadas (8 técnicas tabuladas), pipeline paso a paso, decisiones técnicas (chunk 1024/128, k=20→5, Flat vs HNSW, reranker graceful), evaluación (Recall@k, Precision@k, grounding ratio 0.305, comparación FAISS/hybrid/rerank, ejemplo bueno R@5=1.0 y malo R@5=0.5), minimización alucinaciones (6 mecanismos), demo Gradio, ética, limitaciones + trabajo futuro (GraphRAG, sub-índices, Qwen 3B vs 7B, BLEU/ROUGE), referencias (9 citas), anexo tabla 8 slides.
- Lenguaje seguro en todo el documento: "señal de riesgo", no sospechas/fraude, "requiere revisión humana".
- Placeholders (`_<completar>_`) para Universidad, Docente, Fecha y logo.

## Comandos ejecutados
```bash
bash scripts/init.sh
bash scripts/verify.sh
grep -c "^## " docs/PROYECTO.md
bash scripts/handoff.sh "fase11-doc-slides" deepseek
```

## Resultado
- `docs/PROYECTO.md` completo: 15 secciones `## ` + portada = 16. Cubre todos los puntos de la rúbrica.
- `verify.sh` verde: **104 passed, 6 skipped**, exit=0.

## Evidencia
- `docs/PROYECTO.md` ~680 líneas, 2 mermaid, 8 tablas, 9 referencias, datos de todas las fases.
- `verify.sh` → 104 passed, 6 skipped, exit=0.

## Riesgos
- Completar `_<completar>_` con datos reales de Universidad, Docente y Fecha antes de entregar.
- Logo universidad en `docs/assets/logo-universidad.png`.

## Próxima acción exacta
Generación del notebook final de Colab (F8) y slides de presentación.
