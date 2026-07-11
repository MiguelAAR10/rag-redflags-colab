"""TDR Risk Auditor — frontend Streamlit (F22, spec 007).

Plataforma web del auditor preliminar de contratos/TDRs: sube un documento
(PDF/DOCX/TXT/MD), el pipeline RAG (Qdrant + Gemini 2.5 Flash vía Vertex)
recupera criterios de la guía OCP y produce un dossier con señales de riesgo
potenciales, citas y grounding. Importa el orchestrator directamente (mismo
contenedor que el backend), sin HTTP intermedio.

Lenguaje seguro SIEMPRE: señales de riesgo potenciales, requiere revisión
humana; nunca se afirma corrupción.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st

# --------------------------------------------------------------------------- #
# Configuración de página y estilos
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="TDR Risk Auditor",
    page_icon="🚩",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = """
<style>
.block-container { padding-top: 2.2rem; max-width: 1150px; }
.risk-banner {
    padding: 0.9rem 1.2rem; border-radius: 0.6rem; font-size: 1.15rem;
    font-weight: 600; margin: 0.4rem 0 1rem 0; color: white;
}
.risk-alto { background: #b3261e; }
.risk-medio { background: #b3661e; }
.risk-bajo { background: #2e7d32; }
.risk-insuficiente { background: #5f6368; }
.finding-card {
    border-left: 4px solid #b3261e; background: rgba(179,38,30,0.06);
    padding: 0.7rem 1rem; border-radius: 0 0.5rem 0.5rem 0; margin-bottom: 0.6rem;
}
.finding-rejected { border-left-color: #9aa0a6; background: rgba(154,160,166,0.08); }
.cite { font-size: 0.85rem; color: #5f6368; }
.disclaimer {
    font-size: 0.82rem; color: #5f6368; border-top: 1px solid #dadce0;
    padding-top: 0.7rem; margin-top: 1.4rem;
}
[data-testid="stMetricValue"] { font-size: 1.5rem; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

DISCLAIMER = (
    "⚖️ Este sistema identifica **señales de riesgo potenciales** basadas en la "
    "guía OCP 2024 de red flags en contratación pública. **No prueba corrupción, "
    "responsabilidad ni delito.** Todo hallazgo **requiere revisión humana** y "
    "contraste con las fuentes originales."
)

RISK_CLASS = {
    "Alto": "risk-alto",
    "Medio": "risk-medio",
    "Bajo": "risk-bajo",
    "Evidencia insuficiente": "risk-insuficiente",
}
RISK_ICON = {
    "Alto": "🔴", "Medio": "🟠", "Bajo": "🟢", "Evidencia insuficiente": "⚪",
}


# --------------------------------------------------------------------------- #
# Backend (import directo del orchestrator; init una sola vez)
# --------------------------------------------------------------------------- #


@st.cache_resource
def _init_backend():
    from app.db import init_db

    init_db()
    return True


_init_backend()


def _orchestrator():
    from app.services import orchestrator

    return orchestrator


# --------------------------------------------------------------------------- #
# Componentes de UI
# --------------------------------------------------------------------------- #


def risk_banner(level: str, reason: str = "") -> None:
    css = RISK_CLASS.get(level, "risk-insuficiente")
    icon = RISK_ICON.get(level, "⚪")
    reason_html = f" — {reason}" if reason else ""
    st.markdown(
        f'<div class="risk-banner {css}">{icon} Riesgo preliminar: '
        f"{level}{reason_html}</div>",
        unsafe_allow_html=True,
    )


def render_dossier(dossier: dict) -> None:
    risk_banner(dossier.get("risk_level", ""), dossier.get("risk_reason", ""))

    ev = dossier.get("evidence") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Grounding", f"{dossier.get('grounding_ratio', 0):.2f}")
    c2.metric("Señales aceptadas", ev.get("accepted_count", 0))
    c3.metric("Señales rechazadas", ev.get("rejected_count", 0))
    c4.metric("Evidencia", (ev.get("status") or "—").capitalize())

    if dossier.get("refusal"):
        st.info(f"🛡️ **Abstención segura del sistema:** {dossier['refusal']}")

    if dossier.get("summary"):
        st.markdown(f"**Resumen:** {dossier['summary']}")

    findings = dossier.get("findings") or []
    if findings:
        st.subheader(f"🚩 Señales de riesgo con evidencia ({len(findings)})")
        for f in findings:
            sev = f.get("severity") or "—"
            st.markdown(
                f'<div class="finding-card"><strong>{f.get("title", "Señal")}'
                f"</strong> · severidad {sev}<br>"
                f"<em>Evidencia:</em> {f.get('evidence_quote', '')}<br>"
                f"<em>Por qué importa:</em> {f.get('explanation', '')}<br>"
                f'<span class="cite">📎 {f.get("citation", "")}</span></div>',
                unsafe_allow_html=True,
            )

    rejected = dossier.get("rejected_findings") or []
    if rejected:
        with st.expander(f"🚫 Señales rechazadas por el crítico de evidencia ({len(rejected)})"):
            st.caption(
                "El EvidenceCritic rechaza señales sin cita literal — el gate "
                "anti-alucinación visible del sistema."
            )
            for f in rejected:
                st.markdown(
                    f'<div class="finding-card finding-rejected">'
                    f"<strong>{f.get('title', 'Señal')}</strong><br>"
                    f"<em>Motivo del rechazo:</em> {f.get('rejection_reason', '')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    uncertainty = dossier.get("uncertainty") or []
    if uncertainty:
        with st.expander("❓ Incertidumbre declarada"):
            for u in uncertainty:
                st.markdown(f"- {u}")

    steps = dossier.get("next_steps") or []
    if steps:
        with st.expander("🧭 Próximos pasos sugeridos"):
            for s in steps:
                st.markdown(f"- {s}")

    st.markdown(f'<div class="disclaimer">{dossier.get("disclaimer", "")}</div>',
                unsafe_allow_html=True)


def _run_analysis_flow(tdr_id: int) -> None:
    orch = _orchestrator()
    with st.spinner("Analizando con Gemini 2.5 Flash + guía OCP (Qdrant)…"):
        run_id = orch.queue_analysis(tdr_id)
    dossier = orch.get_dossier(run_id)
    if dossier:
        st.success(f"Análisis completado (run #{run_id}).")
        render_dossier(dossier)
    else:
        status = orch.get_run_status(run_id) or {}
        st.error(
            f"El análisis no se completó (estado: {status.get('status', '?')}). "
            f"{status.get('error_message', '')[:300]}"
        )


# --------------------------------------------------------------------------- #
# Páginas
# --------------------------------------------------------------------------- #


def page_upload() -> None:
    st.title("🚩 TDR Risk Auditor")
    st.caption(
        "Auditor preliminar de contratos, TDRs y licitaciones — RAG sobre la "
        "guía **OCP 2024 Red Flags** · Gemini 2.5 Flash (Vertex AI) · Qdrant Cloud."
    )
    st.markdown(DISCLAIMER)
    st.divider()

    tab_file, tab_text = st.tabs(["📄 Subir archivo", "✏️ Pegar texto"])

    with tab_file:
        uploaded = st.file_uploader(
            "Documento del proceso (PDF, DOCX, TXT o MD — máx. 20 MB)",
            type=["pdf", "docx", "txt", "md"],
        )
        analyze_now_f = st.checkbox("Analizar inmediatamente", value=True, key="an_f")
        if uploaded is not None and st.button("Procesar documento", type="primary"):
            _do_upload(filename=uploaded.name, raw_bytes=uploaded.getvalue(),
                       pasted_text=None, analyze=analyze_now_f)

    with tab_text:
        pasted = st.text_area(
            "Texto del contrato / TDR / licitación (mín. 200 caracteres)",
            height=220,
            placeholder=(
                "Ej.: Contrato de obra pública por 5M USD adjudicado a un solo "
                "oferente, con 3 días entre publicación y apertura de ofertas…"
            ),
        )
        analyze_now_t = st.checkbox("Analizar inmediatamente", value=True, key="an_t")
        if st.button("Procesar texto", type="primary", disabled=len(pasted.strip()) < 200):
            _do_upload(filename="texto-pegado.txt", raw_bytes=None,
                       pasted_text=pasted, analyze=analyze_now_t)


def _do_upload(*, filename, raw_bytes, pasted_text, analyze: bool) -> None:
    orch = _orchestrator()
    try:
        with st.spinner("Procesando documento (extracción + chunking + hash)…"):
            result = orch.create_tdr_with_version(
                filename=filename, raw_bytes=raw_bytes, pasted_text=pasted_text
            )
    except Exception as exc:
        st.error(f"No se pudo procesar el documento: {exc}")
        return

    ri = result.get("reindex") or {}
    st.success(
        f"Documento registrado (TDR #{result['tdr_id']}, "
        f"{result['char_count']:,} caracteres, {ri.get('chunks_total', 0)} chunks, "
        f"sha `{result['sha256'][:12]}…`)."
    )
    if analyze:
        _run_analysis_flow(result["tdr_id"])


def page_documents() -> None:
    st.title("📚 Documentos analizados")
    orch = _orchestrator()
    tdrs = orch.list_tdrs()
    if not tdrs:
        st.info("Aún no hay documentos. Sube el primero en **Analizar documento**.")
        return

    for t in tdrs:
        risk = t.get("risk_level") or "—"
        icon = RISK_ICON.get(risk, "⚪")
        label = (
            f"{icon} **{t['filename']}** · TDR #{t['id']} · {risk} · "
            f"{t.get('latest_run_status') or 'sin análisis'}"
        )
        with st.expander(label):
            detail = orch.get_tdr_detail(t["id"]) or {}
            c1, c2, c3 = st.columns(3)
            c1.metric("Caracteres", f"{detail.get('char_count', 0):,}")
            c2.metric("Estado", detail.get("status", "—"))
            c3.metric("Versión (sha)", (detail.get("sha256") or "")[:12] + "…")

            run = detail.get("latest_run")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                if st.button("🔍 Ver dossier / analizar", key=f"an_{t['id']}"):
                    if run and run.get("status") == "completed":
                        dossier = orch.get_dossier(run["id"])
                        if dossier:
                            render_dossier(dossier)
                    else:
                        _run_analysis_flow(t["id"])
            with col_b:
                st.caption("Re-subir versión modificada (adenda / corrección):")
                new_file = st.file_uploader(
                    "Nueva versión", type=["pdf", "docx", "txt", "md"],
                    key=f"rev_{t['id']}", label_visibility="collapsed",
                )
                if new_file is not None and st.button("Registrar versión", key=f"rv_{t['id']}"):
                    res = orch.add_version_to_tdr(
                        t["id"], filename=new_file.name,
                        raw_bytes=new_file.getvalue(), pasted_text=None,
                    )
                    if res.get("unchanged"):
                        st.info("El contenido es idéntico a la versión vigente: no se re-indexó nada.")
                    else:
                        ri = res.get("reindex") or {}
                        st.success(
                            f"Versión nueva registrada. Cambios: +{ri.get('chunks_added', 0)} "
                            f"chunks, −{ri.get('chunks_removed', 0)}, "
                            f"{ri.get('chunks_kept', 0)} intactos (solo lo nuevo se re-embebió)."
                        )


def page_about() -> None:
    st.title("ℹ️ Cómo funciona")
    st.markdown(
        """
| Etapa | Tecnología |
|---|---|
| Ingesta multi-formato | PDF (PyMuPDF) · DOCX (python-docx) · TXT/MD |
| Base de conocimiento | Guía **OCP 2024 Red Flags** (299 chunks) en **Qdrant Cloud** |
| Embeddings | `gemini-embedding-001` (768d) — corpus y consultas |
| Generación | **Gemini 2.5 Flash** vía Vertex AI |
| Verificación | Grounding semántico multilingüe por frase + citas |
| Crítico de evidencia | Rechaza señales sin cita literal (gate anti-alucinación) |
| Reindexación | Diff por hash de chunk: solo lo modificado se re-embebe |
| Abstención | Taxonomía estructurada: fuera de dominio / evidencia insuficiente |
        """
    )
    st.markdown(DISCLAIMER)


# --------------------------------------------------------------------------- #
# Navegación
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.markdown("## 🚩 TDR Risk Auditor")
    page = st.radio(
        "Navegación",
        ["Analizar documento", "Documentos", "Cómo funciona"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(
        "Proyecto final — IA Generativa · UNI 2026\n\n"
        "Señales de riesgo potenciales; **requiere revisión humana**."
    )

if page == "Analizar documento":
    page_upload()
elif page == "Documentos":
    page_documents()
else:
    page_about()
