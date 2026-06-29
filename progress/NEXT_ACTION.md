# NEXT_ACTION — La siguiente tarea exacta (una sola)

## Acción

**Validación final en Google Colab T4 del notebook `notebooks/redflags_rag_colab.ipynb` con Qwen real.**

- **Owner:** Humano en Colab · **Reviewer:** Claude/DANTE-OS
- **No es tarea de código local:** no tocar `packages/`, `notebooks/`, `data/index/` ni `.env` desde el repo local.

## Objetivo

Ejecutar el notebook completo en un runtime limpio de **Google Colab T4**, con `RAG_QWEN_4BIT=1`, `HF_TOKEN`, `rank_bm25`, Qwen2.5-3B-Instruct real y el chat Gradio, para obtener evidencia final de que el entregable corre fuera del entorno local.

## Contexto confirmado

- F1.1-F7 ✅ pipeline RAG implementado y testeado localmente.
- F8 ✅ notebook autorado y smoke gate local PASS; **pendiente ejecución real en Colab T4**.
- F9 ✅ validación LangChain integrada.
- F10 ✅ chat Gradio + MiniMax opcional integrado.
- F11 ✅ `docs/PROYECTO.md` creado.
- F12 ✅ prompt auditor senior + Qwen 4-bit opcional + MiniMax segunda opinión.
- `progress/agent_io/` ✅ creado para prompts/respuestas trazables de agentes externos.

## Pasos en Colab

1. Abrir `notebooks/redflags_rag_colab.ipynb` en Google Colab.
2. Seleccionar runtime GPU T4.
3. Configurar secret/env `HF_TOKEN`.
4. Activar `RAG_QWEN_4BIT=1` según las celdas del notebook.
5. Asegurar instalación de `rank_bm25` para retrieval híbrido real.
6. Ejecutar `Run all`.
7. Probar al menos un caso con señales de riesgo y un caso limpio/refusal.
8. Ejecutar evaluación completa del gold set si el tiempo de Colab lo permite.

## Evidencia esperada

Guardar un resumen en `progress/evidence/` o traer el output para que Claude/DANTE-OS lo registre:

- runtime usado: T4 / Python / GPU visible;
- instalación de dependencias clave;
- Qwen cargado real o fallback usado, con causa;
- `rank_bm25` activo o fallback documentado;
- resultado de `analyze()` con lenguaje seguro;
- grounding ratio con Qwen real si se pudo ejecutar;
- resultados del gold set completo o explicación honesta si se ejecutó muestra;
- screenshot/log mínimo del chat Gradio funcionando.

## Criterios de aceptación

- [ ] Notebook ejecuta de inicio a fin en Colab T4 o deja fallo reproducible con celda exacta.
- [ ] Qwen real carga con 4-bit o se documenta el bloqueo concreto.
- [ ] Retrieval híbrido usa BM25 real (`rank_bm25`) o se documenta fallback.
- [ ] Salida mantiene lenguaje seguro: señales de riesgo, no corrupción, revisión humana.
- [ ] Evidencia queda registrada en `progress/evidence/` y `docs/CAVELOG.md`.
- [ ] `bash scripts/verify.sh` sigue verde localmente después de registrar evidencia.

## NO hacer

- No modificar pipeline local mientras se valida Colab.
- No reescribir notebook salvo que Colab revele un fallo concreto y reproducible.
- No afirmar corrupción/ilegalidad; mantener lenguaje seguro.
- No pegar tokens ni secretos en logs, prompts o docs.
