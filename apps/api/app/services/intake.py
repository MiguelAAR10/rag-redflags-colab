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


def extract_text_from_docx(path: str) -> tuple[str, str]:
    """Return (text, parser_note) desde un .docx (párrafos + tablas)."""
    try:
        import docx  # python-docx
    except Exception:
        return "", "python-docx no instalado; el archivo DOCX no se pudo procesar."

    try:
        document = docx.Document(path)
    except Exception as exc:  # pragma: no cover - defensive
        return "", f"No se pudo abrir el DOCX: {exc}"

    parts: list[str] = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    text = _normalize_text("\n\n".join(parts))
    if len(text) < MIN_TEXT_CHARS:
        return "", "DOCX sin texto suficiente (¿documento vacío o solo imágenes?)."
    return text, ""


def extract_text_from_plain(path: str) -> tuple[str, str]:
    """Return (text, parser_note) desde .txt/.md."""
    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # pragma: no cover - defensive
        return "", f"No se pudo leer el archivo de texto: {exc}"
    return extract_text_from_pasted(content)


def extract_text_from_pasted(text: str) -> tuple[str, str]:
    normalized = _normalize_text(text)
    if len(normalized) < MIN_TEXT_CHARS:
        return (
            "",
            f"El texto pegado debe tener al menos {MIN_TEXT_CHARS} caracteres.",
        )
    return normalized, ""


# Registro de extractores por extensión (F19: intake multi-formato).
# Para soportar un formato nuevo basta añadir su extractor aquí.
EXTRACTORS = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
    ".txt": extract_text_from_plain,
    ".md": extract_text_from_plain,
}

SUPPORTED_EXTENSIONS = tuple(sorted(EXTRACTORS))


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
    elif file_path is not None:
        extractor = EXTRACTORS.get(file_path.suffix.lower())
        if extractor is None:
            supported = ", ".join(SUPPORTED_EXTENSIONS)
            text, note = "", f"Tipo de archivo no soportado. Usa: {supported}."
        else:
            text, note = extractor(str(file_path))
    else:
        text, note = "", "Debes subir un archivo o pegar texto."

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