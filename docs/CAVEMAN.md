# CAVEMAN — Metodología de trabajo del arnés

Acrónimo de los pilares que mantienen el proyecto bajo control:
**C**ontexto · **A**ctividad única · **V**erificación · **E**videncia · **M**emoria · **A**gentes · **N**o-sobrecarga.

El nombre recuerda la idea base del *harness engineering*: **el arnés vive en archivos** (contexto + herramientas + memoria + verificación), no en una conversación gigante.

---

## 1. TCAD — cómo pensar cada tarea

- **T — Traducción**: convertir la intención en objetivo + restricciones + criterios de aceptación.
- **C — Contexto**: leer SOLO lo que indica `docs/MEMORY_INDEX.md` para la fase.
- **A — Análisis**: proponer plan, riesgos, archivos afectados y pruebas.
- **D — Desarrollo/Documentación**: implementar mínimo, verificar, documentar evidencia.

## 2. PEV — el ciclo de ejecución

- **Plan** → breve, antes de editar.
- **Execute** → cambios mínimos, modulares, testeables. Una fase a la vez.
- **Verify** → `bash scripts/verify.sh`. Sin verde, no hay éxito.

## 3. CAVELOG — bitácora de decisiones

Toda decisión relevante (stack, dataset, chunk size, modelo, métrica) se registra en `docs/CAVELOG.md` con: **fecha · decisión · evidencia · riesgos · próximos pasos**. Es append-only; no reescribir historia.

## 4. Handoff — memoria entre sesiones

Al cerrar una sesión: `bash scripts/handoff.sh "faseXX-titulo"`. Genera un archivo en `progress/runs/` (plantilla `progress/runs/_TEMPLATE.md`) y actualiza `progress/HANDOFF.md`. Sin handoff, la siguiente sesión arranca a ciegas.

## 5. Subagentes — aislar contexto

El coordinador **no implementa todo**. Delega tareas pequeñas a subagentes/CLIs especializados (ver `docs/MULTI_CLI_PROTOCOL.md`). Cada subagente escribe su resultado en `progress/`, no en el chat del coordinador.

## 6. Reglas anti-context-pollution

- Una actividad por sesión.
- No abrir PDF/JSONL/índices completos.
- No mezclar fases (dataset ≠ chunking ≠ notebook).
- El contexto largo se referencia por ruta, no se pega.
- Si la ventana se llena: cerrar con handoff y abrir sesión nueva.

## 7. Definición de "hecho" (Definition of Done) por fase

Una fase está hecha cuando:
1. Cumple los criterios de aceptación de su tarea en `tasks/backlog.json`.
2. `bash scripts/verify.sh` pasa.
3. Hay handoff en `progress/runs/`.
4. `docs/CAVELOG.md` y `progress/CURRENT_STATE.md`/`NEXT_ACTION.md` están actualizados.
5. Un reviewer (Claude o Codex) revisó el trabajo.

## 8. Lenguaje seguro (dominio anticorrupción)

El sistema **no acusa**. Habla de **señales de riesgo / red flags potenciales / posible irregularidad a revisar**, y siempre cierra con **"requiere revisión humana"**. Regla de oro: *el agente lee y propone; el humano decide y aprueba lo irreversible.*
