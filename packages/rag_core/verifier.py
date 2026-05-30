"""
RAG Core Verifier — Grounding check for LLM responses.

Splits a generated answer into sentences and checks each one against
retrieved chunks using lexical overlap (deterministic) or embeddings.
Returns grounding_ratio and flags per sentence.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_GROUNDING_THRESHOLD = 0.25


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences on ., !, ?, ;, newlines.
    Filters empty sentences.
    """
    raw = re.split(r"(?<=[.!?;])\s+|\n+", text)
    return [s.strip() for s in raw if s.strip()]


def _lexical_similarity(sentence: str, chunk_text: str) -> float:
    """Token overlap: ratio of sentence tokens found in chunk text."""
    tokens_sent = set(re.findall(r"\b\w{3,}\b", sentence.lower()))
    tokens_chunk = set(re.findall(r"\b\w{3,}\b", chunk_text.lower()))
    if not tokens_sent:
        return 0.0
    overlap = len(tokens_sent & tokens_chunk)
    return overlap / len(tokens_sent)


def _embedding_similarity(sentence: str, chunk_text: str) -> float:
    """Cosine similarity using sentence-transformers embeddings."""
    from packages.rag_core.embeddings import embed_texts

    vecs = embed_texts([sentence, chunk_text], show_progress=False)
    s_vec = vecs[0:1]
    c_vec = vecs[1:2]
    return float((s_vec @ c_vec.T)[0, 0])


def verify_grounding(
    sentences: List[str],
    chunks: List[Dict],
    threshold: float = DEFAULT_GROUNDING_THRESHOLD,
    method: str = "lexical",
) -> Dict:
    """
    Check each sentence against retrieved chunks for factual support.

    Args:
        sentences: list of sentence strings.
        chunks: list of chunk dicts with at least 'text' and 'chunk_id'.
        threshold: minimum similarity score to consider a sentence supported.
        method: 'lexical' (deterministic, fast) or 'embedding' (semantic).

    Returns:
        {
            "sentences": [
                {"text": "...", "supported": bool, "best_chunk_id": str|None,
                 "best_score": float},
                ...
            ],
            "grounding_ratio": float,
            "passed": bool,
        }
    """
    if method not in ("lexical", "embedding"):
        raise ValueError(f"method must be 'lexical' or 'embedding', got {method!r}")

    sim_fn = _embedding_similarity if method == "embedding" else _lexical_similarity

    supported_count = 0
    sentence_results = []

    for sent in sentences:
        best_score = 0.0
        best_chunk_id = None

        for chunk in chunks:
            try:
                score = sim_fn(sent, chunk.get("text", ""))
            except Exception:
                score = 0.0
            if score > best_score:
                best_score = score
                best_chunk_id = chunk.get("chunk_id")

        is_supported = best_score >= threshold
        if is_supported:
            supported_count += 1

        sentence_results.append(
            {
                "text": sent,
                "supported": is_supported,
                "best_chunk_id": best_chunk_id,
                "best_score": round(float(best_score), 4),
            }
        )

    grounding_ratio = supported_count / len(sentences) if sentences else 0.0

    return {
        "sentences": sentence_results,
        "grounding_ratio": round(grounding_ratio, 4),
        "passed": grounding_ratio >= threshold,
    }


def refusal_check(
    grounding_result: Dict,
    min_ratio: float = DEFAULT_GROUNDING_THRESHOLD,
) -> str:
    """
    If grounding ratio is below min_ratio, return refusal message.
    Otherwise return empty string (meaning: pass, no refusal).
    """
    if grounding_result["grounding_ratio"] < min_ratio:
        return (
            "No hay evidencia suficiente en los documentos recuperados "
            "para emitir observaciones fundamentadas. "
            "Requiere revisión humana."
        )
    return ""
