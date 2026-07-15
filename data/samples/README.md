# Fixtures reales para probar el TDR Risk Auditor

Documentos públicos reales (SEACE, OSCE, PREDES, PRONIED, Contraloría),
descargados de internet, usados para validar el sistema con casos genuinos —
no sintéticos.

## Casos con irregularidad confirmada por el Tribunal de Contrataciones (OSCE)

Estas tres son resoluciones oficiales del Tribunal de Contrataciones del
Estado que **confirman jurídicamente** una irregularidad en el proceso de
selección. Son la prueba más fuerte disponible públicamente sin usar datos
sintéticos: el propio Estado declaró la nulidad o revocó la buena pro.

| Archivo | Caso | Hallazgo del Tribunal | Riesgo detectado |
|---|---|---|---|
| `tdr-tce-01626-2023-essalud-comite-nulo.pdf` | Licitación EsSalud N°003-2022 (S/ 114.9M, dispositivos médicos) | Comité de selección designado en contravención del art. 44 del Reglamento → **nulidad de toda la licitación** (bases y convocatoria incluidas) | Medio · grounding 0.96 · 1 señal: descalificación de todos los postores excepto el ganador |
| `tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf` | Adjudicación Simplificada N°004-2021, Hospital Belén Lambayeque (reactivos de laboratorio) | El ganador de la buena pro (UNILAP S.A.C.) **no cumplía el requisito de registro sanitario** → buena pro revocada, proceso declarado desierto | Medio · grounding 1.00 · 2 señales: ofertas descalificadas por errores formales + revocación de buena pro |
| `tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf` | Licitación N°4-2022-IAFAS-EP, FOSPEME (S/ 5.65M, medicamentos) | El adjudicatario **no acreditó el certificado/protocolo de análisis** exigido en las bases → buena pro revocada | Medio · grounding 1.00 · 1 señal: descalificación que deja un único ganador |

Fuente: `cdn.www.gob.pe` (Plataforma del Estado Peruano), resoluciones
públicas del Tribunal de Contrataciones del Estado.

## TDR reales sin irregularidad conocida (control)

| Archivo | Caso |
|---|---|
| `tdr-contraloria-bid-seguimiento-contractual.pdf` | TDR para especialista en seguimiento de ejecución contractual (proyecto BID SCC359, Contraloría) |
| `tdr-predes-zona-segura-los-olivos.pdf` | TDR de construcción "Zona Segura", Municipalidad de Los Olivos (PREDES) |
| `tdr-pronied-infraestructura-educativa.pdf` | TDR de infraestructura educativa (PRONIED) |

## Cómo probarlos

Subir cualquiera de estos archivos en `/analizar` (web) o vía
`POST /api/tdrs/upload` + `POST /api/tdrs/{id}/analyze` (API). Todos
producen grounding ≥0.95 y al menos una señal de riesgo con cita literal
en los tres casos con irregularidad confirmada.
