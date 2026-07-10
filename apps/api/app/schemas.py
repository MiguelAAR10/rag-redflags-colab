"""Pydantic request and response schemas for the API."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    tdr_id: int
    version_id: int
    sha256: str
    char_count: int
    auto_analyze: bool = True


class TdrListItem(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    status: str
    risk_level: Optional[str] = ""
    latest_run_status: Optional[str] = ""


class TdrDetail(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    status: str
    sha256: Optional[str] = ""
    char_count: Optional[int] = 0
    parser_notes: Optional[str] = ""
    latest_run: Optional["RunStatus"] = None


class RunStatus(BaseModel):
    id: int
    status: str
    risk_level: str = ""
    risk_reason: str = ""
    grounding_ratio: float = 0.0
    refusal: str = ""
    model_name: str = ""
    error_message: str = ""
    created_at: datetime
    completed_at: Optional[datetime] = None


class AnalyzeRequest(BaseModel):
    model_name: Optional[str] = None


class FindingOut(BaseModel):
    title: str
    severity: str
    evidence_quote: str
    citation: str
    explanation: str
    accepted: bool
    rejection_reason: str = ""


class EvidenceOut(BaseModel):
    status: str
    accepted_count: int
    rejected_count: int
    notes: str


class DossierOut(BaseModel):
    tdr_id: int
    filename: str
    sha256: str
    risk_level: str
    risk_reason: str
    summary: str
    evidence: EvidenceOut
    grounding_ratio: float
    refusal: str
    findings: List[FindingOut]
    uncertainty: List[str]
    next_steps: List[str]
    disclaimer: str
    model_name: str
    completed_at: Optional[datetime] = None


class HealthOut(BaseModel):
    status: str
    google_llm_configured: bool
    database_url_kind: str


TdrDetail.model_rebuild()