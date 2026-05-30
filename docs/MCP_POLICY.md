# MCP Policy

## Principio

MCP da herramientas al agente. Toda herramienta debe tener permisos claros, logging y límites.

## Allowlist inicial

Permitido en desarrollo:
- filesystem local del repo
- shell controlado
- git read-only o ramas de trabajo
- Playwright MCP para pruebas
- Postgres dev
- navegador/scraper solo con fuentes autorizadas

No permitido sin aprobación:
- producción
- borrar datos
- modificar usuarios
- enviar correos
- publicar contenido
- ejecutar migraciones destructivas
- leer secretos

## Acciones con aprobación humana

- Deploy
- Merge a main
- Migración de base de datos
- Envío de emails
- Acceso a datos sensibles
- Indexación de documentos privados de cliente
- Cambios de permisos

## Logging obligatorio

Cada tool call relevante debe registrar:
- timestamp
- herramienta
- intención
- input resumido
- output resumido
- resultado
- evidencia

## Seguridad

Nunca enviar secretos al modelo.
Nunca guardar secretos en `progress/`, `docs/` o `CAVELOG`.
Usar `.env.example` para variables esperadas.
