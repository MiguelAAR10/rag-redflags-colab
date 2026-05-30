# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**Fase 8b — Correr el notebook en Google Colab (T4) y validar end-to-end.** (Tarea del **humano**.)

- Notebook listo: `notebooks/redflags_rag_colab.ipynb` (10 secciones, smoke gate 5/5 PASS).
- Sigue los pasos de **`docs/COLAB.md`**: push a GitHub → editar `REPO_URL` → Colab GPU T4 → secret `HF_TOKEN` → subir PDF → Run all.

## Criterios de aceptación (en Colab)

- [ ] El notebook corre de principio a fin sin errores en T4.
- [ ] La demo (celda 10.1) muestra señales de riesgo + citas + "requiere revisión humana" para el contrato con riesgo, y no inventa para el limpio.
- [ ] La evaluación (9.1) imprime Recall@k / Precision@k por método.

## Después

- **Slides** (8 secciones, 7 min) — aparte, con capturas del notebook (ver `docs/COLAB.md` §3). Avísame si quieres que arme el guion/los genere.
- Si algo falla en Colab, pégame el error y lo arreglamos (vuelve a "casa" → Claude).

## Verificación local (ya hecha)

`bash scripts/verify.sh` verde + `test_notebook_smoke.py` 5/5. La validación real es la corrida en Colab.
