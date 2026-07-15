"""
Gate de Fase 8 — smoke test del notebook de Colab.

NO ejecuta el notebook (eso se hace en Colab T4). Valida que el .ipynb sea
JSON nbformat v4 válido, cubra las 10 secciones de la rúbrica e invoque las
APIs reales de rag_core. Si el notebook no existe, hace skip.
"""
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
NB = REPO / "notebooks" / "redflags_rag_colab.ipynb"
COLAB_ARTIFACTS = {
    "data/raw/OCP2024-RedFlagProcurement-1.pdf": 1_000_000,
    "data/processed/redflags_units.jsonl": 100_000,
    "data/processed/redflags_chunks.jsonl": 100_000,
    "data/index/redflags_flatip.index": 500_000,
    "data/index/chunk_id_mapping.json": 10_000,
}


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


def test_required_colab_artifacts_are_versioned():
    for relative_path, minimum_size in COLAB_ARTIFACTS.items():
        artifact = REPO / relative_path
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative_path],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        assert tracked.returncode == 0, f"artefacto no versionado: {relative_path}"
        assert artifact.is_file(), f"artefacto requerido por Run all ausente: {relative_path}"
        assert artifact.stat().st_size >= minimum_size, (
            f"artefacto vacio o incompleto: {relative_path}"
        )


def test_versioned_jsonl_artifacts_are_one_valid_object_per_line():
    expected_counts = {
        "data/processed/redflags_units.jsonl": 237,
        "data/processed/redflags_chunks.jsonl": 299,
    }
    for relative_path, expected_count in expected_counts.items():
        with (REPO / relative_path).open(encoding="utf-8") as jsonl_file:
            lines = list(jsonl_file)
        assert len(lines) == expected_count, f"conteo inesperado en {relative_path}"
        for line_number, line in enumerate(lines, start=1):
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                pytest.fail(f"JSONL invalido en {relative_path}:{line_number}: {exc}")


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
    for unsafe_claim in (
        "señal de riesgo de corrupción",
        "prácticas fraudulentas",
        "resultado de corrupción",
    ):
        assert unsafe_claim not in src.lower(), f"lenguaje inseguro: {unsafe_claim}"


def test_code_cells_non_empty():
    nb = _load()
    code = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    assert len(code) >= 8
    for c in code:
        assert "".join(c.get("source", [])).strip(), "celda de código vacía"


def test_run_all_has_no_interactive_prompts():
    src = _all_source()
    assert "getpass(" not in src, "Run all no debe pedir tokens manualmente"
    assert "files.upload(" not in src, "Run all no debe pedir archivos manualmente"


def test_has_chat_section():
    src = _all_source()
    assert "## 12" in src, "falta la sección 12 (chat)"
    assert "gr.ChatInterface" in src, "el chat debe usar gr.ChatInterface"
    assert "analizar_contrato_chat" in src and "analyze(" in src, "el chat debe llamar analyze()"


def test_has_hnsw_benchmark():
    src = _all_source()
    assert "IndexHNSWFlat" in src, "falta el benchmark HNSW (sección 5.2)"


def test_has_dual_rag_gemini_qdrant_optional_path():
    src = _all_source()
    for token in [
        "RAG_BACKEND",
        "RAG_GENERATOR",
        "RUN_QDRANT_DEMO",
        "RUN_DUAL_RAG_COMPARISON",
        "retrieve(",
        "compare_backends",
        "validate_dual_evidence",
        "make_google_generate_fn",
        "standard_kb",
        "GEMINI_API_KEY",
        "QDRANT_URL",
        "QDRANT_API_KEY",
    ]:
        assert token in src, f"falta contrato dual RAG: {token}"


def test_default_path_remains_faiss_qwen():
    src = _all_source()
    assert 'RAG_BACKEND = os.getenv("RAG_BACKEND", "faiss")' in src
    assert 'RAG_GENERATOR = os.getenv("RAG_GENERATOR", "qwen")' in src
    assert "Qwen2.5-3B" in src


def test_evaluation_separates_answer_quality_from_security_traps():
    src = _all_source()
    assert "answerable_gold" in src
    assert "security_gold" in src
    assert "abstention_accuracy" in src
    assert "evaluate_security_case" in src
    assert "correction_match" in src
