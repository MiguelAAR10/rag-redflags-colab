# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**Auditar el notebook y pipeline contra las indicaciones finales UNI/RAGAS antes de implementar cambios.**

- **Branch:** `feature/final-evaluation-ragas`
- **Owner:** DANTE-OS / reviewer técnico
- **Input principal:** `docs/proyecto-final-indicaciones/README.md` y `docs/proyecto-final-indicaciones/CHECKLIST.md`

## Objetivo

Comparar el estado actual del proyecto contra las indicaciones finales del curso y producir un plan mínimo de mejora para cumplir especialmente:

- notebook `Run all` en Colab;
- ficha técnica como primera celda;
- tabla de trazabilidad requisito/técnica -> celda;
- set de evaluación de 10 a 15 preguntas con al menos 2 trampas;
- métricas RAGAS: faithfulness, answer relevance y context relevance;
- reporte de puntajes y comentario de resultados;
- slides con resultados RAGAS y demo.

## Fuentes a leer

1. `docs/proyecto-final-indicaciones/README.md`
2. `docs/proyecto-final-indicaciones/CHECKLIST.md`
3. `notebooks/redflags_rag_colab.ipynb` solo inspección estructural, no cargar outputs pesados.
4. `packages/evals/metrics.py`
5. `data/eval/goldset.jsonl` por muestra, no completo si no hace falta.
6. `docs/PROYECTO.md`
7. `progress/evidence/fase7-eval-report.json`
8. `docs/CAVELOG.md`

## Criterios de aceptación

- [ ] Matriz requisito -> estado actual -> brecha -> archivo afectado.
- [ ] Identificar exactamente qué celdas del notebook deben agregarse o modificarse.
- [ ] Definir si se usará librería `ragas` o implementación local compatible con el paper.
- [ ] No implementar todavía cambios grandes sin plan.
- [ ] Mantener lenguaje seguro del dominio anticorrupción.

## NO hacer

- No modificar pipeline hasta cerrar auditoría.
- No cambiar el corpus ni regenerar índices.
- No pegar tokens ni credenciales.
