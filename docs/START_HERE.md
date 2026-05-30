# START_HERE — Arranque universal para cualquier worker

> Para **Kimi K2, Qwen, MiniMax, DeepSeek** (y cualquier modelo que NO sea Claude).
> El humano solo dice una frase; la actividad pendiente **siempre** está en `progress/NEXT_ACTION.md`.

## Frase que el humano pega (una sola vez por sesión)

```
Lee docs/START_HERE.md y ejecuta la actividad pendiente. No hagas nada más.
```

(Si tu CLI tiene acceso a archivos —p.ej. OpenCode— léelos directo. Si es chat sin archivos, pídele al humano la salida de `bash scripts/context-pack.sh`.)

## Pasos que TÚ (worker) sigues

1. **Carga solo el contexto mínimo** (nada más): `AGENTS.md`, `docs/MEMORY_INDEX.md`, `progress/CURRENT_STATE.md`, `progress/NEXT_ACTION.md`, `progress/HANDOFF.md`, la spec activa (`specs/004-redflags-rag.md`). Atajo: `bash scripts/context-pack.sh`.
2. **Haz EXACTAMENTE la actividad** descrita en `progress/NEXT_ACTION.md`. Una sola. No expandas el alcance.
3. **Reglas (obligatorias):**
   - No cargues al chat: PDF, `.jsonl` grandes, índices FAISS, notebooks, logs. Trabaja **por código** y guarda reportes en `progress/evidence/`.
   - **Write-through:** escribe resultados a archivos *en el momento* ("si no está en un archivo, no existe").
   - **Lenguaje seguro:** "señales de riesgo", "red flags potenciales", "requiere revisión humana". Nunca afirmar corrupción.
   - No toques fases futuras. No cambies arquitectura sin spec.
4. **Verifica:** `bash scripts/verify.sh` (debe terminar en verde).
5. **Deja handoff:** `bash scripts/handoff.sh "<fase>" <tu-modelo>` (ej. `kimi`, `deepseek`, `qwen`, `minimax`) y **completa** el archivo creado en `progress/runs/` (resultado, evidencia, riesgos, próxima acción).
6. **No declares éxito sin evidencia.** Si algo no se puede verificar, dilo. Si trabajas en worktree/rama, no toques `main`; lista los archivos tocados.

## Qué deja listo para Claude
Claude (coordinador) integra **solo** cuando existe tu handoff y `verify.sh` pasa. Tú no integras a main; Claude revisa, actualiza `CURRENT_STATE`/`NEXT_ACTION`/`CAVELOG` y define la siguiente actividad.

## Ahorro de tokens (clave del proyecto)
- Claude es caro → se usa solo para coordinar/integrar/revisar y razonamiento difícil.
- Los workers (Kimi/Qwen/MiniMax/DeepSeek) hacen el trabajo pesado y repetitivo.
- Todo va por **archivos**, no por chats largos: nadie re-explica el proyecto; se lee `START_HERE` + `NEXT_ACTION`.
- Para navegar el repo sin leerlo entero: `progress/context-graph.json` (mapa) y `docs/MEMORY_INDEX.md`.
