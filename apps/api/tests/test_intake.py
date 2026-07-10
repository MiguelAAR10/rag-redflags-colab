"""Tests for the intake module."""

from __future__ import annotations

import re

import pytest

from app.services.intake import (
    MIN_TEXT_CHARS,
    compute_sha256,
    extract_text_from_pasted,
    persist_intake,
)


def test_compute_sha256_deterministic():
    assert compute_sha256("hola") == compute_sha256("hola")


def test_extract_text_from_pasted_normalizes_whitespace():
    raw = "hola   mundo\n\n\n\n  fin\n" + ("lorem ipsum " * 30)
    text, note = extract_text_from_pasted(raw)
    assert note == ""
    assert text.startswith("hola mundo")
    # Multiple blank lines collapse to a single blank-line gap.
    assert "\n\n\n" not in text
    assert "lorem ipsum" in text


def test_extract_text_rejects_too_short():
    text, note = extract_text_from_pasted("corto")
    assert text == ""
    assert MIN_TEXT_CHARS > 100


def test_persist_intake_pasted(tmp_path):
    payload = ("x" * 250).encode("utf-8")
    result = persist_intake(
        filename="dummy.pdf",
        raw_bytes=None,
        pasted_text="Lorem ipsum " * 50,
        upload_dir=str(tmp_path),
    )
    assert result.char_count > MIN_TEXT_CHARS
    assert result.sha256
    assert result.text_path.endswith(".txt")
    assert (tmp_path / "dummy.pdf").exists() is False


def test_persist_intake_text_file(tmp_path):
    text_file = tmp_path / "input.txt"
    text_file.write_text("Contenido válido " * 80, encoding="utf-8")
    result = persist_intake(
        filename="input.txt",
        raw_bytes=text_file.read_bytes(),
        pasted_text=None,
        upload_dir=str(tmp_path),
    )
    assert result.char_count > MIN_TEXT_CHARS
    assert (tmp_path / "input.txt").exists()


def test_persist_intake_unsupported_extension(tmp_path):
    payload = b"binary data"
    with pytest.raises(ValueError):
        persist_intake(
            filename="file.bin",
            raw_bytes=payload,
            pasted_text=None,
            upload_dir=str(tmp_path),
        )


def test_persist_intake_short_text(tmp_path):
    with pytest.raises(ValueError):
        persist_intake(
            filename="tiny.txt",
            raw_bytes=None,
            pasted_text="muy corto",
            upload_dir=str(tmp_path),
        )


def test_persist_intake_filename_pattern():
    sha = compute_sha256("hola mundo")
    assert re.fullmatch(r"[a-f0-9]{64}", sha)