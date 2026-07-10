"""generate_fn adapter for Google Gemini.

The signature mirrors what packages.rag_core.agent.analyze expects:

    fn(query: str, chunks: list[dict], system_prompt: str) -> str

In tests we inject a fake determinista via the LLMFactory, so this
module is exercised only when GOOGLE_API_KEY is set in the env.
"""

from __future__ import annotations

import logging
import os
from typing import Callable, List, Dict, Optional

logger = logging.getLogger(__name__)


def _build_user_prompt(query: str, chunks: List[Dict]) -> str:
    """Compose the user prompt for Gemini from query + retrieved chunks."""
    context_lines = []
    for c in chunks:
        indicator = c.get("indicator_name") or "Desconocida"
        code = c.get("indicator_code") or "N/A"
        pages = f"p.{c.get('page_start', '?')}-{c.get('page_end', '?')}"
        text = (c.get("text") or "").strip()
        context_lines.append(
            f"[Fuente: {indicator} ({code}, {pages})] {text}"
        )
    context = "\n\n".join(context_lines)
    return (
        f"Fragmento a evaluar:\n\"\"\"\n{query}\n\"\"\"\n\n"
        f"Evidencia recuperada (guía OCP/OCDS):\n{context}\n\n"
        "Genera el análisis con el FORMATO obligatorio."
    )


def make_google_generate_fn(
    *,
    api_key: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
    max_output_tokens: int = 1024,
    temperature: float = 0.0,
) -> Callable[[str, List[Dict], str], str]:
    """Build a generate_fn backed by Google Gemini.

    Falls back to a deterministic stub if google-generativeai is not
    installed or the API key is missing. The stub lets the API surface
    a clear "API no configurada" error message during analysis.
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")

    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        logger.warning("google-generativeai no instalado; usando stub.")
        return _stub_generate_fn(reason="google-generativeai no instalado")

    if not api_key:
        logger.warning("GOOGLE_API_KEY no configurada; usando stub.")
        return _stub_generate_fn(reason="GOOGLE_API_KEY no configurada")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    def _generate(query: str, chunks: List[Dict], system_prompt: str) -> str:
        user_prompt = _build_user_prompt(query, chunks)
        try:
            response = model.generate_content(
                [
                    {"role": "user", "parts": [system_prompt]},
                    {"role": "model", "parts": ["Entendido."]},
                    {"role": "user", "parts": [user_prompt]},
                ],
                generation_config={
                    "max_output_tokens": max_output_tokens,
                    "temperature": temperature,
                },
            )
        except Exception as exc:
            logger.warning("Gemini falló: %s", exc)
            return _REFUSAL_BY_API_ERROR.format(reason=str(exc))

        text = getattr(response, "text", None)
        if not text:
            return _REFUSAL_BY_API_ERROR.format(reason="respuesta vacía")
        return text.strip()

    return _generate


def _stub_generate_fn(reason: str) -> Callable[[str, List[Dict], str], str]:
    def _generate(query: str, chunks: List[Dict], system_prompt: str) -> str:
        return _REFUSAL_BY_API_ERROR.format(reason=reason)

    return _generate


_REFUSAL_BY_API_ERROR = (
    "No hay evidencia suficiente en los documentos recuperados para emitir "
    "observaciones fundamentadas. El servicio de generación por API no está "
    "disponible (motivo: {reason}). Requiere revisión humana."
)


def make_fake_generate_fn(
    fixed_answer: Optional[str] = None,
) -> Callable[[str, List[Dict], str], str]:
    """A deterministic generate_fn for tests and offline demos."""
    answer = fixed_answer or _DEFAULT_FAKE_ANSWER

    def _generate(query: str, chunks: List[Dict], system_prompt: str) -> str:
        return answer

    return _generate


_DEFAULT_FAKE_ANSWER = (
    "### Evaluación preliminar\n"
    "Riesgo general: Medio\n\n"
    "### Señales de riesgo identificadas\n"
    "1. Señal: Plazo de entrega muy corto respecto al alcance\n"
    "   - Evidencia del fragmento: 'El plazo de entrega es de 5 días hábiles.'\n"
    "   - Por qué importa: Plazos cortos pueden reducir la competencia.\n"
    "   - Sustento recuperado: (Indicador: Bidding period too short, R010, p.10-12)\n\n"
    "### Qué faltaría validar\n- Cronograma detallado del proceso.\n\n"
    "### Conclusión\n"
    "No se determina corrupción; son señales de riesgo potenciales. "
    "Requiere revisión humana."
)