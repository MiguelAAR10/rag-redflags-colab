"""Small, dependency-light helpers for the dual-backend Colab notebook.

Este módulo es importable sin tener google-genai ni qdrant_client instalados.
Las dependencias opcionales se cargan lazy dentro de ``retrieve``.
"""

from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, Dict, Iterable, List, Mapping, Optional

from packages.rag_core.citations import build_citations
from packages.rag_core.verifier import split_sentences, verify_grounding


HUMAN_REVIEW = "Requiere revisión humana."
RECALL_K = 5
_MIN_CONTRACT_QUOTE_LEN = 10


def _env(environ: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def qdrant_configured(environ: Optional[Mapping[str, str]] = None) -> bool:
    """Return whether both Qdrant endpoint and API key are available."""
    values = _env(environ)
    endpoint = values.get("QDRANT_URL") or values.get("QDRANT_ENDPOINT")
    return bool(endpoint and values.get("QDRANT_API_KEY"))


def gemini_configured(environ: Optional[Mapping[str, str]] = None) -> bool:
    """Return whether Gemini API-key or Vertex ADC configuration is complete."""
    values = _env(environ)
    if values.get("GOOGLE_API_KEY") or values.get("GEMINI_API_KEY"):
        return True
    return _truthy(values.get("GOOGLE_GENAI_USE_VERTEXAI", "")) and bool(
        values.get("GOOGLE_CLOUD_PROJECT")
    )


def _retrieval_result(
    backend: str,
    status: str,
    started: float,
    *,
    results: Optional[List[Dict]] = None,
    error: Optional[str] = None,
) -> Dict:
    return {
        "backend": backend,
        "status": status,
        "results": results or [],
        "latency_ms": max(0.0, (time.perf_counter() - started) * 1000),
        "error": error,
    }


def retrieve(
    query: str,
    backend: str = "faiss",
    k: int = 5,
    timeout_s: float = 30.0,
    **store_kwargs,
) -> Dict:
    """Retrieve with an explicit PASS/SKIPPED/ERROR envelope.

    Qdrant and Gemini configuration is checked before the shared factory is
    called, so missing credentials never instantiate an external client.
    """
    started = time.perf_counter()
    backend = str(backend or "faiss").strip().lower()
    if backend not in {"faiss", "qdrant"}:
        return _retrieval_result(
            backend,
            "ERROR",
            started,
            error=f"backend desconocido: {backend!r}",
        )
    if not isinstance(query, str) or not query.strip():
        return _retrieval_result(
            backend, "ERROR", started, error="La consulta está vacía."
        )
    if k <= 0:
        return _retrieval_result(
            backend, "ERROR", started, error="k debe ser mayor que cero."
        )
    if timeout_s <= 0:
        return _retrieval_result(
            backend, "ERROR", started, error="timeout_s debe ser mayor que cero."
        )

    if backend == "qdrant":
        explicit_qdrant = bool(
            store_kwargs.get("client")
            or (
                (store_kwargs.get("url") or store_kwargs.get("endpoint"))
                and store_kwargs.get("api_key")
            )
        )
        explicit_gemini = bool(store_kwargs.get("embed_fn"))
        if not (explicit_qdrant or qdrant_configured()) or not (
            explicit_gemini or gemini_configured()
        ):
            return _retrieval_result(
                backend,
                "SKIPPED",
                started,
                error="Faltan credenciales de Qdrant o Gemini.",
            )

    try:
        from packages.rag_core.vector_store import make_vector_store

        store = make_vector_store(backend, **store_kwargs)
    except Exception as exc:
        return _retrieval_result(backend, "ERROR", started, error=str(exc))

    # Local executor: no global pool, closed automatically.
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(store.search, query.strip(), k)
        try:
            results = future.result(timeout=timeout_s)
        except FutureTimeout:
            future.cancel()
            return _retrieval_result(
                backend,
                "ERROR",
                started,
                error=f"Timeout de retrieval después de {timeout_s:g}s.",
            )
        except Exception as exc:
            return _retrieval_result(backend, "ERROR", started, error=str(exc))

    return _retrieval_result(backend, "PASS", started, results=list(results or []))


def _unique_codes(results: Iterable[Dict], k: int) -> List[str]:
    codes = []
    for result in list(results)[:k]:
        code = result.get("indicator_code")
        if code and code not in codes:
            codes.append(str(code))
    return codes


def _recall(retrieved: Iterable[str], relevant: Iterable[str]) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    return len(set(retrieved) & relevant_set) / len(relevant_set)


def compare_backends(
    gold_items: Iterable[Dict],
    *,
    timeout_s: float = 30.0,
    retrieve_fn: Callable[..., Dict] = retrieve,
) -> Dict:
    """Compare FAISS and Qdrant by codes, Recall@5, and observed latency.

    Backend similarity scores are deliberately excluded because they are not
    calibrated onto a common scale.
    """
    items = [item for item in gold_items if not item.get("trap")]
    report = {
        "status": "SKIPPED" if not items else "PASS",
        "k": RECALL_K,
        "evaluated_items": len(items),
        "backends": {},
        "differences": [],
    }
    if not items:
        return report

    per_query: Dict[str, Dict[str, List[str]]] = {}
    any_error = False
    any_skipped = False
    for backend in ("faiss", "qdrant"):
        rows = []
        recalls = []
        latency_ms = 0.0
        statuses = []
        for item in items:
            outcome = retrieve_fn(
                item.get("query", ""),
                backend=backend,
                k=RECALL_K,
                timeout_s=timeout_s,
            )
            status = outcome.get("status", "ERROR")
            statuses.append(status)
            if status == "ERROR":
                any_error = True
            elif status == "SKIPPED":
                any_skipped = True
            latency_ms += float(outcome.get("latency_ms") or 0.0)
            codes = _unique_codes(outcome.get("results") or [], RECALL_K)
            relevant = list(item.get("relevant_indicator_codes") or [])
            recall = _recall(codes, relevant) if status == "PASS" else 0.0
            recalls.append(recall)
            query = item.get("query", "")
            per_query.setdefault(query, {})[backend] = codes
            rows.append(
                {
                    "query": query,
                    "relevant_codes": relevant,
                    "retrieved_codes": codes,
                    "recall_at_5": recall,
                    "latency_ms": float(outcome.get("latency_ms") or 0.0),
                    "status": status,
                    "error": outcome.get("error"),
                }
            )

        backend_status = "PASS"
        if "ERROR" in statuses:
            backend_status = "ERROR"
        elif all(status == "SKIPPED" for status in statuses):
            backend_status = "SKIPPED"
        report["backends"][backend] = {
            "status": backend_status,
            "recall_at_5": sum(recalls) / len(recalls),
            "latency_ms": latency_ms,
            "items": rows,
        }

    report["status"] = (
        "ERROR" if any_error else ("SKIPPED" if any_skipped else "PASS")
    )
    for item in items:
        query = item.get("query", "")
        faiss = set(per_query.get(query, {}).get("faiss", []))
        qdrant = set(per_query.get(query, {}).get("qdrant", []))
        report["differences"].append(
            {
                "query": query,
                "only_faiss": sorted(faiss - qdrant),
                "only_qdrant": sorted(qdrant - faiss),
            }
        )
    return report


_SIGNAL_BLOCK_RE = re.compile(
    r"(?ms)^\s*(\d+)\.\s*Señal(?:\s+de\s+riesgo(?:\s+potencial)?)?\s*:\s*(.+?)"
    r"(?=^\s*\d+\.\s*Señal|\Z)"
)
_CONTRACT_EVIDENCE_RE = re.compile(
    r"(?im)^\s*[-*]?\s*Evidencia\s+del\s+fragmento\s*:\s*(.+?)\s*$"
)
_QUOTE_CHARS = "\"'“”‘’"


def _contract_quote_verified(quote: str, contract_text: str) -> bool:
    """Literal exact match of a contract quote, with word boundary for single words."""
    quote = str(quote).strip().strip(_QUOTE_CHARS)
    if len(quote) < _MIN_CONTRACT_QUOTE_LEN:
        return False
    if " " in quote:
        return quote in contract_text
    return bool(re.search(rf"\b{re.escape(quote)}\b", contract_text))


def _extract_signal_sentences(block: str) -> List[str]:
    """Return analysis sentences from a signal block, excluding title and evidence line."""
    lines = block.splitlines()
    body_lines = []
    for line in lines[1:]:
        if _CONTRACT_EVIDENCE_RE.search(line):
            continue
        body_lines.append(line)
    return split_sentences("\n".join(body_lines))


def validate_dual_evidence(analysis: Dict, contract_text: str) -> Dict:
    """Validate literal contract and OCP evidence independently per signal.

    Uses ``verify_grounding`` and ``build_citations`` from the RAG core instead
    of regex matching for OCP evidence. Contract evidence is verified by exact
    literal search.
    """
    analysis = analysis if isinstance(analysis, dict) else {}
    answer = str(analysis.get("answer") or "")
    retrieved = list(analysis.get("retrieved") or [])
    signals = []

    for match in _SIGNAL_BLOCK_RE.finditer(answer):
        signal_index = int(match.group(1))
        block = match.group(2)
        title_line = block.splitlines()[0].strip() if block.strip() else ""

        evidence_match = _CONTRACT_EVIDENCE_RE.search(block)
        contract_quote = evidence_match.group(1).strip() if evidence_match else ""
        contract_verified = _contract_quote_verified(contract_quote, contract_text)

        sentences = _extract_signal_sentences(block)
        if sentences and retrieved:
            grounding = verify_grounding(sentences, retrieved, method="lexical")
            citations = build_citations(grounding["sentences"], retrieved)
        else:
            grounding = {"sentences": [], "grounding_ratio": 0.0}
            citations = []

        reasons = []
        if not contract_verified:
            reasons.append("La evidencia contractual no es una cita literal del contrato.")
        if not sentences:
            reasons.append("La señal no contiene frases de análisis.")
        elif not grounding.get("grounding_ratio", 0.0):
            reasons.append(
                "Ninguna frase de la señal está sustentada por los chunks recuperados."
            )
        elif not citations:
            reasons.append("No se pudo construir una cita OCP para la señal.")
        elif any(not c.get("chunk_id") for c in citations):
            reasons.append("La cita OCP carece de chunk_id.")
        elif any(not c.get("indicator_code") for c in citations):
            reasons.append("La cita OCP carece de indicator_code.")

        standard_verified = (
            sentences
            and grounding.get("grounding_ratio", 0.0) > 0
            and citations
            and all(c.get("chunk_id") for c in citations)
            and all(c.get("indicator_code") for c in citations)
        )

        first_citation = next(
            (c for c in citations if c.get("chunk_id") and c.get("indicator_code")),
            {},
        )

        signals.append(
            {
                "signal_index": signal_index,
                "signal": title_line,
                "accepted": not reasons,
                "contract_evidence": {
                    "quote": contract_quote.strip(_QUOTE_CHARS),
                    "verified": contract_verified,
                },
                "standard_evidence": {
                    "quote": first_citation.get("sentence", ""),
                    "verified": standard_verified,
                    "chunk_id": first_citation.get("chunk_id"),
                    "indicator_code": first_citation.get("indicator_code"),
                },
                "rejection_reasons": reasons,
            }
        )

    accepted_count = sum(signal["accepted"] for signal in signals)
    rejected_count = len(signals) - accepted_count
    status = "PASS" if signals and rejected_count == 0 else "REVIEW_REQUIRED"
    return {
        "status": status,
        "signals": signals,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "requires_human_review": True,
        "disclaimer": HUMAN_REVIEW,
    }
