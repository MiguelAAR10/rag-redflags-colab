"""generate_fn adapter for Google Gemini.

The signature mirrors what packages.rag_core.agent.analyze expects:

    fn(query: str, chunks: list[dict], system_prompt: str) -> str

In tests we inject a fake determinista via the LLMFactory, so this
module is exercised only when GOOGLE_API_KEY is set in the env.

Uses the google-genai SDK (successor of the deprecated
google-generativeai package).
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


def _truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def make_google_generate_fn(
    *,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
    max_output_tokens: int = 2048,
    temperature: float = 0.0,
    use_vertex: Optional[bool] = None,
    project: str = "",
    location: str = "",
) -> Callable[[str, List[Dict], str], str]:
    """Build a generate_fn backed by Google Gemini (SDK google-genai).

    Two auth routes:
    - Vertex AI (ADC / service account): billing via the GCP project;
      no API key needed. Selected with use_vertex or
      GOOGLE_GENAI_USE_VERTEXAI env.
    - API key (AI Studio): GOOGLE_API_KEY / GEMINI_API_KEY.

    Falls back to a deterministic stub if google-genai is not installed
    or no auth route is configured.
    """
    api_key = (
        api_key
        or os.environ.get("GOOGLE_API_KEY", "")
        or os.environ.get("GEMINI_API_KEY", "")
    )
    if use_vertex is None:
        use_vertex = _truthy(os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", ""))
    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    location = location or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    try:
        from google import genai  # type: ignore
        from google.genai import types as genai_types  # type: ignore
    except Exception:
        logger.warning("google-genai no instalado; usando stub.")
        return _stub_generate_fn(reason="google-genai no instalado")

    if use_vertex and project:
        client = genai.Client(vertexai=True, project=project, location=location)
    elif api_key:
        client = genai.Client(api_key=api_key)
    else:
        logger.warning("Sin auth Gemini (ni Vertex ni API key); usando stub.")
        return _stub_generate_fn(reason="GOOGLE_API_KEY/Vertex no configurados")

    def _generate(query: str, chunks: List[Dict], system_prompt: str) -> str:
        user_prompt = _build_user_prompt(query, chunks)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                    # Sin thinking: salida de auditor determinista; evita que
                    # los tokens de razonamiento consuman max_output_tokens.
                    thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
                ),
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