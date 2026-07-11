"""Routes for the TDR review API and HTML views."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import get_settings
from ..services.intake import MAX_TEXT_CHARS
from ..services.orchestrator import (
    IntakeError,
    add_version_to_tdr,
    create_tdr_with_version,
    get_dossier,
    get_run_status,
    get_tdr_detail,
    list_tdrs,
    queue_analysis,
)


router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _base_context(request: Request) -> dict:
    return {"request": request, "settings": get_settings()}


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context["tdrs_count"] = len(list_tdrs())
    return templates.TemplateResponse(request, "home.html", context)


@router.get("/health")
def health() -> dict:
    from ..adapters.llm_factory import google_llm_configured

    settings = get_settings()
    return {
        "status": "ok",
        "google_llm_configured": google_llm_configured(),
        "database_url_kind": settings.database_url.split(":", 1)[0],
    }


@router.get("/tdrs/upload", response_class=HTMLResponse)
def upload_form(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context["max_text_chars"] = MAX_TEXT_CHARS
    return templates.TemplateResponse(request, "upload.html", context)


@router.post("/tdrs/upload")
async def upload(
    request: Request,
    file: Optional[UploadFile] = File(None),
    pasted_text: Optional[str] = Form(None),
    auto_analyze: bool = Form(True),
) -> RedirectResponse:
    raw_bytes: Optional[bytes] = None
    filename = "pasted.txt"
    if file is not None and file.filename:
        raw_bytes = await file.read()
        filename = file.filename

    text_clean = (pasted_text or "").strip()

    if not raw_bytes and not text_clean:
        raise HTTPException(
            status_code=400,
            detail="Debes subir un PDF/TXT o pegar texto del TDR.",
        )

    try:
        result = create_tdr_with_version(
            filename=filename,
            raw_bytes=raw_bytes,
            pasted_text=text_clean or None,
        )
    except IntakeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tdr_id = result["tdr_id"]
    if auto_analyze:
        queue_analysis(tdr_id)
    target = f"/tdrs/{tdr_id}"
    return RedirectResponse(url=target, status_code=303)


@router.get("/tdrs", response_class=HTMLResponse)
def tdrs_index(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context["tdrs"] = list_tdrs()
    return templates.TemplateResponse(request, "tdrs_list.html", context)


@router.get("/tdrs/{tdr_id}", response_class=HTMLResponse)
def tdr_detail(request: Request, tdr_id: int) -> HTMLResponse:
    detail = get_tdr_detail(tdr_id)
    if not detail:
        raise HTTPException(status_code=404, detail="TDR no encontrado.")
    context = _base_context(request)
    context["tdr"] = detail
    context["tdr_id"] = tdr_id
    return templates.TemplateResponse(request, "tdr_detail.html", context)


@router.post("/tdrs/{tdr_id}/analyze")
def analyze(tdr_id: int) -> RedirectResponse:
    detail = get_tdr_detail(tdr_id)
    if not detail:
        raise HTTPException(status_code=404, detail="TDR no encontrado.")
    run_id = queue_analysis(tdr_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_view(request: Request, run_id: int) -> HTMLResponse:
    status = get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run no encontrado.")
    context = _base_context(request)
    context["status"] = status
    context["run_id"] = run_id
    dossier_url = None
    if "tdr_id" in status:
        dossier_url = f"/tdrs/{status['tdr_id']}/dossier"
    context["dossier_url"] = dossier_url
    return templates.TemplateResponse(request, "run_status.html", context)


@router.get("/tdrs/{tdr_id}/dossier", response_class=HTMLResponse)
def dossier_view(request: Request, tdr_id: int) -> HTMLResponse:
    detail = get_tdr_detail(tdr_id)
    if not detail:
        raise HTTPException(status_code=404, detail="TDR no encontrado.")
    latest = detail.get("latest_run")
    context = _base_context(request)
    context["tdr"] = detail
    context["tdr_id"] = tdr_id
    if not latest or latest.get("status") != "completed":
        return templates.TemplateResponse(request, "dossier_pending.html", context)
    dossier = get_dossier(latest["id"])
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier no disponible.")
    context["dossier"] = dossier
    return templates.TemplateResponse(request, "dossier.html", context)


# JSON API ---------------------------------------------------------------

@router.post("/api/tdrs/upload")
async def api_upload(
    file: Optional[UploadFile] = File(None),
    pasted_text: Optional[str] = Form(None),
    auto_analyze: bool = Form(True),
) -> dict:
    raw_bytes: Optional[bytes] = None
    filename = "pasted.txt"
    if file is not None and file.filename:
        raw_bytes = await file.read()
        filename = file.filename

    text_clean = (pasted_text or "").strip()
    if not raw_bytes and not text_clean:
        raise HTTPException(
            status_code=400,
            detail="Debes subir un PDF/TXT o pegar texto del TDR.",
        )
    try:
        result = create_tdr_with_version(
            filename=filename,
            raw_bytes=raw_bytes,
            pasted_text=text_clean or None,
        )
    except IntakeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if auto_analyze:
        run_id = queue_analysis(result["tdr_id"])
        result["analysis_run_id"] = run_id
    return result

@router.post("/api/tdrs/{tdr_id}/upload")
async def api_upload_new_version(
    tdr_id: int,
    file: Optional[UploadFile] = File(None),
    pasted_text: Optional[str] = Form(None),
    auto_analyze: bool = Form(False),
) -> dict:
    """Re-subida de una version nueva de un TDR existente (F19).

    Mismo contenido -> no-op (unchanged=true). Contenido distinto -> version
    nueva con diff por chunk (solo lo cambiado se embebe) y ChangeEvent.
    """
    raw_bytes: Optional[bytes] = None
    filename = "pasted.txt"
    if file is not None and file.filename:
        raw_bytes = await file.read()
        filename = file.filename

    text_clean = (pasted_text or "").strip()
    if not raw_bytes and not text_clean:
        raise HTTPException(
            status_code=400,
            detail="Debes subir un archivo (PDF/DOCX/TXT/MD) o pegar texto.",
        )
    try:
        result = add_version_to_tdr(
            tdr_id,
            filename=filename,
            raw_bytes=raw_bytes,
            pasted_text=text_clean or None,
        )
    except IntakeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if auto_analyze and not result.get("unchanged"):
        run_id = queue_analysis(result["tdr_id"])
        result["analysis_run_id"] = run_id
    return result



@router.get("/api/tdrs")
def api_list_tdrs() -> dict:
    return {"tdrs": list_tdrs()}


@router.get("/api/tdrs/{tdr_id}")
def api_tdr_detail(tdr_id: int) -> dict:
    detail = get_tdr_detail(tdr_id)
    if not detail:
        raise HTTPException(status_code=404, detail="TDR no encontrado.")
    return detail


@router.post("/api/tdrs/{tdr_id}/analyze")
def api_analyze(tdr_id: int) -> dict:
    detail = get_tdr_detail(tdr_id)
    if not detail:
        raise HTTPException(status_code=404, detail="TDR no encontrado.")
    run_id = queue_analysis(tdr_id)
    return {"run_id": run_id}


@router.get("/api/runs/{run_id}")
def api_run(run_id: int) -> dict:
    status = get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run no encontrado.")
    return status


@router.get("/api/tdrs/{tdr_id}/dossier")
def api_dossier(tdr_id: int) -> dict:
    detail = get_tdr_detail(tdr_id)
    if not detail:
        raise HTTPException(status_code=404, detail="TDR no encontrado.")
    latest = detail.get("latest_run")
    if not latest or latest.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Dossier a\u00fan no disponible.")
    dossier = get_dossier(latest["id"])
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier no encontrado.")
    return dossier