# Diseño — Descarga de PDFs de demostración

## Objetivo

Dar acceso estable desde la aplicación a los seis PDFs públicos de `data/samples/`, sin duplicarlos en el bundle de Vercel y sin presentar sus resultados como acusaciones.

## Decisión

La página `/documentos` mantendrá el historial efímero de la API y añadirá antes una sección estática **Documentos de demostración**. Cada caso tendrá:

- nombre corto y entidad/fuente;
- descripción prudente del hallazgo oficial o del uso de prueba;
- enlace `Descargar PDF` a `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/<archivo>`;
- enlace `Analizar un documento` a `/analizar`.

Los PDFs permanecen versionados una sola vez en GitHub. Vercel solo sirve la interfaz.

### Catálogo canónico

1. `tdr-tce-01626-2023-essalud-comite-nulo.pdf`
2. `tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf`
3. `tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf`
4. `tdr-contraloria-bid-seguimiento-contractual.pdf`
5. `tdr-predes-zona-segura-los-olivos.pdf`
6. `tdr-pronied-infraestructura-educativa.pdf`

La base raw y la referencia `main` estarán centralizadas en constantes. Se mantiene `main` por decisión del usuario para que la demo siempre exponga la versión publicada; CI y la protección de rama deben impedir renombres o eliminaciones accidentales.

## Lenguaje y seguridad

- Usar “señales de riesgo potenciales”, “hallazgo oficial documentado” y “requiere revisión humana”.
- No afirmar corrupción, fraude, culpabilidad ni ilegalidad por resultado del sistema.
- Identificar los documentos como fuentes públicas de demostración.
- Mostrar un aviso visible: son fuentes públicas para revisar señales potenciales; todo resultado requiere revisión humana.
- Reemplazar “TDRs auditados”/“Auditar” por “documentos revisados”/“Analizar” en esta página.
- Abrir descargas externas en una pestaña nueva con `rel="noreferrer"`.

## Error y disponibilidad

La sección estática debe renderizar aunque Cloud Run o SQLite no respondan. Los enlaces apuntan a `main`, y CI valida que los seis archivos estén versionados y que las URLs raw sean construibles desde nombres conocidos.

## Pruebas

- Test estático: seis archivos locales y seis nombres únicos.
- Test de interfaz: seis tarjetas con los nombres y URLs exactos, descarga externa con `target="_blank"` y `rel="noreferrer"`, y enlace a `/analizar`.
- La sección de demostración se renderiza aunque `listTdrs()` falle.
- Build Next.js y lint sin errores.
- Smoke HTTP 200 sobre cada URL raw después del push.
- La página conserva el historial actual y ofrece un camino visible a `/analizar`.

## Fuera de alcance

- Copiar PDFs a `apps/web/public`.
- Crear GitHub Releases.
- Ejecutar automáticamente el análisis al pulsar una tarjeta.
- Persistencia del historial de Cloud Run.
