# Spec 003 — Agent Runtime

## Roles

### Planner
Decide estrategia de búsqueda.

### Retriever
Ejecuta búsquedas sobre índices y metadata.

### Answerer
Redacta respuesta usando evidencia.

### Verifier
Revisa si cada claim está soportado.

### Human Approver
Aprueba acciones sensibles o respuestas críticas.

## Flujo

```text
question
  -> classify intent
  -> plan retrieval
  -> retrieve evidence
  -> rerank
  -> answer draft
  -> verify claims
  -> final answer or refusal
```

## Estados mínimos

- received
- planned
- retrieved
- answered
- verified
- failed
- needs_human
