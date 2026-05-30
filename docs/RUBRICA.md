# RUBRICA — Criterios de evaluación del proyecto final

Fuente: enunciado del Proyecto Final (Diseño e Implementación de un Sistema RAG en Google Colab).
Este archivo es la referencia del **reviewer** para auditar cada fase.

## Obligatorio (LLM Qwen)

El sistema **debe** usar un modelo de la familia **Qwen** para la generación. Decisión del proyecto: **Qwen2.5-3B-Instruct** (cabe en Colab T4).

## Rúbrica (0–20)

| Criterio | Puntos | Cómo lo cubrimos | Fase |
|---|---|---|---|
| Arquitectura correcta y funcional | 4 | Pipeline completo + diagrama en slides | 6, 8 |
| Chunking + análisis crítico | 4 | Comparar 2 tamaños + overlap; tabla tradeoff | 2 |
| Retrieval correctamente implementado | 4 | FAISS + top-k justificado + router por familias | 3, 4 |
| Grounding y reducción de alucinación | 3 | Ratio de frases soportadas + refusal | 6 |
| Evaluación coherente | 3 | Recall@k / Precision@k + grounding ratio | 7 |
| Presentación técnica y claridad | 2 | Slides 7 min + diagrama | 8 |
| **BONUS técnico** | hasta +2 | ver abajo | varias |

## Requisitos obligatorios (checklist)

- [ ] Dataset real ≥ 100 documentos (aquí: ≥100 **unidades documentales lógicas** del libro PDF) — explicar fuente, dominio, dificultades.
- [ ] Chunking + overlap; comparar ≥2 tamaños; explicar tradeoff tamaño/fragmentación, impacto en recuperación y rol del overlap.
- [ ] Embeddings pre-entrenados, con justificación de la elección y qué representan.
- [ ] FAISS (Flat o IVF); explicar búsqueda vectorial, top-k y justificar k.
- [ ] Pipeline RAG completo con diagrama claro.
- [ ] Grounding básico (proporción de frases respaldadas por chunks recuperados).
- [ ] Evaluación: análisis cualitativo (ejemplos buenos y malos) + ≥1 métrica coherente.

## BONUS (para máxima calificación)

- [ ] HNSW en FAISS (explicar y comparar vs Flat).
- [ ] Hybrid Search (BM25 + FAISS).
- [ ] Reranker cross-encoder (`BAAI/bge-reranker-v2-m3`; fallback a FAISS top-k si falla por memoria).
- [ ] Citation per sentence.
- [ ] Comparación entre dos LLMs (p.ej. Qwen2.5-3B vs 7B-4bit) — opcional según cuota Colab.
- [ ] Evaluación automática avanzada: BLEU/ROUGE.

## Entregables

- Notebook funcional en Colab (sigue la plantilla de 10 secciones).
- Slides de presentación (estructura de 8 puntos, 7 minutos).
- Entrega como ZIP o repositorio de GitHub.

## Plantilla del notebook (10 secciones)

1. Instalación de librerías · 2. Carga y exploración del dataset · 3. Chunking + comparación de tamaños · 4. Generación de embeddings · 5. Indexación con FAISS · 6. Retrieval top-k · 7. Integración con LLM (Qwen) · 8. Grounding básico · 9. Evaluación · 10. Análisis de resultados.

## Estructura de la presentación (7 min)

1. Título · 2. Problema · 3. Dataset · 4. Arquitectura RAG · 5. Decisiones técnicas (chunking, k, embeddings) · 6. Demo · 7. Resultados y análisis · 8. Conclusiones, limitaciones y mejoras futuras.
