# Fixtures reales para probar el TDR Risk Auditor

Documentos públicos reales (SEACE, OSCE, PREDES, PRONIED, Contraloría),
descargados de internet, usados para validar el sistema con casos genuinos —
no sintéticos.

## Casos con decisiones oficiales del Tribunal de Contrataciones (OSCE)

Estas tres son resoluciones oficiales del Tribunal de Contrataciones del
Estado que documentan decisiones de nulidad o revocación de la buena pro.
Sirven para contrastar señales de riesgo potenciales con una fuente pública;
el sistema no determina responsabilidades ni sustituye la revisión jurídica.
Todo resultado requiere revisión humana.

| Archivo | Caso | Hallazgo del Tribunal | Riesgo detectado |
|---|---|---|---|
| [Descargar PDF](https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-tce-01626-2023-essalud-comite-nulo.pdf) | Licitación EsSalud N°003-2022 (S/ 114.9M, dispositivos médicos) | La resolución declaró la nulidad del procedimiento por la conformación del comité | Medio · grounding 0.96 · 1 señal preliminar en la validación registrada |
| [Descargar PDF](https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf) | Adjudicación Simplificada N°004-2021, Hospital Belén Lambayeque | La resolución revocó la buena pro por el requisito de registro sanitario | Medio · grounding 1.00 · 2 señales preliminares en la validación registrada |
| [Descargar PDF](https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf) | Licitación N°4-2022-IAFAS-EP, FOSPEME | La resolución revocó la buena pro por la acreditación del certificado requerido | Medio · grounding 1.00 · 1 señal preliminar en la validación registrada |

Fuente: `cdn.www.gob.pe` (Plataforma del Estado Peruano), resoluciones
públicas del Tribunal de Contrataciones del Estado.

## Documentos de control sin decisión sancionadora referenciada

| Archivo | Caso |
|---|---|
| [Descargar PDF](https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-contraloria-bid-seguimiento-contractual.pdf) | TDR para especialista en seguimiento de ejecución contractual (proyecto BID SCC359, Contraloría) |
| [Descargar PDF](https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-predes-zona-segura-los-olivos.pdf) | TDR de construcción "Zona Segura", Municipalidad de Los Olivos (PREDES) |
| [Descargar PDF](https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-pronied-infraestructura-educativa.pdf) | TDR de infraestructura educativa (PRONIED) |

## Cómo probarlos

Subir cualquiera de estos archivos en `/analizar` (web) o vía
`POST /api/tdrs/upload` + `POST /api/tdrs/{id}/analyze` (API). Todos
En las validaciones registradas, los tres primeros casos produjeron grounding
≥0.95 y al menos una señal de riesgo potencial con cita literal. Estos valores
no son un veredicto y deben reproducirse antes de una presentación formal.
