"""AnalysisAgent — orchestrates retrieval + generation + grounding for the
TDR text using the existing RAG core.

This agent does NOT re-implement the RAG core. It calls
`packages.rag_core.agent.analyze` with an injectable `generate_fn` so
the deployed web demo can run on Google Gemini (no GPU) while tests
run with a deterministic fake.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def _ensure_repo_root_on_path() -> None:
    """Make sure `packages.rag_core.agent` is importable when this
    module is run from a working dir that does not include the repo
    root (e.g. when uvicorn is started from apps/api).
    """
    repo_root = Path(__file__).resolve().parents[4]
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


@dataclass
class AnalysisOutput:
    answer: str = ""
    sentences: List[Dict] = field(default_factory=list)
    citations: List[Dict] = field(default_factory=list)
    grounding_ratio: float = 0.0
    refusal: str = ""
    retrieved: List[Dict] = field(default_factory=list)
    chunks_used: int = 0
    citations_count: int = 0
    supported_sentences: int = 0
    total_sentences: int = 0
    model_name: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def run_analysis(
    tdr_text: str,
    generate_fn: Callable[[str, List[Dict], str], str],
    *,
    grounding_threshold: float = 0.25,
    grounding_method: str = "lexical",
    retrieved_chunks: Optional[List[Dict]] = None,
    model_name: str = "",
) -> AnalysisOutput:
    """Run the RAG analysis on the TDR text.

    Args:
        tdr_text: full TDR text or representative fragment.
        generate_fn: LLM function with signature
            (query, chunks, system_prompt) -> str.
        grounding_threshold: minimum grounding ratio to consider
            the response supported.
        grounding_method: 'lexical' (default, determinista para tests) o
            'gemini' (semántico multilingüe, producción).
        retrieved_chunks: optional pre-computed chunks (for tests).
        model_name: human-readable name of the LLM, recorded in output.
    """
    _ensure_repo_root_on_path()
    from packages.rag_core.agent import analyze

    query = _build_query(tdr_text)
    result = analyze(
        query=query,
        generate_fn=generate_fn,
        retrieved_chunks=retrieved_chunks,
        grounding_method=grounding_method,
        grounding_threshold=grounding_threshold,
    )

    sentences = result.get("sentences", []) or []
    citations = result.get("citations", []) or []
    retrieved = result.get("retrieved", []) or []

    return AnalysisOutput(
        answer=result.get("answer", ""),
        sentences=[
            {"text": s.get("text", ""), "supported": bool(s.get("supported"))}
            for s in sentences
        ],
        citations=citations,
        grounding_ratio=float(result.get("grounding_ratio", 0.0)),
        refusal=result.get("refusal", "") or "",
        retrieved=retrieved,
        chunks_used=len(retrieved),
        citations_count=len(citations),
        supported_sentences=sum(1 for s in sentences if s.get("supported")),
        total_sentences=len(sentences),
        model_name=model_name,
    )


def _build_query(tdr_text: str) -> str:
    """Trim the TDR text to a query-friendly length.

    The RAG pipeline only needs a representative fragment to drive
    retrieval. We cap at 8k characters to keep generation stable.
    """
    if len(tdr_text) <= 8000:
        return tdr_text
    head = tdr_text[:6000]
    tail = tdr_text[-2000:]
    return head + "\n\n[...]\n\n" + tail


def safe_json_dumps(payload: Dict) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)