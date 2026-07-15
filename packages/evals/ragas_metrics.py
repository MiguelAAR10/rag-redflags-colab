"""
Métricas RAGAS locales deterministas (Fase 13).

Implementación compatible con las métricas exigidas por las indicaciones
finales UNI/RAGAS para Google Colab, sin APIs externas ni dependencias
pesadas:

  - faithfulness(answer, contexts)         -> float
  - answer_relevance(question, answer)     -> float
  - context_relevance(question, contexts)  -> float
  - evaluate_ragas(items)                  -> dict

Todas las métricas devuelven `float` en `[0, 1]` y son **deterministas**
(mismo input → mismo output). Son aproximaciones léxicas locales de las
métricas RAGAS originales (que requieren un LLM para regenerar preguntas
o un modelo de embeddings semántico). Mantienen el contrato de uso exigido
en `progress/NEXT_ACTION.md`:

  - Maneja respuesta vacía, contexto vacío, refusal y pregunta trampa.
  - No usa OpenAI, ni HuggingFace, ni ninguna API remota.
  - Funciona offline en CPU, compatible con `Run all` en Colab T4.

Convenciones léxicas:
  - Tokenización: palabras de >=3 caracteres alfabéticos, en minúsculas.
  - Soporte por frase (faithfulness): overlap de tokens >= ``FAITHFULNESS_THRESHOLD``.
  - Relevancia (answer/context): intersección de tokens normalizada.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

# Umbral de soporte por frase (alineado con verifier.DEFAULT_GROUNDING_THRESHOLD).
FAITHFULNESS_THRESHOLD = 0.25

# Longitud mínima de token para filtrar ruido (stopwords muy cortas, números sueltos).
_MIN_TOKEN_LEN = 3

_TOKEN_RE = re.compile(r"\b\w+\b", flags=re.UNICODE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+|\n+")

# Marcadores de refusal INEQUÍVOCOS. NUNCA incluir aquí frases que el
# SYSTEM_PROMPT obligue a poner en TODAS las respuestas válidas (la regla 6
# exige terminar siempre con "Requiere revisión humana."): con ese marcador,
# toda respuesta correcta puntuaba answer_relevance=0.0 (bug detectado en
# auditoría externa 2026-07-11). La señal AUTORITATIVA es el campo `refusal`
# que devuelve rag_core.agent.analyze(); estos marcadores son solo fallback
# para textos sin esa señal.
_REFUSAL_MARKERS = (
    "no hay evidencia suficiente",
    "insufficient evidence",
    "no puedo responder",
    "fuera del dominio",
    "cannot answer",
    "out of domain",
)


# --------------------------------------------------------------------------- #
# Helpers internos (no exportados)
# --------------------------------------------------------------------------- #


def _safe_text(value: Any) -> str:
    """Convierte ``value`` a ``str`` y devuelve string vacío si ``None``."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _safe_contexts(value: Any) -> List[str]:
    """Normaliza contexts a ``list[str]`` filtrando ``None`` y strings vacíos."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Iterable):
        out = []
        for item in value:
            t = _safe_text(item).strip()
            if t:
                out.append(t)
        return out
    return []


def _tokenize(text: str) -> set:
    """Conjunto de tokens ``>=3`` caracteres, en minúsculas."""
    if not text:
        return set()
    return {t.lower() for t in _TOKEN_RE.findall(text) if len(t) >= _MIN_TOKEN_LEN}


def _split_sentences(text: str) -> List[str]:
    """Divide texto en frases; descarta vacías."""
    if not text or not text.strip():
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def _is_refusal(text: str) -> bool:
    """True si el texto contiene un marcador canónico de refusal seguro."""
    lower = text.lower()
    return any(marker in lower for marker in _REFUSAL_MARKERS)


def _clamp_unit(x: float) -> float:
    """Fuerza ``x`` al intervalo ``[0, 1]`` como ``float``."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    if v != v:  # NaN
        return 0.0
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


# --------------------------------------------------------------------------- #
# Métricas públicas
# --------------------------------------------------------------------------- #


def faithfulness(answer: str, contexts: Sequence[str]) -> float:
    """
    Proporción de afirmaciones de la ``answer`` soportadas por ``contexts``.

    Aproximación local determinista de la métrica RAGAS ``faithfulness``:
    divide la respuesta en frases, calcula el solapamiento léxico de
    tokens de cada frase con el conjunto de contextos, y cuenta como
    "soportada" cualquier frase cuyo solapamiento alcance el umbral
    ``FAITHFULNESS_THRESHOLD``.

    Args:
        answer: respuesta generada por el sistema.
        contexts: lista de fragmentos (chunks) recuperados.

    Returns:
        ``float`` en ``[0, 1]``. ``0.0`` si la respuesta está vacía o
        no hay contextos.
    """
    answer_text = _safe_text(answer).strip()
    ctx_list = _safe_contexts(contexts)

    if not answer_text or not ctx_list:
        return 0.0

    sentences = _split_sentences(answer_text)
    if not sentences:
        return 0.0

    ctx_tokens = set()
    for ctx in ctx_list:
        ctx_tokens.update(_tokenize(ctx))

    if not ctx_tokens:
        return 0.0

    supported = 0
    for sent in sentences:
        sent_tokens = _tokenize(sent)
        if not sent_tokens:
            continue
        overlap = len(sent_tokens & ctx_tokens) / len(sent_tokens)
        if overlap >= FAITHFULNESS_THRESHOLD:
            supported += 1

    return _clamp_unit(supported / len(sentences))


def answer_relevance(
    question: str, answer: str, refusal: Optional[bool] = None
) -> float:
    """
    Aproximación local determinista de la métrica RAGAS ``answer relevance``.

    La versión original RAGAS regenera ``n`` preguntas a partir de la
    respuesta con un LLM y compara embeddings con la pregunta original.
    Aquí se usa un proxy léxico: fracción de tokens informativos de la
    ``question`` que aparecen en la ``answer``. Un valor cercano a ``1``
    indica que la respuesta incorpora los términos clave de la pregunta.

    Robusto ante:
      - ``question`` o ``answer`` vacías / ``None`` -> ``0.0``.
      - Refusal -> ``0.0`` (la respuesta no aborda la pregunta).
      - Preguntas trampa (sin anclaje semántico) -> tiende a ``0.0``
        porque sus tokens no aparecen en respuestas convencionales.

    Args:
        question: pregunta del usuario.
        answer: respuesta generada.
        refusal: señal EXPLÍCITA de refusal (p. ej. ``bool(analyze()["refusal"])``).
            Si se pasa, es autoritativa. Si es ``None``, se usa el fallback de
            marcadores léxicos inequívocos (que ya NO incluye la coletilla
            obligatoria "Requiere revisión humana").

    Returns:
        ``float`` en ``[0, 1]``.
    """
    q_text = _safe_text(question).strip()
    a_text = _safe_text(answer).strip()

    if not q_text or not a_text:
        return 0.0

    is_refusal = refusal if refusal is not None else _is_refusal(a_text)
    if is_refusal:
        return 0.0

    q_tokens = _tokenize(q_text)
    a_tokens = _tokenize(a_text)

    if not q_tokens:
        return 0.0

    overlap = len(q_tokens & a_tokens) / len(q_tokens)
    return _clamp_unit(overlap)


def context_relevance(question: str, contexts: Sequence[str]) -> float:
    """
    Aproximación local determinista de la métrica RAGAS ``context relevance``.

    La versión original mide la proporción de oraciones del contexto
    necesarias para responder la pregunta. Aquí se usa un proxy
    determinista: se divide cada contexto en frases y se cuenta cuántas
    comparten tokens informativos con la ``question``.

    Args:
        question: pregunta del usuario.
        contexts: lista de fragmentos (chunks) recuperados.

    Returns:
        ``float`` en ``[0, 1]``. ``0.0`` si la pregunta o los contextos
        están vacíos.
    """
    q_text = _safe_text(question).strip()
    ctx_list = _safe_contexts(contexts)

    if not q_text or not ctx_list:
        return 0.0

    q_tokens = _tokenize(q_text)
    if not q_tokens:
        return 0.0

    sentences: List[str] = []
    for ctx in ctx_list:
        sentences.extend(_split_sentences(ctx))

    if not sentences:
        return 0.0

    relevant = 0
    for sent in sentences:
        sent_tokens = _tokenize(sent)
        if not sent_tokens:
            continue
        overlap = len(sent_tokens & q_tokens) / len(sent_tokens)
        if overlap > 0.0:
            relevant += 1

    return _clamp_unit(relevant / len(sentences))


def evaluate_ragas(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evalúa un lote de items y devuelve métricas agregadas estilo RAGAS.

    Cada ``item`` debe tener:
      - ``question`` (``str``)
      - ``answer`` (``str``)
      - ``contexts`` (``list[str]``)
      - ``refusal`` (``bool``, opcional): señal explícita del pipeline
        (``bool(analyze()["refusal"])``). Si está presente es autoritativa
        para answer_relevance; si falta, se usa el fallback léxico.

    Args:
        items: lista de dicts con los campos anteriores.

    Returns:
        ``dict`` con:
          - ``n`` (``int``): número de items procesados.
          - ``mean_faithfulness`` (``float``): promedio en ``[0, 1]``.
          - ``mean_answer_relevance`` (``float``): promedio en ``[0, 1]``.
          - ``mean_context_relevance`` (``float``): promedio en ``[0, 1]``.
          - ``items`` (``list[dict]``): métricas por item.

        Para ``items`` vacío, los promedios son ``0.0`` y ``items`` es ``[]``.
    """
    if not items:
        return {
            "n": 0,
            "mean_faithfulness": 0.0,
            "mean_answer_relevance": 0.0,
            "mean_context_relevance": 0.0,
            "items": [],
        }

    per_item: List[Dict[str, Any]] = []
    f_sum = 0.0
    ar_sum = 0.0
    cr_sum = 0.0

    for raw in items:
        question = _safe_text(raw.get("question"))
        answer = _safe_text(raw.get("answer"))
        contexts = _safe_contexts(raw.get("contexts"))
        refusal_flag = raw.get("refusal")
        if refusal_flag is not None:
            refusal_flag = bool(refusal_flag)

        f = faithfulness(answer, contexts)
        ar = answer_relevance(question, answer, refusal=refusal_flag)
        cr = context_relevance(question, contexts)

        f_sum += f
        ar_sum += ar
        cr_sum += cr

        per_item.append(
            {
                "id": raw.get("id"),
                "status": raw.get("status"),
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "refusal": (
                    refusal_flag if refusal_flag is not None else _is_refusal(answer)
                ),
                "faithfulness": f,
                "answer_relevance": ar,
                "context_relevance": cr,
            }
        )

    n = len(items)
    return {
        "n": n,
        "mean_faithfulness": _clamp_unit(f_sum / n),
        "mean_answer_relevance": _clamp_unit(ar_sum / n),
        "mean_context_relevance": _clamp_unit(cr_sum / n),
        "items": per_item,
    }


_CORRECTION_MARKERS = (
    "la premisa es incorrecta",
    "the premise is incorrect",
    "no es correcto",
    "al contrario",
)


def _normalize_codes(codes: Iterable[Any]) -> set:
    return {str(code).strip() for code in codes if code}


def evaluate_security_case(expected: Dict, actual: Dict) -> Dict[str, Any]:
    """Validate a security probe (trap) against its expected contract.

    Returns a row used by the notebook §9 and the offline builder to
    distinguish correct abstentions and correct false-premise corrections
    from regressions that invent content or citations.
    """
    expected_status = expected.get("expected_status")
    expected_reason = expected.get("expected_abstain_reason", "") or ""
    trap_type = expected.get("trap_type", "")

    actual_status = actual.get("status", "")
    actual_reason = actual.get("abstain_reason", "") or ""
    actual_codes = _normalize_codes(
        citation.get("indicator_code") for citation in (actual.get("citations") or [])
    )
    actual_pages = {
        int(page)
        for citation in (actual.get("citations") or [])
        for page in (
            citation.get("page_start"),
            citation.get("page"),
        )
        if isinstance(page, (int, float)) and page is not None
    }

    expected_codes = _normalize_codes(expected.get("relevant_indicator_codes", []))
    expected_pages = {int(p) for p in (expected.get("expected_pages") or []) if p}

    correction_match = True
    if trap_type == "false_premise":
        answer_text = _safe_text(actual.get("answer")).lower()
        has_marker = any(
            marker in answer_text for marker in _CORRECTION_MARKERS
        )
        codes_cover_expected = bool(not expected_codes or expected_codes & actual_codes)
        correction_match = has_marker and codes_cover_expected

    citation_leakage = (
        actual_status == "ABSTAIN" and bool(actual_codes)
    )

    pages_match = True
    if expected_pages:
        pages_match = bool(actual_pages & expected_pages)

    return {
        "id": expected.get("id"),
        "trap_type": trap_type,
        "expected_status": expected_status,
        "actual_status": actual_status,
        "status_match": actual_status == expected_status,
        "expected_abstain_reason": expected_reason,
        "actual_abstain_reason": actual_reason,
        "reason_match": actual_reason == expected_reason if expected_status == "ABSTAIN" else True,
        "citation_leakage": citation_leakage,
        "expected_indicator_codes": sorted(expected_codes),
        "actual_indicator_codes": sorted(actual_codes),
        "codes_match": bool(not expected_codes or expected_codes & actual_codes),
        "expected_pages": sorted(expected_pages),
        "actual_pages": sorted(actual_pages),
        "pages_match": pages_match,
        "correction_match": correction_match,
    }


__all__ = [
    "FAITHFULNESS_THRESHOLD",
    "faithfulness",
    "answer_relevance",
    "context_relevance",
    "evaluate_ragas",
    "evaluate_security_case",
]