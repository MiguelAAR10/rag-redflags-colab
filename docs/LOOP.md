# LOOP — El ciclo humano (a quién le hablas en cada paso)

**Modelo mental:** Claude = **casa / integrador**. Los workers (Kimi, DeepSeek, MiniMax, Qwen) = **brazos**. **Siempre pasas por casa entre pasos.**

```
        ┌─────────────── CASA (Claude, aquí) ───────────────┐
        │  revisa · corre el gate · integra · avanza la cola │
        └───────▲───────────────────────────────┬───────────┘
                │ "ya lo hizo, revisa"           │ "el siguiente es <CLI>"
                │                                 ▼
        ┌───────┴─────────┐   pega:        ┌──────────────────┐
        │  TÚ (humano)    │ ─────────────► │  Worker (Kimi/…)  │
        └─────────────────┘  "Lee docs/    └──────────────────┘
                              START_HERE.md      produce + gate + handoff
                              y ejecuta lo
                              pendiente"
```

## Los 4 pasos, siempre iguales

1. **Vas al worker dueño de la tarea.** Abres su CLI (Kimi/DeepSeek/MiniMax/Qwen) y pegas SIEMPRE lo mismo:
   `Lee docs/START_HERE.md y ejecuta la actividad pendiente. No hagas nada más.`
2. **El worker trabaja:** produce el código/datos → corre su `test_cmd` (el gate) → deja handoff en `progress/runs/`.
3. **Vuelves a CASA (aquí, Claude)** y dices: **"ya lo hizo, revisa"**. Claude corre el gate, integra, marca `done` y avanza la cola.
4. **Claude te dice quién sigue.** Si el owner es un worker → vas a ese CLI (paso 1). Si el owner es `claude` → se hace aquí mismo.

## ¿Cómo sé quién sigue sin preguntar?
```bash
bash scripts/next-task.sh           # la próxima tarea READY (cualquier CLI)
bash scripts/next-task.sh kimi      # la próxima READY para Kimi
```
O simplemente Claude te lo dice al integrar.

## Regla de una línea
**Trabajo pesado → workers. Revisión, integración y decisiones → Claude (casa).**
Nunca dejas que un worker integre a `main`; nunca encadenas dos workers sin pasar por casa.
