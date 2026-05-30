"""
Gate de Fase 8 — smoke test del notebook de Colab.

NO ejecuta el notebook (eso se hace en Colab T4). Valida que el .ipynb sea
JSON nbformat v4 válido, cubra las 10 secciones de la rúbrica e invoque las
APIs reales de rag_core. Si el notebook no existe, hace skip.
"""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
NB = REPO / "notebooks" / "redflags_rag_colab.ipynb"


def _load():
    if not NB.exists():
        pytest.skip(f"notebook no encontrado: {NB}")
    return json.loads(NB.read_text(encoding="utf-8"))


def _all_source():
    nb = _load()
    return "\n".join("".join(c.get("source", [])) for c in nb["cells"])


def test_notebook_is_valid_nbformat4():
    nb = _load()
    assert nb.get("nbformat") == 4
    assert isinstance(nb.get("cells"), list) and len(nb["cells"]) >= 10


def test_has_ten_rubric_sections():
    src = _all_source()
    for n in range(1, 11):
        assert f"## {n}." in src, f"falta la sección {n}"


def test_uses_real_rag_core_api():
    src = _all_source()
    for token in [
        "load_pdf",            # 2 dataset
        "chunk_units",         # 3 chunking
        "embed_texts",         # 4 embeddings
        "build_index",         # 5 FAISS
        "hybrid_search",       # 6 retrieval híbrido
        "route_family",        # 6 router
        "rerank",              # 7 reranker
        "analyze",             # 7 Qwen pipeline
        "grounding_ratio",     # 8 grounding
        "evaluate_on_goldset", # 9 eval
    ]:
        assert token in src, f"el notebook no usa {token}"


def test_uses_qwen_and_safe_language():
    src = _all_source()
    assert "Qwen2.5-3B" in src
    assert "revisión humana" in src or "revision humana" in src


def test_code_cells_non_empty():
    nb = _load()
    code = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    assert len(code) >= 8
    for c in code:
        assert "".join(c.get("source", [])).strip(), "celda de código vacía"
