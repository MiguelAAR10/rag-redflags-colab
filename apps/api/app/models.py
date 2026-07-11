"""SQLModel table models for the TDR review web demo.

These models are intentionally simple: one file, no relationships, and
clear status strings so the UI can render state without extra joins.
Relationships are queried manually by foreign key (simpler and more
predictable for SQLModel 0.0.x).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Tdr(SQLModel, table=True):
    __tablename__ = "tdrs"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="uploaded")  # uploaded | analyzing | completed | failed


class TdrVersion(SQLModel, table=True):
    __tablename__ = "tdr_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    tdr_id: int = Field(foreign_key="tdrs.id")
    sha256: str
    file_path: str
    text_path: str
    char_count: int = 0
    parser_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisRun(SQLModel, table=True):
    __tablename__ = "analysis_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    tdr_version_id: int = Field(foreign_key="tdr_versions.id")
    status: str = Field(default="queued")  # queued | running | completed | failed
    model_name: str = ""
    grounding_ratio: float = 0.0
    refusal: str = ""
    risk_level: str = ""  # Bajo | Medio | Alto | Evidencia insuficiente
    risk_reason: str = ""
    summary: str = ""
    raw_json: str = ""  # serialized analysis output
    error_message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class RiskFinding(SQLModel, table=True):
    __tablename__ = "risk_findings"

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_run_id: int = Field(foreign_key="analysis_runs.id")
    title: str
    severity: str = ""  # Bajo | Medio | Alto
    evidence_quote: str = ""
    citation: str = ""
    explanation: str = ""
    accepted: bool = False
    rejection_reason: str = ""
    requires_human_review: bool = True


class EvidenceReview(SQLModel, table=True):
    __tablename__ = "evidence_reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_run_id: int = Field(foreign_key="analysis_runs.id")
    evidence_status: str = "weak"  # sufficient | weak | insufficient
    accepted_count: int = 0
    rejected_count: int = 0
    notes: str = ""


class DocChunk(SQLModel, table=True):
    """Chunk de un documento subido, con hash para reindexación incremental.

    F19 (spec 007): al re-subir una versión modificada, solo los chunks cuyo
    hash cambió se re-embeben y upsertean a Qdrant; los intactos reutilizan
    su punto existente.
    """

    __tablename__ = "doc_chunks"

    id: Optional[int] = Field(default=None, primary_key=True)
    tdr_version_id: int = Field(foreign_key="tdr_versions.id")
    chunk_hash: str = Field(index=True)
    ord: int = 0
    text: str = ""
    qdrant_point_id: str = ""  # vacío si aún no se ha indexado
    embedded_at: Optional[datetime] = None


class ChangeEvent(SQLModel, table=True):
    """Evento de cambio entre dos versiones de un documento (CDC, spec 007)."""

    __tablename__ = "change_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    tdr_id: int = Field(foreign_key="tdrs.id")
    from_version_id: int = Field(foreign_key="tdr_versions.id")
    to_version_id: int = Field(foreign_key="tdr_versions.id")
    chunks_added: int = 0
    chunks_removed: int = 0
    chunks_kept: int = 0
    detected_at: datetime = Field(default_factory=datetime.utcnow)