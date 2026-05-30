# Security Model — RAG Agentico

## Riesgos principales

1. Prompt injection en documentos indexados.
2. Data leakage entre tenants.
3. Herramientas MCP con permisos excesivos.
4. Respuestas sin fuente o con fuente inventada.
5. Indexación de documentos no autorizados.
6. Supply chain en dependencias.
7. Evals insuficientes.

## Controles mínimos

- Separación por tenant.
- Metadata obligatoria por documento.
- Hash de documento y versión.
- Citas obligatorias.
- Verificador de claims.
- Tool allowlist.
- Human approval para acciones sensibles.
- Logs de ejecución.
- Tests y evals antes de deploy.

## Regla de oro

El agente puede leer y proponer.
El sistema decide qué puede ejecutar.
El humano aprueba acciones irreversibles.
