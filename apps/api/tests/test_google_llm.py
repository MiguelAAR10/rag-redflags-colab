"""Tests for the Google Gemini generate_fn adapter."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from app.adapters.google_llm import make_google_generate_fn


class FakeModels:
    def __init__(self, client: "FakeGenaiClient") -> None:
        self._client = client

    def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config: Any,
    ) -> Any:
        return self._client._generate_content(model, contents, config)


class FakeGenaiClient:
    """In-memory google-genai client that records every generation call."""

    def __init__(self, response_text: str = "Respuesta determinista de prueba.") -> None:
        self.models = FakeModels(self)
        self.calls: List[Dict[str, Any]] = []
        self.response_text = response_text
        self.raise_on_call: Exception | None = None

    def _generate_content(self, model: str, contents: str, config: Any) -> Any:
        self.calls.append(
            {
                "model": model,
                "contents": contents,
                "config": config,
            }
        )
        if self.raise_on_call is not None:
            raise self.raise_on_call
        return SimpleNamespace(text=self.response_text)


def test_fake_client_is_used_and_captures_generation_config() -> None:
    fake = FakeGenaiClient()
    generate = make_google_generate_fn(
        client=fake,
        model_name="gemini-2.5-flash",
        temperature=0.3,
        max_output_tokens=1024,
        strict=True,
    )

    result = generate("query", [], "system")

    assert result == fake.response_text
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["model"] == "gemini-2.5-flash"
    assert call["config"].temperature == 0.3
    assert call["config"].max_output_tokens == 1024


def test_default_model_is_gemini_2_5_flash() -> None:
    fake = FakeGenaiClient()
    generate = make_google_generate_fn(client=fake, strict=True)

    generate("query", [], "system")

    assert fake.calls[0]["model"] == "gemini-2.5-flash"


def test_temperature_is_configurable() -> None:
    fake = FakeGenaiClient()
    generate = make_google_generate_fn(
        client=fake,
        temperature=0.7,
        strict=True,
    )

    generate("query", [], "system")

    assert fake.calls[0]["config"].temperature == 0.7


def test_valid_response_is_returned() -> None:
    fake = FakeGenaiClient(response_text="Respuesta válida.")
    generate = make_google_generate_fn(client=fake, strict=True)

    result = generate("query", [], "system")

    assert result == "Respuesta válida."


def test_empty_response_raises_runtime_error_in_strict_mode() -> None:
    fake = FakeGenaiClient(response_text="")
    generate = make_google_generate_fn(client=fake, strict=True)

    with pytest.raises(RuntimeError) as exc_info:
        generate("query", [], "system")

    assert "respuesta vacía" in str(exc_info.value).lower()


def test_api_exception_raises_runtime_error_in_strict_mode() -> None:
    fake = FakeGenaiClient()
    fake.raise_on_call = RuntimeError("boom")
    generate = make_google_generate_fn(client=fake, strict=True)

    with pytest.raises(RuntimeError) as exc_info:
        generate("query", [], "system")

    message = str(exc_info.value)
    assert "gemini" in message.lower() or "api" in message.lower()
    assert "boom" not in message  # original exception text must not leak


def test_missing_auth_raises_runtime_error_in_strict_mode() -> None:
    with pytest.raises(RuntimeError) as exc_info:
        make_google_generate_fn(
            api_key="",
            use_vertex=False,
            strict=True,
        )

    assert "auth" in str(exc_info.value).lower() or "credenciales" in str(exc_info.value).lower()


def test_sdk_import_failure_raises_runtime_error_in_strict_mode() -> None:
    with patch(
        "app.adapters.google_llm._import_google_genai",
        side_effect=ImportError("No module named 'google'"),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            make_google_generate_fn(strict=True)

    assert "sdk" in str(exc_info.value).lower() or "google-genai" in str(exc_info.value).lower()


def test_non_strict_mode_keeps_stub_fallback_when_no_auth() -> None:
    generate = make_google_generate_fn(
        api_key="",
        use_vertex=False,
        strict=False,
    )

    result = generate("query", [], "system")

    assert "no hay evidencia suficiente" in result.lower()


def test_whitespace_only_response_treated_as_empty_in_strict_mode() -> None:
    fake = FakeGenaiClient(response_text="   \n\t  ")
    generate = make_google_generate_fn(client=fake, strict=True)

    with pytest.raises(RuntimeError) as exc_info:
        generate("query", [], "system")

    assert "respuesta vacía" in str(exc_info.value).lower()


def test_whitespace_only_response_treated_as_empty_in_non_strict_mode() -> None:
    fake = FakeGenaiClient(response_text="   \n\t  ")
    generate = make_google_generate_fn(client=fake, strict=False)

    result = generate("query", [], "system")

    assert "no hay evidencia suficiente" in result.lower()


def test_injected_client_does_not_require_google_genai_sdk() -> None:
    fake = FakeGenaiClient(response_text="Funciona sin SDK.")
    with patch(
        "app.adapters.google_llm._import_google_genai",
        side_effect=ImportError("No module named 'google'"),
    ):
        generate = make_google_generate_fn(
            client=fake,
            model_name="gemini-test",
            temperature=0.42,
            max_output_tokens=512,
            strict=True,
        )
        result = generate("query", [], "system")

    assert result == "Funciona sin SDK."
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["model"] == "gemini-test"
    assert call["config"].temperature == 0.42
    assert call["config"].max_output_tokens == 512


def test_vertex_without_project_or_location_raises_runtime_error_in_strict_mode() -> None:
    with pytest.raises(RuntimeError) as exc_info:
        make_google_generate_fn(
            use_vertex=True,
            project="",
            location="",
            strict=True,
        )

    message = str(exc_info.value).lower()
    assert "vertex" in message
    assert "project" in message or "location" in message
