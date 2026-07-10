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
_REFUSAL_MARKERS = (
    "no hay evidencia suficiente",
    "insufficient evidence",
    "requiere revisión humana",
    "requires human review",
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


def answer_relevance(question: str, answer: str) -> float:
    """
    Aproximación local determinista de la métrica RAGAS ``answer relevance``.

    La versión original RAGAS regenera ``n`` preguntas a partir de la
    respuesta con un LLM y compara embeddings con la pregunta original.
    Aquí se usa un proxy léxico: fracción de tokens informativos de la
    ``question`` que aparecen en la ``answer``. Un valor cercano a ``1``
    indica que la respuesta incorpora los términos clave de la pregunta.

    Robusto ante:
      - ``question`` o ``answer`` vacías / ``None`` -> ``0.0``.
      - Refusal seguro -> ``0.0`` (la respuesta no aborda la pregunta).
      - Preguntas trampa (sin anclaje semántico) -> tiende a ``0.0``
        porque sus tokens no aparecen en respuestas convencionales.

    Args:
        question: pregunta del usuario.
        answer: respuesta generada.

    Returns:
        ``float`` en ``[0, 1]``.
    """
    q_text = _safe_text(question).strip()
    a_text = _safe_text(answer).strip()

    if not q_text or not a_text:
        return 0.0

    if _is_refusal(a_text):
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

        f = faithfulness(answer, contexts)
        ar = answer_relevance(question, answer)
        cr = context_relevance(question, contexts)

        f_sum += f
        ar_sum += ar
        cr_sum += cr

        per_item.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
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


__all__ = [
    "FAITHFULNESS_THRESHOLD",
    "faithfulness",
    "answer_relevance",
    "context_relevance",
    "evaluate_ragas",
]