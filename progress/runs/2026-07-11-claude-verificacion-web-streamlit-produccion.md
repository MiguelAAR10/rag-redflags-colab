# Run — 2026-07-11 — verificación web Streamlit en producción (Cloud Run)

## Objetivo
El usuario pidió "hacer la web RAG que reciba TDR en PDF y texto, en Streamlit,
lista para producción con Cloud Run". Se verificó que F22 ya entrega exactamente
eso y que sigue operativo.

## Hallazgo principal
La web YA EXISTE y está desplegada (commit `fbf58c3`, F22). No hubo que
implementar nada nuevo.

- App: `apps/web_streamlit/app.py` — tabs "Subir archivo" (PDF/DOCX/TXT/MD,
  máx. 20 MB) y "Pegar texto" (mín. 200 caracteres).
- Backend: orquestador importado directo (mismo contenedor), RAG con Qdrant
  (`standard_kb` 299 chunks OCP 2024) + Gemini 2.5 Flash vía Vertex AI.
- URL pública: https://tdr-risk-auditor-x42sfxhyha-uc.a.run.app

## Comandos ejecutados
```bash
curl https://tdr-risk-auditor-x42sfxhyha-uc.a.run.app/          # 200
curl .../_stcore/health                                          # 200
gcloud run services describe tdr-risk-auditor --region us-central1
bash scripts/verify.sh
```

## Resultados
- Cloud Run: revisión `tdr-risk-auditor-00001-6mq`, Ready=True, root y health 200.
- Gate local: **209 passed, 6 skipped** (5:49 min).
- Cambios pendientes en working tree (branch `v2`) son solo docs/notebook/progress
  — no tocan código de la app, así que la revisión desplegada está al día.

## Problemas / riesgos (heredados del handoff anterior, sin cambios)
- Metadata SQLite en `/tmp` es efímera: se pierde al desplegar nueva revisión
  (Qdrant sí persiste embeddings). Aceptado como limitación declarada de la demo.
- E2E público solo probó texto→dossier; el path PDF está cubierto por la suite
  de intake multi-formato (F19), no por un E2E en producción.
- Sigue pendiente: Colab T4 Run all para el `ragas-report.json` neural (humano).

## Próximos pasos
1. (Humano) Colab T4 Run all — ver `progress/NEXT_ACTION.md`.
2. Opcional: commitear los cambios de docs pendientes en `v2` y publicar a `main`.
3. Opcional hardening: probar E2E en producción con un PDF real y considerar
   persistencia SQL gestionada si la demo pasa a uso continuo.
