"""EvidenceCritic V1 — deterministic gate that splits findings into
accepted (supported by retrieved evidence) and rejected (insufficient
evidence). This is the visible anti-hallucination feature of the
dossier: it tells the user how many signals survived the gate.

V1 rules:
- If the analyzer refused → evidence_status = insufficient.
- If grounding_ratio < threshold → evidence_status = weak.
- If citations list is empty → evidence_status = weak.
- Otherwise → evidence_status = sufficient.
- Findings are derived heuristically from the LLM answer + citations.
  Each "Señal" line becomes a finding; if it has no matching citation,
  it is rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


SIGNAL_REGEX = re.compile(
    r"^\s*(\d+)\.\s*Se\u00f1al:\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)


@dataclass
class Finding:
    title: str
    severity: str  # Bajo | Medio | Alto
    evidence_quote: str
    citation: str
    explanation: str
    accepted: bool
    rejection_reason: str = ""
    requires_human_review: bool = True


@dataclass
class CritiqueResult:
    evidence_status: str  # sufficient | weak | insufficient
    accepted_findings: List[Finding] = field(default_factory=list)
    rejected_findings: List[Finding] = field(default_factory=list)
    notes: str = ""

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_findings)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_findings)


def critique(analysis_dict: Dict, grounding_threshold: float = 0.25) -> CritiqueResult:
    """Apply the V1 evidence critic to the analyzer output."""
    refusal = (analysis_dict.get("refusal") or "").strip()
    citations: List[Dict] = analysis_dict.get("citations", []) or []
    grounding_ratio = float(analysis_dict.get("grounding_ratio", 0.0))
    answer = analysis_dict.get("answer", "") or ""

    if refusal:
        return CritiqueResult(
            evidence_status="insufficient",
            notes=f"Refusal del analizador: {refusal}",
        )

    if grounding_ratio < grounding_threshold:
        return CritiqueResult(
            evidence_status="weak",
            notes=(
                f"Grounding ratio {grounding_ratio:.2f} por debajo del "
                f"umbral {grounding_threshold:.2f}."
            ),
        )

    if not citations:
        return CritiqueResult(
            evidence_status="weak",
            notes="El analizador no produjo citas literales.",
        )

    findings = _extract_findings(answer, citations)
    accepted = [f for f in findings if f.accepted]
    rejected = [f for f in findings if not f.accepted]

    if not findings:
        return CritiqueResult(
            evidence_status="sufficient",
            notes="Sin señales extraídas; el dossier se limita al resumen.",
        )

    return CritiqueResult(
        evidence_status="sufficient",
        accepted_findings=accepted,
        rejected_findings=rejected,
        notes=f"{len(accepted)} señales aceptadas, {len(rejected)} rechazadas.",
    )


def _extract_findings(answer: str, citations: List[Dict]) -> List[Finding]:
    """Heuristically pull each "Señal" block from the answer and try
    to attach the nearest citation.

    The regex intentionally tolerates that LLMs vary in formatting.
    """
    if not answer:
        return []

    blocks = _split_blocks(answer)
    findings: List[Finding] = []
    for block in blocks:
        title = _block_title(block)
        if not title:
            continue
        evidence_quote = _block_field(block, "Evidencia del fragmento")
        citation_text = _best_citation(citations, title, evidence_quote)
        accepted = bool(citation_text)
        finding = Finding(
            title=title,
            severity=_infer_severity(title),
            evidence_quote=evidence_quote,
            citation=citation_text,
            explanation=_block_field(block, "Por qué importa"),
            accepted=accepted,
            rejection_reason="" if accepted else "Sin cita literal en el corpus.",
            requires_human_review=True,
        )
        findings.append(finding)
    return findings


def _split_blocks(answer: str) -> List[str]:
    """Split on numbered 'N. Señal:' lines."""
    indices = [m.start() for m in SIGNAL_REGEX.finditer(answer)]
    if not indices:
        return []
    indices.append(len(answer))
    return [answer[indices[i]:indices[i + 1]].strip() for i in range(len(indices) - 1)]


def _block_title(block: str) -> str:
    m = SIGNAL_REGEX.search(block)
    return m.group("title").strip() if m else ""


def _block_field(block: str, label: str) -> str:
    pattern = re.compile(
        rf"-\s*{re.escape(label)}\s*:\s*(?P<v>.+?)(?:\n\s*-\s|\n### |\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(block)
    if not m:
        return ""
    return m.group("v").strip().strip('"').strip("'")


def _infer_severity(title: str) -> str:
    t = title.lower()
    high_kw = ["fraude", "corrupción", "corrupcion", "colusión", "colusion", "ilegal", "urgente"]
    medium_kw = ["restrictivo", "restricción", "restriccion", "subjetivo", "opaco", "corto"]
    for kw in high_kw:
        if kw in t:
            return "Alto"
    for kw in medium_kw:
        if kw in t:
            return "Medio"
    return "Bajo"


def _best_citation(citations: List[Dict], title: str, quote: str) -> str:
    """Return a human-readable citation string if we can attach any
    citation to this finding. Currently uses heuristic: prefer any
    citation whose indicator_code is present in the answer block;
    otherwise pick the first citation as a fallback.
    """
    if not citations:
        return ""
    title_tokens = set(re.findall(r"\b\w{4,}\b", title.lower()))
    quote_tokens = set(re.findall(r"\b\w{4,}\b", (quote or "").lower()))

    for c in citations:
        indicator = (c.get("indicator_name") or "").lower()
        if any(tok in indicator for tok in title_tokens if len(tok) >= 5):
            return _format_citation(c)
    for c in citations:
        sentence = (c.get("sentence") or "").lower()
        if quote_tokens and any(tok in sentence for tok in quote_tokens if len(tok) >= 5):
            return _format_citation(c)
    return _format_citation(citations[0])


def _format_citation(c: Dict) -> str:
    code = c.get("indicator_code") or "N/A"
    name = c.get("indicator_name") or "Desconocida"
    pages = f"p.{c.get('page_start', '?')}-{c.get('page_end', '?')}"
    return f"{code} — {name} ({pages})"