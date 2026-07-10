"""TDR intake: extract text from PDF or pasted text, hash, persist.

This module deliberately avoids depending on heavy PDF libraries if
not needed: PDFs are parsed with PyMuPDF if available, otherwise we
return a clear parser_note that the user can paste text manually.

The intake is designed to be safe for the web demo:
- Compute SHA-256 over the extracted text (not the file bytes),
  so identical text always produces the same version hash.
- Reject uploads that produce too little text (likely scanned PDFs).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


MIN_TEXT_CHARS = 200
MAX_TEXT_CHARS = 50_000


@dataclass
class IntakeResult:
    text: str
    sha256: str
    char_count: int
    parser_notes: str
    file_path: str
    text_path: str


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(path: str) -> tuple[str, str]:
    """Return (text, parser_note). Empty text means likely scanned PDF."""
    try:
        import fitz  # PyMuPDF
    except Exception:
        return "", "PyMuPDF no instalado; el archivo PDF no se pudo procesar."

    try:
        doc = fitz.open(path)
    except Exception as exc:  # pragma: no cover - defensive
        return "", f"No se pudo abrir el PDF: {exc}"

    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    text = "\n\n".join(parts).strip()
    if len(text) < MIN_TEXT_CHARS:
        return (
            "",
            "PDF sin texto extraíble (probablemente escaneado). Pega el texto manualmente.",
        )
    return text, ""


def extract_text_from_pasted(text: str) -> tuple[str, str]:
    normalized = _normalize_text(text)
    if len(normalized) < MIN_TEXT_CHARS:
        return (
            "",
            f"El texto pegado debe tener al menos {MIN_TEXT_CHARS} caracteres.",
        )
    return normalized, ""


def persist_intake(
    *,
    filename: str,
    raw_bytes: Optional[bytes],
    pasted_text: Optional[str],
    upload_dir: str,
) -> IntakeResult:
    """Save the file (if provided), extract text, compute hash, save text.

    Exactly one of raw_bytes or pasted_text must be provided.
    """
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path: Optional[Path] = None
    if raw_bytes is not None and len(raw_bytes) > 0:
        safe_name = Path(filename).name or "upload.pdf"
        file_path = upload_path / safe_name
        file_path.write_bytes(raw_bytes)

    if pasted_text is not None and pasted_text.strip():
        text, note = extract_text_from_pasted(pasted_text)
    elif file_path is not None and file_path.suffix.lower() == ".pdf":
        text, note = extract_text_from_pdf(str(file_path))
    elif file_path is not None and file_path.suffix.lower() in {".txt", ".md"}:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            text, note = extract_text_from_pasted(content)
        except Exception as exc:  # pragma: no cover - defensive
            text, note = "", f"No se pudo leer el archivo de texto: {exc}"
    else:
        text, note = "", "Tipo de archivo no soportado. Usa PDF o TXT."

    if not text:
        raise ValueError(note or "No se pudo extraer texto del documento.")

    sha = compute_sha256(text)
    text_path = upload_path / f"{sha}.txt"
    text_path.write_text(text, encoding="utf-8")

    stored_file_path = str(file_path) if file_path else ""
    return IntakeResult(
        text=text,
        sha256=sha,
        char_count=len(text),
        parser_notes=note,
        file_path=stored_file_path,
        text_path=str(text_path),
    )