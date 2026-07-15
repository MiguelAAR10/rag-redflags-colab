# Run — 2026-07-12 — frontend Next.js en Vercel + tdr-api en Cloud Run

## Objetivo
Reemplazar la UI Streamlit por un frontend React/Next.js de nivel producto en
Vercel, con branding UNI (minimalista blanco + guinda institucional), y exponer
el backend FastAPI como servicio JSON público en Cloud Run.

## Arquitectura final
- **Frontend:** Next.js 16 + React 19 + Tailwind 4 en `apps/web`, desplegado en
  Vercel → https://tdr-risk-auditor.vercel.app (proyecto `tdr-risk-auditor`,
  cuenta `miguelarias-9172`; `NEXT_PUBLIC_API_URL` en env de producción).
- **Backend:** servicio Cloud Run `tdr-api` (misma imagen que el contenedor
  Streamlit, command override a uvicorn `app.main:app --app-dir apps/api`),
  URL https://tdr-api-x42sfxhyha-uc.a.run.app. CORS `allow_origins=["*"]`
  agregado en `apps/api/app/main.py`. Deploy reproducible:
  `scripts/deploy-api.sh` (copia env vars del servicio Streamlit sin exponerlas).
- **Branding:** escudo oficial UNI (Wikimedia Commons, negro) recoloreado al
  guinda `#951414` sampleado de admision.uni.edu.pe →
  `apps/web/public/uni-escudo-{guinda,negro}.png`. Tema claro por tokens en
  `globals.css`.

## Archivos tocados
- `apps/web/**` (nuevo: landing, /analizar, /documentos, /como-funciona,
  `src/lib/api.ts` cliente tipado, `DossierView`, Nav/Footer)
- `apps/api/app/main.py` (CORSMiddleware)
- `scripts/deploy-api.sh` (nuevo), `.gcloudignore` (nuevo)

## Verificación
- `npm run build`: 4 rutas estáticas OK.
- E2E producción texto: TDR #1 → riesgo Medio, grounding 1.0, 3 señales
  aceptadas, ~6 s de análisis.
- E2E producción PDF (generado con PyMuPDF, subido como multipart): TDR #2 →
  riesgo Medio, grounding 1.0, 5 señales aceptadas (plazo corto, experiencia
  restrictiva, metodología no publicada, subcontratación 80%, presupuesto
  coincidente).
- Preflight CORS OPTIONS desde `Origin: tdr-risk-auditor.vercel.app` → 200 con
  `access-control-allow-origin: *`.

## Problemas encontrados
- El clasificador de permisos bloqueó (bien) inyectar la QDRANT_API_KEY por CLI;
  se resolvió con `scripts/deploy-api.sh` + aprobación del usuario.
- Bug del error del usuario: la web en Vercel fallaba con "CORS blocked" porque
  `tdr-api` aún no existía (el 404 del GFE no lleva cabeceras CORS). No era un
  problema del frontend.
- `/healthz` en `tdr-api` devuelve el 404 de Google (no bloqueante; `/api/*`
  funciona). Sospecha: ruta reservada/interceptada; investigar si molesta.

## Riesgos / pendientes
- CORS `*`: aceptable para demo pública; endurecer a dominio Vercel si pasa a
  uso real.
- SQLite efímero en `/tmp` del servicio `tdr-api` (igual que Streamlit).
- Streamlit sigue vivo como respaldo en la URL original.
- Pendiente heredado: Colab T4 Run all (`progress/NEXT_ACTION.md`).

## Próxima acción
Commitear `apps/web`, `scripts/deploy-api.sh`, `.gcloudignore` y el CORS de
`main.py` en la rama `v2` (aún sin commitear).
