"""
RAG Core Citations — Per-sentence source attribution.

Maps each supported sentence to the chunk that best supports it,
including indicator code, name, and page range.
"""

from __future__ import annotations

from typing import Dict, List


def build_citations(
    sentence_results: List[Dict],
    chunks: List[Dict],
) -> List[Dict]:
    """
    Build citation entries for supported sentences.

    Args:
        sentence_results: list of {"text", "supported", "best_chunk_id", "best_score"}
                          from verifier.verify_grounding.
        chunks: list of chunk dicts used for retrieval/verification.

    Returns:
        List of citation dicts, one per supported sentence:
        {"sentence", "chunk_id", "indicator_code", "indicator_name",
         "page_start", "page_end"}
    """
    chunk_map = {c.get("chunk_id", ""): c for c in chunks}

    citations = []
    for sent in sentence_results:
        if not sent.get("supported"):
            continue
        chunk_id = sent.get("best_chunk_id", "")
        chunk = chunk_map.get(chunk_id, {})
        citations.append(
            {
                "sentence": sent["text"],
                "chunk_id": chunk_id,
                "indicator_code": chunk.get("indicator_code"),
                "indicator_name": chunk.get("indicator_name"),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
            }
        )
    return citations
