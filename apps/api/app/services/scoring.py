"""RiskScoringAgent V1 — deterministic rules to convert the evidence
critique + accepted findings into a preliminary risk label.

Risk ladder (descending confidence):
- "Evidencia insuficiente": evidence_status == 'insufficient' OR refusal.
- "Bajo": zero accepted findings.
- "Medio": 1-2 accepted findings and no Alto-severity finding.
- "Alto": >=1 accepted finding with severity 'Alto' OR >=3 accepted findings.

Every label includes a deterministic `reason` string so the UI can
show why this risk was assigned. The disclaimers live in the Dossier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .evidence import CritiqueResult


@dataclass
class RiskVerdict:
    level: str
    reason: str


def score(critique: CritiqueResult) -> RiskVerdict:
    if critique.evidence_status == "insufficient":
        return RiskVerdict(
            level="Evidencia insuficiente",
            reason="El analizador se negó a emitir observaciones por falta de evidencia.",
        )

    accepted = critique.accepted_findings
    if not accepted:
        return RiskVerdict(
            level="Bajo",
            reason="No se identificaron señales de riesgo con evidencia suficiente.",
        )

    high_count = sum(1 for f in accepted if f.severity == "Alto")
    if high_count >= 1:
        return RiskVerdict(
            level="Alto",
            reason=f"{high_count} se\u00f1al(es) de severidad alta con evidencia.",
        )

    if len(accepted) >= 3:
        return RiskVerdict(
            level="Medio",
            reason=f"{len(accepted)} se\u00f1ales aceptadas, ninguna alta.",
        )

    return RiskVerdict(
        level="Medio",
        reason=f"{len(accepted)} se\u00f1al(es) aceptada(s), severidad media o baja.",
    )


def to_dict(verdict: RiskVerdict) -> Dict[str, str]:
    return {"level": verdict.level, "reason": verdict.reason}


def serialize_findings(findings: List) -> List[Dict]:
    return [
        {
            "title": f.title,
            "severity": f.severity,
            "evidence_quote": f.evidence_quote,
            "citation": f.citation,
            "explanation": f.explanation,
            "accepted": f.accepted,
            "rejection_reason": f.rejection_reason,
        }
        for f in findings
    ]