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
from types import SimpleNamespace
from typing import Any, Callable, List, Dict, Optional, Tuple

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
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


def _import_google_genai() -> Tuple[Any, Any]:
    """Import google-genai SDK; extracted so tests can patch it."""
    from google import genai  # type: ignore
    from google.genai import types as genai_types  # type: ignore
    return genai, genai_types


def _build_generation_config(
    system_instruction: str,
    max_output_tokens: int,
    temperature: float,
    genai_types: Any,
) -> Any:
    """Build a config object compatible with the injected client."""
    if genai_types is not None:
        return genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            # Sin thinking: salida de auditor determinista; evita que
            # los tokens de razonamiento consuman max_output_tokens.
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
        )
    return SimpleNamespace(
        system_instruction=system_instruction,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )


def make_google_generate_fn(
    *,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
    max_output_tokens: int = 2048,
    temperature: float = 0.0,
    use_vertex: Optional[bool] = None,
    project: str = "",
    location: str = "",
    client: Optional[Any] = None,
    strict: bool = False,
) -> Callable[[str, List[Dict], str], str]:
    """Build a generate_fn backed by Google Gemini (SDK google-genai).

    Two auth routes:
    - Vertex AI (ADC / service account): billing via the GCP project;
      no API key needed. Selected with use_vertex or
      GOOGLE_GENAI_USE_VERTEXAI env.
    - API key (AI Studio): GOOGLE_API_KEY / GEMINI_API_KEY.

    Parameters
    ----------
    client:
        Optional pre-built google-genai client (or fake). When provided,
        auth discovery is skipped and this client is used directly.
    strict:
        If True, any SDK/import error, missing auth, API exception or empty
        response raises a controlled RuntimeError instead of falling back to
        the safe stub. Credentials are never included in error messages.

    Falls back to a deterministic stub if google-genai is not installed
    or no auth route is configured (and strict=False).
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

    genai_types: Any = None
    resolved_client = client
    if resolved_client is None:
        try:
            genai, genai_types = _import_google_genai()
        except Exception:
            if strict:
                raise RuntimeError(
                    "El SDK de Google (google-genai) no está disponible. "
                    "Requiere revisión humana."
                )
            logger.warning("google-genai no instalado; usando stub.")
            return _stub_generate_fn(reason="google-genai no instalado")

        if use_vertex and not project:
            if strict:
                raise RuntimeError(
                    "Vertex AI requiere GOOGLE_CLOUD_PROJECT para usar Gemini. "
                    "Requiere revisión humana."
                )
            logger.warning("Vertex AI configurado sin proyecto; usando stub.")
            return _stub_generate_fn(reason="Vertex AI sin GOOGLE_CLOUD_PROJECT")

        if use_vertex and project:
            resolved_client = genai.Client(
                vertexai=True, project=project, location=location
            )
        elif api_key:
            resolved_client = genai.Client(api_key=api_key)
        elif strict:
            raise RuntimeError(
                "Faltan credenciales de autenticación para Gemini "
                "(API key o configuración Vertex). Requiere revisión humana."
            )
        else:
            logger.warning("Sin auth Gemini (ni Vertex ni API key); usando stub.")
            return _stub_generate_fn(reason="GOOGLE_API_KEY/Vertex no configurados")

    def _generate(query: str, chunks: List[Dict], system_prompt: str) -> str:
        user_prompt = _build_user_prompt(query, chunks)
        config = _build_generation_config(
            system_instruction=system_prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            genai_types=genai_types,
        )
        try:
            response = resolved_client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
        except Exception as exc:
            if strict:
                logger.warning("Gemini falló en modo estricto: %s", exc)
                raise RuntimeError(
                    "Error al llamar a la API de Gemini. Requiere revisión humana."
                )
            logger.warning("Gemini falló: %s", exc)
            return _REFUSAL_BY_API_ERROR.format(reason=str(exc))

        text = getattr(response, "text", None)
        if not text or not str(text).strip():
            if strict:
                raise RuntimeError(
                    "La API de Gemini devolvió una respuesta vacía. "
                    "Requiere revisión humana."
                )
            return _REFUSAL_BY_API_ERROR.format(reason="respuesta vacía")
        return str(text).strip()

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
