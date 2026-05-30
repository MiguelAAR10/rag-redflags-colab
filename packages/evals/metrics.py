"""
Evaluación cuantitativa — Recall@k, Precision@k, Grounding Ratio.

Usa un gold set (goldset.jsonl) con queries y sus indicator_codes esperados.
El retrieval score se calcula comparando los indicator_codes recuperados
contra los relevantes del gold set.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDSET = REPO_ROOT / "data" / "eval" / "goldset.jsonl"


def load_goldset(path: Optional[Path] = None) -> List[Dict]:
    """Carga el gold set desde JSONL."""
    if path is None:
        path = DEFAULT_GOLDSET
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def recall_at_k(
    retrieved_codes: List[str],
    relevant_codes: List[str],
    k: int,
) -> float:
    """
    Recall@k = |relevantes en top-k| / |relevantes totales|.
    """
    if not relevant_codes:
        return 1.0
    pred = set(retrieved_codes[:k])
    rel = set(relevant_codes)
    return len(pred & rel) / len(rel)


def precision_at_k(
    retrieved_codes: List[str],
    relevant_codes: List[str],
    k: int,
) -> float:
    """
    Precision@k = |relevantes en top-k| / k.
    """
    if k <= 0:
        return 0.0
    pred = set(retrieved_codes[:k])
    rel = set(relevant_codes)
    return len(pred & rel) / k


def mean_grounding_ratio(results: List[Dict]) -> float:
    """
    Average grounding_ratio across results.
    Each result dict must have 'grounding_ratio' key.
    """
    if not results:
        return 0.0
    ratios = [r.get("grounding_ratio", 0.0) for r in results]
    return sum(ratios) / len(ratios)


def evaluate_on_goldset(
    gold_items: List[Dict],
    retrieved_items: List[Dict],
    ks: List[int] = None,
) -> Dict:
    """
    Compute Recall@k and Precision@k for each k on the full gold set.

    Args:
        gold_items: list of gold dicts with 'relevant_indicator_codes'.
        retrieved_items: list of result dicts with 'retrieved_indicator_codes'
            (same order as gold_items).
        ks: list of k values (default [3, 5, 10]).

    Returns:
        Dict with recall and precision per k, plus mean grounding_ratio.
    """
    if ks is None:
        ks = [3, 5, 10]

    recall = {}
    precision = {}
    for k in ks:
        recalls = []
        precs = []
        for gold, ret in zip(gold_items, retrieved_items):
            rel = gold.get("relevant_indicator_codes", [])
            ret_codes = ret.get("retrieved_indicator_codes", [])
            recalls.append(recall_at_k(ret_codes, rel, k))
            precs.append(precision_at_k(ret_codes, rel, k))
        recall[k] = round(sum(recalls) / len(recalls), 4) if recalls else 0.0
        precision[k] = round(sum(precs) / len(precs), 4) if precs else 0.0

    return {
        "recall_at_k": recall,
        "precision_at_k": precision,
        "mean_grounding_ratio": round(mean_grounding_ratio(retrieved_items), 4),
    }


def compare_methods(
    method_results: Dict[str, List[Dict]],
    gold_items: List[Dict],
    ks: List[int] = None,
) -> Dict:
    """
    Compare multiple retrieval methods (FAISS, hybrid, rerank) against gold set.

    Args:
        method_results: {"method_name": [result_dicts_per_query], ...}
        gold_items: gold set items.
        ks: k values.

    Returns:
        Nested dict with metrics per method.
    """
    if ks is None:
        ks = [3, 5, 10]

    comparison = {}
    for method, results in method_results.items():
        comparison[method] = evaluate_on_goldset(gold_items, results, ks)
    return comparison


def _try_rouge_bleu(predictions: List[str], references: List[str]) -> Dict:
    """
    BONUS: compute ROUGE-L and BLEU scores. Returns empty dict if deps missing.
    """
    try:
        from rouge_score import rouge_scorer
    except Exception:
        scorer = None
    else:
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

    rouge_scores = []
    bleu_scores = []
    bleu_available = False

    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

        smooth = SmoothingFunction().method1
        bleu_available = True
    except Exception:
        pass

    for pred, ref in zip(predictions, references):
        if scorer:
            r = scorer.score(ref, pred)
            rouge_scores.append(r["rougeL"].fmeasure)
        if bleu_available and ref.strip():
            try:
                b = sentence_bleu(
                    [ref.split()], pred.split(), smoothing_function=smooth
                )
                bleu_scores.append(b)
            except Exception:
                pass

    result = {}
    if rouge_scores:
        result["rougeL"] = round(sum(rouge_scores) / len(rouge_scores), 4)
    if bleu_scores:
        result["bleu"] = round(sum(bleu_scores) / len(bleu_scores), 4)

    return result


if __name__ == "__main__":
    items = load_goldset()
    print(f"Gold set cargado: {len(items)} items")
    for i, item in enumerate(items):
        print(f"  {i + 1}. {item['query'][:70]}... -> {item['relevant_indicator_codes']}")
