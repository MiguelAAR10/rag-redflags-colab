# Spec 004 — RAG Agéntico de Red Flags en Contratación Pública

Estado: **ACTIVA** · Reemplaza el caso de uso genérico de `specs/001` para este proyecto.

## 1. Objetivo

Construir un RAG agéntico en Google Colab que, dado **un contrato/licitación**, recupere los indicadores de riesgo relevantes de una guía internacional de contratación pública y emita **señales de riesgo fundamentadas** (red flags potenciales), citando la guía y el dato del contrato, para apoyar **revisión humana**.

## 2. Dataset principal (decisión confirmada con la docente)

- **Fuente:** libro/PDF grande (~500 pp) de la *Open Contracting Partnership* — *Red Flags for Integrity*, mapeado a OCDS. El usuario lo coloca en `data/raw/`.
- **Un PDF/libro grande cuenta como dataset válido** por su volumen; **no** se fuerzan 100 procesos OCDS.
- **Definición operativa de "documento" = unidad documental lógica** extraída del libro, **no** un chunk arbitrario.

```
PDF (~500 pp) → 100+ UNIDADES DOCUMENTALES LÓGICAS → CHUNKS (con overlap)
```

- **Metadata obligatoria por unidad:** `doc_id, source_file, page_start, page_end, section, family, indicator_name (si aplica), hash`.
- **Familias de red flags:** planeación · competencia/licitación · adjudicación · ejecución/contrato.
- **Contratos externos (OCDS/sintéticos): solo casos de prueba/demo** para analizar; **no se indexan**.
- **Dificultades a documentar:** ~500 pp con tablas y fórmulas, layout/OCR, fórmulas en prosa, deduplicación, bilingüe EN/ES.

## 3. Pipeline requerido

```
CONTRATO → [1] extracción estructurada (Qwen) → [2] router de familias →
[3] retrieval híbrido (BM25 + FAISS) top-20 → [4] reranker cross-encoder → top-5 →
[5] Qwen genera observaciones con citas → [6] grounding/verifier (citation-per-sentence) →
[7] reporte: señales de riesgo + severidad + citas + "requiere revisión humana"
```

## 4. Restricciones técnicas (de la rúbrica)

- **LLM obligatorio: Qwen** → `Qwen2.5-3B-Instruct`.
- **Vector store obligatorio: FAISS** (`IndexFlatIP` baseline; HNSW como bonus).
- **Embeddings** pre-entrenados multilingües (`BAAI/bge-m3` o `intfloat/multilingual-e5-base`), justificados.
- **Chunking comparativo** (≥2 tamaños + overlap) con análisis del tradeoff.
- **Grounding ratio** (proporción de frases respaldadas).
- **Evaluación**: Recall@k / Precision@k + grounding ratio + análisis cualitativo.
- Debe **correr en Colab T4**.

## 5. Bonus objetivo

HNSW · Hybrid BM25+FAISS · cross-encoder reranker · citation-per-sentence · (opcional) 3B vs 7B · BLEU/ROUGE.

## 6. Criterios de aceptación

- El corpus produce **≥100 unidades documentales** con metadata completa.
- Para un contrato de prueba con patrones de riesgo, el sistema **recupera los indicadores correctos** y **cita** guía + dato del contrato.
- Para un contrato limpio, **no inventa** red flags (refusal / baja severidad).
- Toda salida usa **lenguaje seguro** y nota de **revisión humana**.
- Retrieval reproducible; ejecución registrada en `progress/`.

## 7. Lenguaje seguro (no negociable)

Nunca afirmar corrupción/ilegalidad. Usar "señales de riesgo", "red flags potenciales", "posible irregularidad a revisar"; cerrar con "requiere revisión humana".

## 8. Fuera de alcance (por ahora)

Multi-tenant, billing, scraping masivo, despliegue en producción, acciones irreversibles, FastAPI/pgvector (el stack del proyecto es Colab + FAISS + Qwen; ver `docs/CAVELOG.md`).
