"""Orchestration layer that ties the agents together and persists results."""

from __future__ import annotations

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from sqlmodel import Session, select

from ..adapters.llm_factory import resolve_generate_fn
from ..config import get_settings
from ..db import get_session
from ..models import (
    AnalysisRun,
    EvidenceReview,
    RiskFinding,
    Tdr,
    TdrVersion,
)
from . import analysis as analysis_svc
from . import dossier as dossier_svc
from . import evidence as evidence_svc
from . import reindex as reindex_svc
from . import scoring as scoring_svc
from .intake import IntakeResult, persist_intake

logger = logging.getLogger(__name__)


class IntakeError(ValueError):
    """Raised when intake cannot produce usable text."""


def create_tdr_with_version(
    *,
    filename: str,
    raw_bytes: Optional[bytes],
    pasted_text: Optional[str],
) -> Dict:
    """Intake one document and persist Tdr + TdrVersion."""
    settings = get_settings()
    try:
        intake: IntakeResult = persist_intake(
            filename=filename,
            raw_bytes=raw_bytes,
            pasted_text=pasted_text,
            upload_dir=settings.upload_dir,
        )
    except ValueError as exc:
        raise IntakeError(str(exc)) from exc

    with get_session() as session:
        tdr = Tdr(filename=filename)
        session.add(tdr)
        session.flush()

        version = TdrVersion(
            tdr_id=tdr.id,
            sha256=intake.sha256,
            file_path=intake.file_path,
            text_path=intake.text_path,
            char_count=intake.char_count,
            parser_notes=intake.parser_notes,
        )
        session.add(version)
        session.flush()

        # F19: chunk + hash (+ upsert incremental a subject_docs si está
        # habilitado). Primera versión → sin ChangeEvent.
        reindex_summary = reindex_svc.reindex_version(
            session,
            tdr_id=tdr.id,
            version=version,
            text=intake.text,
            prev_version=None,
            index_enabled=settings.rag_index_subject_docs,
        )

        session.commit()
        session.refresh(tdr)
        session.refresh(version)
        return {
            "tdr_id": tdr.id,
            "version_id": version.id,
            "sha256": version.sha256,
            "char_count": version.char_count,
            "reindex": reindex_summary,
        }


def add_version_to_tdr(
    tdr_id: int,
    *,
    filename: str,
    raw_bytes: Optional[bytes],
    pasted_text: Optional[str],
) -> Dict:
    """Re-subida de un documento existente (F19: reindexación inteligente).

    - Mismo sha256 que la versión más reciente → no-op (sin versión nueva,
      sin ChangeEvent, cero embeddings).
    - Contenido distinto → versión nueva + diff por chunk (solo lo cambiado
      se embebe) + ChangeEvent con added/removed/kept.
    """
    settings = get_settings()
    try:
        intake: IntakeResult = persist_intake(
            filename=filename,
            raw_bytes=raw_bytes,
            pasted_text=pasted_text,
            upload_dir=settings.upload_dir,
        )
    except ValueError as exc:
        raise IntakeError(str(exc)) from exc

    with get_session() as session:
        tdr = session.get(Tdr, tdr_id)
        if not tdr:
            raise ValueError(f"TDR {tdr_id} no existe.")
        versions = session.exec(
            select(TdrVersion)
            .where(TdrVersion.tdr_id == tdr_id)
            .order_by(TdrVersion.id.desc())
        ).all()
        latest = versions[0] if versions else None

        if latest is not None and latest.sha256 == intake.sha256:
            logger.info(
                "Re-subida sin cambios para TDR %s (sha %s…): no-op.",
                tdr_id, intake.sha256[:12],
            )
            return {
                "tdr_id": tdr_id,
                "version_id": latest.id,
                "sha256": latest.sha256,
                "unchanged": True,
                "reindex": None,
            }

        version = TdrVersion(
            tdr_id=tdr_id,
            sha256=intake.sha256,
            file_path=intake.file_path,
            text_path=intake.text_path,
            char_count=intake.char_count,
            parser_notes=intake.parser_notes,
        )
        session.add(version)
        session.flush()

        reindex_summary = reindex_svc.reindex_version(
            session,
            tdr_id=tdr_id,
            version=version,
            text=intake.text,
            prev_version=latest,
            index_enabled=settings.rag_index_subject_docs,
        )

        tdr.status = "uploaded"
        tdr.filename = filename or tdr.filename
        session.add(tdr)
        session.commit()
        session.refresh(version)
        return {
            "tdr_id": tdr_id,
            "version_id": version.id,
            "sha256": version.sha256,
            "unchanged": False,
            "reindex": reindex_summary,
        }


def list_tdrs() -> List[Dict]:
    with get_session() as session:
        tdrs = session.exec(select(Tdr).order_by(Tdr.uploaded_at.desc())).all()
        out: List[Dict] = []
        for t in tdrs:
            versions = session.exec(
                select(TdrVersion)
                .where(TdrVersion.tdr_id == t.id)
                .order_by(TdrVersion.id.desc())
            ).all()
            latest_version = versions[0] if versions else None
            latest_run = None
            if latest_version is not None:
                runs = session.exec(
                    select(AnalysisRun)
                    .where(AnalysisRun.tdr_version_id == latest_version.id)
                    .order_by(AnalysisRun.id.desc())
                ).all()
                latest_run = runs[0] if runs else None
            out.append(
                {
                    "id": t.id,
                    "filename": t.filename,
                    "uploaded_at": t.uploaded_at,
                    "status": t.status,
                    "risk_level": latest_run.risk_level if latest_run else "",
                    "latest_run_status": latest_run.status if latest_run else "",
                }
            )
        return out


def get_tdr_detail(tdr_id: int) -> Optional[Dict]:
    with get_session() as session:
        t = session.get(Tdr, tdr_id)
        if not t:
            return None
        versions = session.exec(
            select(TdrVersion)
            .where(TdrVersion.tdr_id == t.id)
            .order_by(TdrVersion.id.desc())
        ).all()
        latest_version = versions[0] if versions else None
        latest_run = None
        if latest_version is not None:
            runs = session.exec(
                select(AnalysisRun)
                .where(AnalysisRun.tdr_version_id == latest_version.id)
                .order_by(AnalysisRun.id.desc())
            ).all()
            latest_run = runs[0] if runs else None
        return {
            "id": t.id,
            "filename": t.filename,
            "uploaded_at": t.uploaded_at,
            "status": t.status,
            "sha256": latest_version.sha256 if latest_version else "",
            "char_count": latest_version.char_count if latest_version else 0,
            "parser_notes": latest_version.parser_notes if latest_version else "",
            "latest_run": _run_to_dict(latest_run) if latest_run else None,
        }


def get_run_status(run_id: int) -> Optional[Dict]:
    with get_session() as session:
        run = session.get(AnalysisRun, run_id)
        if not run:
            return None
        version = session.get(TdrVersion, run.tdr_version_id)
        tdr_id_value = version.tdr_id if version else None
        data = _run_to_dict(run)
        if tdr_id_value is not None:
            data["tdr_id"] = tdr_id_value
        return data


def _run_to_dict(run: AnalysisRun) -> Dict:
    return {
        "id": run.id,
        "status": run.status,
        "risk_level": run.risk_level or "",
        "risk_reason": run.risk_reason or "",
        "grounding_ratio": run.grounding_ratio or 0.0,
        "refusal": run.refusal or "",
        "model_name": run.model_name or "",
        "error_message": run.error_message or "",
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


def queue_analysis(
    tdr_id: int,
    *,
    generate_fn: Optional[Callable[[str, List[Dict], str], str]] = None,
    retrieved_chunks: Optional[List[Dict]] = None,
    force: bool = False,
) -> int:
    """Create a queued analysis_run and run it synchronously inline.

    For the V1 demo we execute the pipeline immediately. The model
    already exposes the status field (`queued` -> `running` -> `completed`)
    so the UI can poll without further changes.

    Dedupe (spec 006): si la versión más reciente (mismo sha256 de texto)
    ya tiene un run `completed`, se devuelve ese run en vez de re-analizar.
    `force=True` fuerza un re-análisis explícito.
    """
    settings = get_settings()

    with get_session() as session:
        t = session.get(Tdr, tdr_id)
        if not t:
            raise ValueError(f"TDR {tdr_id} no existe.")
        versions = session.exec(
            select(TdrVersion)
            .where(TdrVersion.tdr_id == t.id)
            .order_by(TdrVersion.id.desc())
        ).all()
        if not versions:
            raise ValueError(f"TDR {tdr_id} no tiene versiones.")
        latest_version = versions[0]

        if not force:
            existing = session.exec(
                select(AnalysisRun)
                .where(AnalysisRun.tdr_version_id == latest_version.id)
                .where(AnalysisRun.status == "completed")
                .order_by(AnalysisRun.id.desc())
            ).first()
            if existing is not None:
                logger.info(
                    "Dedupe: versión %s (sha %s…) ya analizada en run %s.",
                    latest_version.id, latest_version.sha256[:12], existing.id,
                )
                return existing.id

        run = AnalysisRun(
            tdr_version_id=latest_version.id,
            status="queued",
            model_name=settings.rag_gemini_model,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

    try:
        _execute_run(
            run_id,
            generate_fn=generate_fn,
            retrieved_chunks=retrieved_chunks,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Análisis %s falló", run_id)
        _mark_run_failed(run_id, error=f"{exc}\n{traceback.format_exc()}")

    return run_id


def _execute_run(
    run_id: int,
    *,
    generate_fn: Optional[Callable[[str, List[Dict], str], str]] = None,
    retrieved_chunks: Optional[List[Dict]] = None,
) -> None:
    settings = get_settings()
    fn = generate_fn if generate_fn is not None else resolve_generate_fn()
    model_name = settings.rag_gemini_model

    with get_session() as session:
        run = session.get(AnalysisRun, run_id)
        if not run:
            return
        run.status = "running"
        run.model_name = model_name
        session.add(run)
        session.commit()

        version = session.get(TdrVersion, run.tdr_version_id)
        if not version:
            raise FileNotFoundError(f"Versión {run.tdr_version_id} no encontrada.")
        text_path = Path(version.text_path)
        if not text_path.exists():
            raise FileNotFoundError(f"Texto no encontrado: {text_path}")
        tdr_text = text_path.read_text(encoding="utf-8")

        # F18: retrieval vía VectorStore seleccionable. Con 'qdrant' el
        # backend no carga FAISS/E5 locales: embebe la query con Gemini y
        # consulta standard_kb en Qdrant Cloud. Con 'faiss' (default) el
        # retrieval lo hace agent.analyze() como en V1 (tests sin red).
        if retrieved_chunks is None and settings.rag_vector_store == "qdrant":
            from packages.rag_core.vector_store import make_vector_store

            store = make_vector_store("qdrant")
            retrieved_chunks = store.search(
                analysis_svc._build_query(tdr_text), k=settings.rag_retrieval_k
            )

        grounding_method = settings.rag_grounding_method
        grounding_threshold = (
            settings.grounding_threshold_semantic
            if grounding_method in ("gemini", "embedding")
            else settings.grounding_threshold
        )

        analysis = analysis_svc.run_analysis(
            tdr_text=tdr_text,
            generate_fn=fn,
            grounding_threshold=grounding_threshold,
            grounding_method=grounding_method,
            retrieved_chunks=retrieved_chunks,
            model_name=model_name,
        )

        critique = evidence_svc.critique(
            analysis.to_dict(),
            grounding_threshold=settings.grounding_threshold,
        )
        risk = scoring_svc.score(critique)
        dossier = dossier_svc.build_dossier(analysis, critique, risk)

        run.grounding_ratio = analysis.grounding_ratio
        run.refusal = analysis.refusal
        run.risk_level = risk.level
        run.risk_reason = risk.reason
        run.summary = dossier.summary
        run.raw_json = analysis_svc.safe_json_dumps(dossier.to_dict())
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.error_message = ""

        session.add(
            EvidenceReview(
                analysis_run_id=run.id,
                evidence_status=critique.evidence_status,
                accepted_count=len(critique.accepted_findings),
                rejected_count=len(critique.rejected_findings),
                notes=critique.notes,
            )
        )
        for f in critique.accepted_findings + critique.rejected_findings:
            session.add(
                RiskFinding(
                    analysis_run_id=run.id,
                    title=f.title,
                    severity=f.severity,
                    evidence_quote=f.evidence_quote,
                    citation=f.citation,
                    explanation=f.explanation,
                    accepted=f.accepted,
                    rejection_reason=f.rejection_reason,
                    requires_human_review=True,
                )
            )

        tdr = session.get(Tdr, version.tdr_id)
        if tdr:
            tdr.status = "completed"
            session.add(tdr)
        session.add(run)
        session.commit()


def _mark_run_failed(run_id: int, *, error: str) -> None:
    with get_session() as session:
        run = session.get(AnalysisRun, run_id)
        if not run:
            return
        run.status = "failed"
        run.error_message = error[:2000]
        run.completed_at = datetime.utcnow()
        version = session.get(TdrVersion, run.tdr_version_id)
        if version:
            tdr = session.get(Tdr, version.tdr_id)
            if tdr:
                tdr.status = "failed"
                session.add(tdr)
        session.add(run)
        session.commit()


def get_dossier(run_id: int) -> Optional[Dict]:
    """Return the dossier JSON for a given analysis run."""
    with get_session() as session:
        run = session.get(AnalysisRun, run_id)
        if not run:
            return None
        version = session.get(TdrVersion, run.tdr_version_id)
        if not version:
            return None
        tdr = session.get(Tdr, version.tdr_id)
        if not tdr:
            return None
        from .dossier import DISCLAIMER, NEXT_STEPS

        if run.raw_json:
            import json

            try:
                data = json.loads(run.raw_json)
            except Exception:
                data = {}
        else:
            data = {}

        return {
            "tdr_id": tdr.id,
            "filename": tdr.filename,
            "sha256": version.sha256,
            "risk_level": run.risk_level or "",
            "risk_reason": run.risk_reason or "",
            "summary": run.summary or "",
            "evidence": data.get("evidence") or {
                "status": "weak",
                "notes": "Dossier no reconstruido.",
                "accepted_count": 0,
                "rejected_count": 0,
            },
            "grounding_ratio": run.grounding_ratio or 0.0,
            "refusal": run.refusal or "",
            "findings": data.get("findings") or [],
            "rejected_findings": data.get("rejected_findings") or [],
            "uncertainty": data.get("uncertainty") or [],
            "next_steps": data.get("next_steps") or NEXT_STEPS,
            "disclaimer": data.get("disclaimer") or DISCLAIMER,
            "model_name": run.model_name or "",
            "completed_at": run.completed_at,
        }
