"""DossierAgent — assembles the final dossier payload from the analysis,
critique, and risk verdict. Also produces the user-facing disclaimer
and the "next steps" guidance.

The dossier is the single, auditable artifact the user sees.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .analysis import AnalysisOutput
from .evidence import CritiqueResult
from .scoring import RiskVerdict, serialize_findings


DISCLAIMER = (
    "Este an\u00e1lisis identifica se\u00f1ales de riesgo potenciales en documentos "
    "p\u00fablicos. No es una acusaci\u00f3n ni determina responsabilidad. "
    "Requiere revisi\u00f3n humana y verificaci\u00f3n contra la fuente oficial."
)


NEXT_STEPS = [
    "Cruzar las se\u00f1ales con el expediente oficial de la contrataci\u00f3n.",
    "Validar las citas contra la gu\u00eda OCP/OCDS y los documentos del proceso.",
    "Solicitar al \u00e1rea correspondiente aclaraciones sobre los puntos se\u00f1alados.",
    "Documentar las observaciones y su trazabilidad para una posible auditor\u00eda.",
]


@dataclass
class Dossier:
    risk_level: str
    risk_reason: str
    summary: str
    evidence_status: str
    evidence_notes: str
    grounding_ratio: float
    refusal: str
    accepted_findings: List[Dict]
    rejected_findings: List[Dict]
    uncertainty: List[str]
    next_steps: List[str]
    disclaimer: str
    model_name: str
    completed_at: datetime

    def to_dict(self) -> Dict:
        return {
            "risk_level": self.risk_level,
            "risk_reason": self.risk_reason,
            "summary": self.summary,
            "evidence": {
                "status": self.evidence_status,
                "notes": self.evidence_notes,
                "accepted_count": len(self.accepted_findings),
                "rejected_count": len(self.rejected_findings),
            },
            "grounding_ratio": self.grounding_ratio,
            "refusal": self.refusal,
            "findings": self.accepted_findings,
            "rejected_findings": self.rejected_findings,
            "uncertainty": self.uncertainty,
            "next_steps": self.next_steps,
            "disclaimer": self.disclaimer,
            "model_name": self.model_name,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


def build_dossier(
    analysis: AnalysisOutput,
    critique: CritiqueResult,
    risk: RiskVerdict,
) -> Dossier:
    summary = _build_summary(analysis, critique, risk)
    uncertainty = _build_uncertainty(analysis, critique)
    return Dossier(
        risk_level=risk.level,
        risk_reason=risk.reason,
        summary=summary,
        evidence_status=critique.evidence_status,
        evidence_notes=critique.notes,
        grounding_ratio=analysis.grounding_ratio,
        refusal=analysis.refusal,
        accepted_findings=serialize_findings(critique.accepted_findings),
        rejected_findings=serialize_findings(critique.rejected_findings),
        uncertainty=uncertainty,
        next_steps=NEXT_STEPS,
        disclaimer=DISCLAIMER,
        model_name=analysis.model_name,
        completed_at=datetime.utcnow(),
    )


def _build_summary(
    analysis: AnalysisOutput,
    critique: CritiqueResult,
    risk: RiskVerdict,
) -> str:
    if critique.evidence_status == "insufficient":
        return (
            "No hay evidencia suficiente para emitir se\u00f1ales fundamentadas. "
            "El documento se consider\u00f3 fuera del corpus cubierto por la gu\u00eda."
        )
    if not critique.accepted_findings:
        return (
            f"La revisi\u00f3n preliminar del TDR no encontr\u00f3 se\u00f1ales con "
            f"evidencia suficiente. Grounding {analysis.grounding_ratio:.2f}, "
            f"citas recuperadas: {analysis.citations_count}."
        )
    return (
        f"Se identificaron {len(critique.accepted_findings)} se\u00f1ales de riesgo "
        f"con evidencia y {len(critique.rejected_findings)} sin evidencia "
        f"suficiente (rechazadas). Riesgo preliminar: {risk.level}."
    )


def _build_uncertainty(
    analysis: AnalysisOutput,
    critique: CritiqueResult,
) -> List[str]:
    items: List[str] = []
    if analysis.citations_count == 0:
        items.append("No se recuperaron citas literales de la gu\u00eda OCP/OCDS.")
    if analysis.grounding_ratio < 0.5:
        items.append(
            f"Grounding {analysis.grounding_ratio:.2f}: la respuesta "
            "del modelo a\u00fan no se apoya suficientemente en evidencia."
        )
    if critique.rejected_findings:
        items.append(
            f"{len(critique.rejected_findings)} se\u00f1al(es) no superaron el "
            "gate de evidencia y requieren verificaci\u00f3n manual."
        )
    if analysis.refusal:
        items.append("El analizador emiti\u00f3 una negativa expl\u00edcita (refusal).")
    if not items:
        items.append(
            "A\u00fan con evidencia suficiente, las se\u00f1ales son preliminares "
            "y deben cruzarse con el expediente completo."
        )
    return items