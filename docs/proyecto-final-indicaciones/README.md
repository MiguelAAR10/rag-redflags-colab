# Trabajo Final — Proyecto de Implementación: Sistema RAG e Ingeniería de Prompts

**Universidad Nacional de Ingeniería**  
Facultad de Ingeniería Económica, Estadística y Ciencias Sociales (FIEECS)  
Posgrado FIEECS · Maestría en Data Science

**Curso de Python para Data Science**  
**Lima, Perú · Ciclo 2026**

## Modalidad, duración y entrega

| Modalidad | Duración | Entrega final | Exposiciones |
|---|---|---|---|
| Parejas (2 integrantes) | 2 semanas | 4 de julio de 2026 | Desde el 6 de julio |

## 1. Objetivo del proyecto

El propósito del trabajo final es llevar a la práctica, de extremo a extremo, lo aprendido en Ingeniería de Prompts y Sistemas RAG, construyendo un sistema funcional que resuelva un problema concreto sobre un dominio real elegido por el equipo.

No se trata de repetir los ejemplos de clase, sino de reutilizar esas técnicas, mejorarlas o combinarlas para implementar una solución propia.

El énfasis está en la implementación: el resultado debe ser un sistema que se ejecute y demuestre su utilidad, acompañado de evidencia de funcionamiento confiable: recuperación correcta, control de alucinaciones, comportamiento seguro y métricas objetivas de calidad.

## 2. Modalidad y conformación de equipos

El trabajo se desarrolla en parejas de 2 integrantes.

La inscripción se realiza en el archivo Excel de inscripción que se distribuirá: una persona registra a la pareja, escribiendo sus datos y los de su compañero(a) en la misma fila e indicando un dominio tentativo.

Fecha límite de inscripción: **viernes 26 de junio de 2026**.

## 3. Qué deben construir

El sistema se organiza en tres partes:

1. Un componente base obligatorio.
2. Un conjunto de técnicas avanzadas a elegir.
3. Una evaluación del propio sistema.

## 3.1 Componente base obligatorio — RAG vertical de dominio

Requisitos:

- Definir un dominio y un corpus propio con documentos reales del caso: normativa, manuales, guías, bases de datos, etc.
- No basta con el corpus de los ejemplos de clase.
- Implementar el pipeline RAG completo:
  - ingesta y fragmentación (chunking);
  - generación de embeddings;
  - indexación con FAISS;
  - recuperación top-k;
  - generación de la respuesta con el modelo de chat.
- La respuesta final debe estar fundamentada en el contexto recuperado (grounding), no en el conocimiento libre del modelo.

## 3.2 Menú de técnicas avanzadas

El equipo debe incorporar al menos 2 técnicas avanzadas vistas en clase, justificando por qué son adecuadas para el caso.

Opciones:

- Ingesta multiformato (PDF / DOCX / TXT) con parsers por extensión.
- Re-ranking con cross-encoder para reordenar los fragmentos recuperados por relevancia real.
- Multi-query expansion: generar variantes o sinónimos de la consulta antes de buscar.
- Guardrails de cumplimiento: protección de PII, defensa contra prompt injection y/o filtro de sesgos y toxicidad.
- Citación obligatoria / trazabilidad de la fuente en cada respuesta.
- RAG agéntico con autocorrección (Self-RAG): bucle que evalúa y corrige el borrador antes de responder.
- Text-to-SQL RAG: traducir preguntas en lenguaje natural a consultas SQL sobre datos estructurados.
- Routing condicional / triaje, o comité multi-persona con reglas de decisión y veto.
- Few-shot con salida JSON estricta y/o Chain-of-Thought con reglas de negocio explícitas.

## 3.3 Evaluación y monitoreo del sistema con métricas RAGAS

La evaluación con métricas RAGAS es obligatoria.

El sistema debe monitorearse con métricas del framework RAGAS, evaluación sin respuestas de referencia, cubriendo recuperación y generación.

Métricas requeridas:

- **Faithfulness (fidelidad) — generación:** mide si la respuesta está fundamentada en el contexto recuperado. Sirve para controlar alucinaciones. Se calcula como la proporción de afirmaciones de la respuesta que pueden inferirse del contexto.
- **Answer Relevance (relevancia de la respuesta) — generación:** mide si la respuesta atiende realmente la pregunta, penalizando respuestas incompletas o redundantes. Se estima por la similitud entre la pregunta original y preguntas regeneradas a partir de la respuesta.
- **Context Relevance (relevancia del contexto) — recuperación:** mide si el contexto recuperado es pertinente y enfocado, sin información irrelevante. Es la proporción de oraciones del contexto que resultan relevantes para la pregunta.

Se puede usar la librería `ragas`, que se integra con LangChain y LlamaIndex, o implementar las métricas siguiendo el paper de referencia.

Debe construirse un set de evaluación de 10 a 15 preguntas representativas del dominio, incluyendo al menos 2 preguntas trampa fuera del corpus.

Se deben reportar los puntajes RAGAS sobre ese set y comentar qué revelan sobre la recuperación y la generación del sistema.

## 4. Entregables

Se entregan dos artefactos:

1. Notebook reproducible.
2. Presentación.

El foco del proyecto está en estos dos elementos.

## 4.1 Notebook reproducible en Google Colab

Debe ejecutarse de inicio a fin con **Run all** sin intervención manual ni errores. Una celda que falla penaliza la nota.

Requisitos:

- La primera celda debe ser una ficha técnica del sistema: dominio, objetivo, arquitectura, modelos y técnicas.
- Debe seguir el formato visto en los notebooks de clase.
- Incluir una tabla de trazabilidad que indique, para cada técnica o requisito, en qué celda del notebook se encuentra.
- El código debe estar comentado y organizado por secciones: ingesta, indexación, recuperación, generación y evaluación.

## 4.2 Presentación

La presentación debe servir como material de apoyo para la exposición.

Debe cubrir:

- problema y dominio;
- arquitectura del sistema;
- técnicas implementadas;
- resultados de evaluación con métricas RAGAS;
- demostración en vivo del sistema.

## 5. Requisitos mínimos para aprobar

Si falta alguno de estos puntos, la nota queda topada.

1. El notebook ejecuta Run all sin errores.
2. El corpus es propio y real, no únicamente el de los ejemplos de clase.
3. Se implementaron al menos 2 técnicas del menú avanzado.
4. Existe un set de evaluación de mínimo 10 preguntas, con al menos 2 preguntas trampa.
5. Se implementaron las métricas RAGAS: faithfulness, answer relevance y context relevance.
6. Se reportan los puntajes RAGAS.
7. La ficha técnica y la tabla de trazabilidad están completas.
8. Ambos integrantes participan en la exposición.

## 6. Cronograma

| Fecha | Hito |
|---|---|
| Miércoles 24 de junio | Publicación del entregable e inicio de inscripción de equipos. |
| Viernes 26 de junio | Fecha límite de inscripción en archivo Excel. |
| Sábado 4 de julio | Entrega final de notebook y presentación. |
| Desde el 6 de julio | Inicio de exposiciones, semana del 6 al 12 de julio. |

El calendario específico de exposiciones se confirmará una vez cerrada la inscripción, según el número de equipos.

## 7. Exposición

- Duración aproximada: 20 minutos de exposición con demostración en vivo.
- Preguntas del evaluador: 5 minutos.
- Ambos integrantes deben exponer y responder.

## 8. Criterios de evaluación

| Criterio | Peso |
|---|---:|
| Funcionalidad y reproducibilidad del sistema: Run all, pipeline RAG completo | 20 % |
| Técnicas avanzadas implementadas y justificadas, mínimo 2 | 15 % |
| Evaluación y monitoreo con métricas RAGAS: recuperación + generación | 25 % |
| Documentación del notebook: ficha técnica y tabla de trazabilidad | 10 % |
| Exposición y demostración en vivo | 20 % |
| Respuestas a las preguntas del evaluador | 10 % |
| **Total** | **100 %** |

Bonus que suma a la nota:

- interfaz de usuario sencilla, Gradio o Streamlit;
- benchmark comparativo entre dos o más arquitecturas RAG;
- despliegue del sistema.

## 9. Recomendaciones

- Empezar por un corpus pequeño pero real y hacer funcionar el RAG base cuanto antes.
- Añadir técnicas avanzadas después de que el RAG base funcione.
- Definir dominio y corpus en los primeros días.
- Construir temprano el set de evaluación.
- Probar Run all en una sesión limpia de Colab antes de entregar.
- Gestionar token y credenciales mediante Secretos de Colab, como en clase.

## 10. Recursos de referencia

Los notebooks trabajados en clase son la base directa del proyecto:

- **Ingeniería de Prompts:** system prompts, temperatura, memoria, few-shot, salida JSON, Chain-of-Thought, reglas de negocio, delimitadores, routing, multi-persona, guardrails, defensa contra injection, grounding y filtros de IA responsable.
- **Sistemas RAG:** RAG base con FAISS, ingesta multiformato, guardrails de cumplimiento, reranking con cross-encoder, Text-to-SQL RAG y RAG agéntico con autocorrección.
- **Métricas RAGAS:** Es, S., James, J., Espinosa-Anke, L. y Schockaert, S. (2025). *Ragas: Automated Evaluation of Retrieval Augmented Generation* (arXiv:2309.15217). Framework y librería para evaluar fidelidad, relevancia de la respuesta y relevancia del contexto sin respuestas de referencia.

Palabras clave: RAG, FAISS, embeddings, prompt engineering, guardrails, RAGAS, Self-RAG, Text-to-SQL.
