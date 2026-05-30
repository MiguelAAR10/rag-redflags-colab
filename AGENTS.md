# AGENTS.md

> Contrato común para **todos los CLIs**: Claude Code, Codex y OpenCode lo leen antes de trabajar.
> Manténlo corto (< 180 líneas). La documentación larga vive en `docs/`.

## Proyecto

Sistema **RAG agéntico** en Google Colab usando **Qwen** para analizar un **libro/PDF grande (~500 pp)** sobre *red flags* en contratación pública (guía OCP / OCDS) y emitir **señales de riesgo** fundamentadas sobre un contrato.

Entregable que se califica: **notebook de Colab**. Este repo es el arnés de apoyo (specs, código reutilizable, evals, memoria).

## Regla principal

**No hacer todo en una sola sesión.** Trabajar por **fases pequeñas, verificables y con handoff**. Una actividad por sesión.

## Leer SIEMPRE primero (contexto mínimo)

1. `docs/MEMORY_INDEX.md`  ← el mapa: qué leer según la fase
2. `progress/CURRENT_STATE.md`
3. `progress/NEXT_ACTION.md`
4. `progress/HANDOFF.md`
5. la **spec activa** en `specs/` (hoy: `specs/004-redflags-rag.md`)
6. `docs/CAVELOG.md` (decisiones previas)

## NO cargar completo salvo necesidad real

PDF original · notebooks grandes · `.jsonl` procesados grandes · índices FAISS · outputs de embeddings · logs extensos.
El contexto largo **vive en archivos**, no en el chat. Usa `docs/MEMORY_INDEX.md` para decidir qué abrir.

## Flujo obligatorio por sesión (TCAD + PEV)

1. **Plan** breve (objetivo, archivos, riesgos).
2. **Execute** cambios mínimos y modulares.
3. **Verify**: `bash scripts/verify.sh`.
4. **CAVELOG**: registrar decisión en `docs/CAVELOG.md`.
5. **Handoff**: `bash scripts/handoff.sh` → deja resumen en `progress/runs/`.

Metodología completa en `docs/CAVEMAN.md`. Coordinación multi-CLI en `docs/MULTI_CLI_PROTOCOL.md`. Memoria/contexto en `docs/MEMORY_PROTOCOL.md` (**"si no está en un archivo, no existe"**; arranca con `bash scripts/context-pack.sh`).

## Comandos

```bash
bash scripts/init.sh      # valida estructura (no destructivo)
bash scripts/verify.sh    # quality gates
bash scripts/handoff.sh "fase-xx-titulo"   # crea handoff en progress/runs/
```

## Reglas obligatorias

1. Antes de modificar código, ejecuta `bash scripts/init.sh`. Si falla, no continúes; explica el fallo.
2. Una actividad por sesión. No expandas el scope de la fase.
3. No metas secretos, tokens ni claves en prompts, logs o commits. Usa `.env.example`.
4. No cambies arquitectura global sin crear/actualizar una spec en `specs/`.
5. Todo cambio deja evidencia en `progress/runs/`. Todo cambio relevante actualiza `docs/CAVELOG.md`.
6. No declares éxito sin `bash scripts/verify.sh`. Si no puedes verificar algo, dilo explícitamente.
7. **Lenguaje seguro** (dominio anticorrupción): nunca afirmar corrupción ni ilegalidad. Usar **"señales de riesgo"**, **"red flags potenciales"**, **"posible irregularidad a revisar"** y cerrar con **"requiere revisión humana"**.

## Política RAG

1. Toda respuesta basada en documentos debe tener **citas** (fuente + página/sección).
2. Si el retrieval no encuentra evidencia suficiente → responder **"no hay evidencia suficiente"**.
3. Separar siempre: **respuesta · evidencia · incertidumbre · próximos pasos**.
4. Nunca inventar fuentes. Usar reranking/verificación cuando la respuesta sea crítica.

## Roles (multi-CLI)

- **Claude** → coordina, integra, revisa final, escribe specs/slides/notebook (caro → úsalo poco).
- **Kimi K2 / DeepSeek** → implementan módulos, tests, auditoría técnica.
- **MiniMax / Qwen** → worker barato: docs, reportes, tareas pequeñas. (Qwen además es el LLM obligatorio del RAG.)
- **Humano** → aprueba acciones sensibles e irreversibles.

Workers NO-Claude arrancan leyendo **`docs/START_HERE.md`**. Detalle de roles en `docs/MULTI_CLI_PROTOCOL.md`.
