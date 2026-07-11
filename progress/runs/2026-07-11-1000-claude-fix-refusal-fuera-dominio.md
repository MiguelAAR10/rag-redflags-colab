# Fix — Refusal limpio para consultas fuera de dominio

- **Fecha:** 2026-07-11
- **Rama:** v2
- **Origen:** feedback de revisión — `analyze("What is the capital of France?")`
  no devolvía un refusal claro.

## Diagnóstico (root cause real, no era el goldset)

1. El retrieval (FAISS local Y Qdrant) **siempre devuelve top-k**, sin piso de
   similitud. Para "capital of France", FAISS/E5 local da scores de **0.75**
   (más alto que Qdrant, 0.53) — normal en embeddings, no es bug de Qdrant.
2. El mecanismo de grounding **sí detecta correctamente** `grounding_ratio=0.0`
   y activa `refusal`.
3. Pero `SYSTEM_PROMPT` forzaba el formato de auditoría **sin excepción**, así
   que el LLM (Qwen o Gemini) rellenaba dócilmente "Riesgo: Bajo, no se
   identifican señales" en vez de rehusarse — se lee como veredicto limpio,
   no como refusal.
4. El campo `refusal` existía y era correcto, pero `analyze()` nunca lo usaba
   para sobreescribir `answer` → cualquier caller directo (notebook celda 8.2,
   chat Gradio) veía dos señales contradictorias.
5. **La web (`apps/api`) ya estaba a salvo**: `evidence.critique()` +
   `scoring.score()` ya ignoran el texto del LLM y usan `refusal`/
   `grounding_ratio` como autoridad → `risk.level="Evidencia insuficiente"`
   correctamente, verificado en vivo contra el stack real.
6. El goldset (`data/eval/goldset.jsonl`, 15 ítems, 2 trampas) está bien
   diseñado; no era la causa.

## Fix aplicado (`packages/rag_core/agent.py`)

- `SYSTEM_PROMPT`: nueva regla 0 — corto-circuito explícito para consultas
  fuera de dominio (frase exacta de refusal, sin formato de auditoría).
- `analyze()`: `answer` se sobreescribe **deterministamente** con el mensaje
  de refusal cuando `grounding_ratio` está bajo el umbral, sin depender de
  que el LLM obedezca el prompt. Texto crudo del modelo queda en
  `raw_answer` (nueva clave) para diagnóstico/auditoría.

## Validación

- `bash scripts/verify.sh` → **169 passed, 6 skipped** (sin regresiones;
  ningún test comparaba `answer` literal contra el generate_fn).
- Smoke real contra Qdrant+Gemini: "capital of France" → `answer` limpio de
  refusal; `raw_answer` confirma que el LLM sí obedeció la regla 0.
- TDR real (oferente único) sigue generando análisis con señales — el fix
  es específico a refusal, no afecta casos grounded.

## Hallazgo colateral (NO es este fix): grounding cross-lingüe

Al validar el TDR real con `grounding_method="lexical"`, salió refusal
también — porque la respuesta de Gemini está en español y el corpus en
inglés (solapamiento léxico ≈ 0). Es el mismo bug ya anotado en el handoff
de F17b. Registrado como tarea **V1.2** — no se toca aquí, es trabajo de F18
(grounding por embeddings multilingües, ya integrado con Gemini).

## Sincronización

Copiado y pusheado a `MiguelAAR10/rag-redflags-colab` (commit `bf915d2`) —
el notebook académico importa este mismo `agent.py`, así que sus celdas de
demo (7.1, 8.2, 12.0) y RAGAS (9.2) ya reflejan el fix antes del Run all.

## Próximos pasos
1. Usuario: correr **Run all** en Colab T4 (V1.1, ya con el fix incluido).
2. F18: interfaz VectorStore + grounding por embeddings Gemini (incluye V1.2).
