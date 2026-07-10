"""Centralized LLM factory for the web demo.

Resolves which generate_fn to use based on environment settings.
Keeps tests deterministic by exposing an explicit fake factory.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from ..config import get_settings
from .google_llm import make_fake_generate_fn, make_google_generate_fn


def resolve_generate_fn(
    override: Optional[Callable[[str, List[Dict], str], str]] = None,
) -> Callable[[str, List[Dict], str], str]:
    """Return the generate_fn to use for the analysis pipeline.

    Order of precedence:
    1. Explicit override (used by tests).
    2. Google Gemini if GOOGLE_API_KEY is set and RAG_USE_GOOGLE_LLM=1.
    3. Deterministic fake (so the API still responds with a valid dossier).
    """
    if override is not None:
        return override

    settings = get_settings()
    if google_llm_configured():
        return make_google_generate_fn(
            api_key=settings.google_api_key,
            model_name=settings.rag_gemini_model,
            use_vertex=settings.google_genai_use_vertexai,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return make_fake_generate_fn()


def google_llm_configured() -> bool:
    settings = get_settings()
    if not settings.rag_use_google_llm:
        return False
    vertex_ready = settings.google_genai_use_vertexai and settings.google_cloud_project
    return bool(settings.google_api_key or vertex_ready)