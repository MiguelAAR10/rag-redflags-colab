# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**V1.1 (cierre) — Correr «Run all» en Colab T4 y guardar el `ragas-report.json` definitivo.**

- **Branch:** `v2` (repo Colab `MiguelAAR10/rag-redflags-colab` en `072198c`)
- **Owner:** Humano (requiere GPU de Colab; el agente no tiene)
- **Base:** F17a/F17b/F18 completas. El repo Colab ya incluye PDF, datos
  procesados, índice FAISS, `ragas_metrics.py`, el notebook con los fixes de
  Run all y el `agent.py` con refusal fuera-de-dominio corregido.

## Pasos exactos

1. Abrir `notebooks/redflags_rag_colab.ipynb` en Google Colab.
2. Runtime → *Change runtime type* → **GPU (T4)**.
3. (Opcional) Colab Secrets: `HF_TOKEN`.
4. **Runtime → Run all.** No debe pedir NINGUNA intervención manual.
5. Al terminar: descargar `progress/evidence/ragas-report.json` generado y
   copiarlo al repo principal (reemplaza el baseline offline).
6. Registrar en `docs/CAVELOG.md` + run en `progress/runs/`: duración total,
   celdas problemáticas si las hubo, y los 3 promedios RAGAS.

## Criterios de aceptación

- [ ] Run all completo sin errores ni interacción manual.
- [ ] `ragas-report.json` con `n=15`, `traps=2`, promedios en [0,1].
- [ ] Las 2 trampas dan métricas ≈ 0 (refusal correcto).
- [ ] Celda 8.2 (fuera de dominio) muestra el refusal limpio nuevo
      ("No puedo responder: ... fuera del dominio ...").

## NO hacer

- No editar celdas durante la corrida (invalida el "sin intervención").
- No usar el `.env` del repo principal en Colab (credenciales V2 no
  aplican; el notebook es autosuficiente con E5+FAISS+Qwen).

## Después de esto (F19, agente)

Intake multi-formato (PDF/DOCX/TXT) + reindexación inteligente por chunk
(diff de hashes, upsert incremental a `subject_docs` en Qdrant,
`change_events`). Spec 007 §F19. Para F21 el usuario debe crear la base
Neon (free) y pegar `DATABASE_URL` en `.env`.
