# Run — 2026-07-12 — validación con TDR reales, incluyendo casos con irregularidad confirmada

## Objetivo
El usuario pidió TDR reales de internet para probar la app en producción, y en
particular documentos donde exista corrupción/irregularidad real confirmada,
para validar que el sistema detecta señales de riesgo genuinas (no solo en
texto sintético con trampas).

## Estrategia
En vez de buscar TDR "sueltos" con corrupción (difíciles de encontrar como PDF
público y verificable), usé **resoluciones oficiales del Tribunal de
Contrataciones del Estado (OSCE)** — documentos públicos donde el propio
Estado peruano confirma jurídicamente una irregularidad en el proceso de
selección (nulidad, revocación de buena pro). Es la evidencia más fuerte
disponible sin recurrir a datos sintéticos.

## Documentos probados (subidos y analizados vía API en producción)
1. **TDR #6** — Resolución TCE N°01626-2023-S3: licitación EsSalud N°003-2022
   (S/114.9M, dispositivos médicos) anulada por comité de selección designado
   irregularmente (art. 44 del Reglamento).
   → Riesgo: **Medio** · grounding **0.9565** · 1 señal aceptada, 0 rechazadas.
2. **TDR #7** — Resolución TCE N°00132-2022-S1: Hospital Belén Lambayeque,
   buena pro revocada porque el ganador (UNILAP S.A.C.) no cumplía el
   registro sanitario exigido.
   → Riesgo: **Medio** · grounding **1.00** · 2 señales aceptadas, 0 rechazadas.
3. **TDR #8** — Resolución TCE N°04185-2022-S1: FOSPEME, buena pro revocada
   porque el adjudicatario no acreditó el certificado/protocolo de análisis
   exigido en bases.
   → Riesgo: **Medio** · grounding **1.00** · 1 señal aceptada, 0 rechazadas.

En los 3 casos el sistema generó señales con cita literal correcta del texto
(sin rechazos del EvidenceCritic), coherentes con el hallazgo real del
Tribunal: descalificaciones que dejan un único ganador, revocación de buena
pro, proceso declarado desierto.

También se habían probado antes (sesión previa) 2 TDR reales "limpios" sin
irregularidad conocida (Contraloría/BID, PREDES) con resultado Medio/grounding
1.00 y hallazgos menores no relacionados con corrupción.

## Archivos guardados en el repo
`data/samples/` (nuevo):
- `tdr-tce-01626-2023-essalud-comite-nulo.pdf`
- `tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf`
- `tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf`
- `tdr-contraloria-bid-seguimiento-contractual.pdf` (de sesión previa)
- `tdr-predes-zona-segura-los-olivos.pdf` (de sesión previa)
- `tdr-pronied-infraestructura-educativa.pdf` (de sesión previa, no analizado)
- `README.md` — tabla con caso, hallazgo del Tribunal y riesgo detectado.

## Fuente y licitud
Todos son documentos públicos oficiales (`cdn.www.gob.pe`, Plataforma del
Estado Peruano — resoluciones del Tribunal de Contrataciones del Estado) o de
ONGs/entidades públicas (PREDES, PRONIED, Contraloría/BID). No se usó ningún
dato privado ni de acceso restringido.

## Limitación observada
El riesgo preliminar del sistema se mantuvo en "Medio" en los 3 casos con
irregularidad confirmada — no escaló a "Alto" pese a que uno involucra S/114.9M
y nulidad total de la licitación. Posible área de calibración futura: el
riesgo agregado no pondera el monto ni la severidad jurídica del hallazgo
(nulidad total vs. descalificación parcial), solo la severidad individual de
cada señal (todas "Baja" en estos casos).

## Próxima acción sugerida
Si se quiere reforzar el caso de uso para el examen/demo, considerar calibrar
el mapeo de riesgo agregado para que casos con múltiples señales o con
"nulidad total" confirmada puedan alcanzar "Alto".
