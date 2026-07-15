# Colab Dual RAG con Gemini y Qdrant

## Objetivo

Mantener `notebooks/redflags_rag_colab.ipynb` como entregable principal y
autosuficiente, con el corpus OCP 2024 cargado sin intervención manual y dos
backends de recuperación seleccionables:

1. `faiss`: E5 + FAISS local, modo académico predeterminado.
2. `qdrant`: `standard_kb` + `gemini-embedding-001`, modo cloud opcional.

Qwen seguirá siendo el generador académico predeterminado y obligatorio. Gemini
API se añadirá como generador opcional para demostrar los dos backends sin
reemplazar la ruta evaluada E5 + FAISS + Qwen. El flujo nuevo debe reutilizar
generación, grounding, citas y evaluación existentes.

## Alcance

- Carga automática de `OCP2024-RedFlagProcurement-1.pdf` desde el repositorio,
  con descarga pública de respaldo y validación básica del archivo.
- Lectura no interactiva de `GEMINI_API_KEY`, `QDRANT_URL` y
  `QDRANT_API_KEY` desde Colab Secrets o variables de entorno.
- Selector `RAG_BACKEND=faiss|qdrant`, con `faiss` como valor predeterminado.
- Contrato común de resultados para ambos backends.
- Generación opcional con Gemini API sobre los chunks recuperados.
- Comparación opcional de retrieval FAISS contra Qdrant.
- Tests herméticos con mocks, sin usar secretos ni red.

## Fuera de alcance

- Sustituir el pipeline Qwen requerido por la rúbrica.
- Hacer que Qdrant sea obligatorio para `Run all`.
- Modificar la aplicación Streamlit o el despliegue Cloud Run.
- Reindexar automáticamente `standard_kb` desde el notebook.
- Introducir LangGraph, Self-RAG, colas o nuevos servicios.

## Arquitectura

```text
OCP PDF incluido/descargado
          |
          +--> FAISS: E5 local + indice FAISS
          |
          +--> Qdrant: standard_kb + Gemini embeddings
                         |
                         v
              retrieve(query, backend, k)
                         |
                         v
                chunks normalizados
                         |
              +----------+----------+
              |                     |
              v                     v
       Qwen predeterminado     Gemini API opt-in
                         |
                         v
              grounding + citas + salida segura
```

El selector solo cambia la recuperación. Los dos backends deben devolver una
lista de diccionarios con, como mínimo:

```python
{
    "chunk_id": str,
    "text": str,
    "score": float,
    "indicator_code": str | None,
    "indicator_name": str | None,
    "family": str | None,
    "page_start": int | None,
    "page_end": int | None,
}
```

## Componentes

### Configuración del notebook

Una celda temprana define:

```python
RAG_BACKEND = os.getenv("RAG_BACKEND", "faiss").lower()
RAG_GENERATOR = os.getenv("RAG_GENERATOR", "qwen").lower()
RUN_QDRANT_DEMO = os.getenv("RUN_QDRANT_DEMO", "0") == "1"
RUN_DUAL_RAG_COMPARISON = os.getenv("RUN_DUAL_RAG_COMPARISON", "0") == "1"
```

Las credenciales se obtienen mediante `google.colab.userdata.get()` cuando
está disponible y, fuera de Colab, mediante variables de entorno. Nunca se usa
`getpass()` ni se imprime el valor de un secreto.

`RAG_BACKEND` es exclusivo del notebook. No reemplaza
`RAG_VECTOR_STORE`, que sigue siendo la configuración de la aplicación web.

### Corpus OCP

El notebook conserva el comportamiento actual:

- Usa `data/raw/OCP2024-RedFlagProcurement-1.pdf` incluido en el clone.
- Si falta, descarga el archivo desde el repositorio público.
- Verifica existencia y tamaño mínimo.
- No usa `files.upload()`.

### Backend FAISS

- Usa el pipeline existente E5 + FAISS.
- Es el backend predeterminado.
- Debe ejecutar `Run all` sin Qdrant.
- Mantiene retrieval híbrido y reranking donde ya se demuestran.
- Reutiliza `make_vector_store("faiss")` o los helpers actuales, sin copiar el
  algoritmo dentro del notebook.

### Backend Qdrant

- Consulta únicamente la colección `standard_kb`.
- Embebe queries con `gemini-embedding-001`, dimensión 768 y task type
  `RETRIEVAL_QUERY`.
- Normaliza la respuesta al mismo contrato que FAISS.
- Antes de buscar valida credenciales, existencia de la colección y presencia
  de puntos.
- Si no hay configuración, la celda informa `SKIPPED` y continúa.
- Reutiliza `make_vector_store("qdrant")` y los helpers de
  `packages.rag_core.gemini_embeddings`.

### Normalización de resultados

Una función importable normaliza ambos backends al contrato común. Debe:

- producir siempre las ocho claves documentadas;
- convertir `score` a `float`;
- usar `None` para metadata ausente;
- aceptar resultados vacíos;
- rechazar elementos sin `text` utilizable.

El notebook consume esa función; no es suficiente añadir código muerto que solo
contenga los nombres de los backends.

### Generación Qwen y Gemini

La ruta académica predeterminada conserva Qwen mediante `analyze()`.

La ruta Gemini es opt-in y reutiliza la inyección existente:

```python
analyze(
    query,
    retrieved_chunks=chunks,
    generate_fn=gemini_generate,
    grounding_method="embedding",
)
```

Una función inyectable recibe `query`, `retrieved_chunks` y `system_prompt`.
Debe:

- usar `google-genai`;
- usar `gemini-2.5-flash` por defecto;
- usar temperatura `0.1` y límite de salida configurable;
- pedir salida en lenguaje seguro;
- citar código de indicador y página de la guía OCP;
- citar también el fragmento o dato contractual que origina cada señal;
- responder "no hay evidencia suficiente" cuando corresponda;
- terminar indicando que requiere revisión humana.

Cada señal aceptada debe conservar dos evidencias separadas:

```python
{
    "contract_evidence": {"quote": str, "source": str},
    "standard_evidence": {
        "indicator_code": str,
        "page_start": int,
        "quote": str,
    },
    "requires_human_review": True,
}
```

Una señal sin evidencia contractual o sin evidencia OCP debe rechazarse o
convertirse en abstención por evidencia insuficiente.

Los tests usarán un cliente falso. Ningún test local llama a Gemini real.
Una respuesta vacía o una excepción de API debe producir un error controlado,
sin imprimir secretos ni caer silenciosamente al generador falso.

### Comparación opcional

Una celda opt-in compara ambos backends sobre una muestra del gold set y
reporta:

- indicadores recuperados;
- Recall@5;
- latencia;
- diferencias entre resultados.

La comparación excluye trampas sin indicadores esperados, compara códigos y
Recall@5, no scores crudos incompatibles. Cada backend reporta
`PASS`, `SKIPPED` o `ERROR`, con timeout explícito.

No forma parte del camino predeterminado de `Run all` para evitar costo y
dependencia de red.

## Flujo de errores

- PDF ausente o corrupto: fallo explícito antes de construir el índice.
- `RAG_BACKEND` desconocido: `ValueError` con valores permitidos.
- Falta `GEMINI_API_KEY`: se omite solo la integración Gemini; las secciones
  locales y Qwen continúan y no se declara Gemini validado.
- Faltan credenciales Qdrant: se marca Qdrant como omitido, no como aprobado.
- Colección vacía o incompatible: error descriptivo sin fallback silencioso a
  resultados inventados.
- Error de API: mostrar tipo de error sin imprimir tokens ni payload sensible.

## Testing

### Tests estáticos del notebook

- Notebook nbformat v4 válido.
- No contiene `getpass()` ni `files.upload()`.
- Contiene `RAG_BACKEND`, `faiss`, `qdrant` y `standard_kb`.
- Lee secretos sin imprimirlos.
- Mantiene secciones, Qwen, FAISS, grounding y lenguaje seguro.

### Tests unitarios

- Selector acepta `faiss` y `qdrant` y rechaza otros valores.
- Ambos backends normalizan el mismo esquema.
- Qdrant usa `RETRIEVAL_QUERY` y dimensión 768.
- El preflight Qdrant cubre colección inexistente, vacía, dimensión incorrecta
  y fallo del cliente.
- La generación Gemini se prueba con cliente falso que captura modelo,
  temperatura y límite de salida.
- Gemini cubre respuesta válida, vacía y excepción.
- Ausencia de secretos produce skip/fallback explícito.
- Respuesta sin evidencia conserva abstención y revisión humana.
- Una señal sin cita contractual o sin cita OCP no puede quedar aceptada.

### Tests de integración herméticos

- `selector -> FAISS falso -> Qwen/generador falso -> grounding -> citas`.
- `selector -> Qdrant falso -> Gemini falso -> grounding -> citas`.
- Backend inválido, retrieval vacío y API fallida.
- Qdrant omitido no construye cliente, embeddings ni llamadas de red.

### Verificación final

- `bash scripts/verify.sh` pasa localmente.
- El smoke estático del notebook pasa sin red; no se presenta como ejecución de
  celdas.
- En Colab T4, `Run all` funciona con `RAG_BACKEND=faiss`.
- En Colab T4 se registra evidencia manual de una ejecución fresca de
  `Run all` con Qwen.
- Con Secrets configurados y flags opt-in, una celda Qdrant recupera evidencia
  real de `standard_kb` y Gemini genera una respuesta con citas.

## Criterios de aceptación

- El PDF OCP no requiere carga manual.
- FAISS es el modo predeterminado y autosuficiente.
- Qdrant es seleccionable y no rompe `Run all` cuando no está configurado.
- Qwen + FAISS continúa siendo la ruta académica predeterminada.
- Gemini API funciona de forma opt-in con ambos backends mediante una sola ruta
  de generación.
- Cada señal aceptada cita tanto el dato contractual como la guía OCP.
- Los dos backends devuelven el mismo contrato de chunks.
- Los tests no requieren claves reales ni acceso a red.
- No se eliminan ni falsean las demostraciones de Qwen exigidas por la rúbrica.
- Toda salida conserva lenguaje de señales de riesgo potenciales y revisión
  humana.

## Dependencias y reutilización

- Añadir `google-genai` y `qdrant-client` a la celda de instalación, con imports
  tardíos para que FAISS/Qwen no dependa de credenciales Qdrant.
- Reutilizar `packages.rag_core.vector_store.make_vector_store`.
- Reutilizar `packages.rag_core.gemini_embeddings`.
- Reutilizar `packages.rag_core.agent.analyze` con `retrieved_chunks` y
  `generate_fn` inyectables.
- El adaptador Gemini debe vivir en un módulo importable y probado, no como
  implementación extensa dentro de una celda.
