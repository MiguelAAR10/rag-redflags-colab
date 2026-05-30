"""
Gate de Fase 9 — vía LangChain.

Unit (siempre corren, sin LangChain): mapeo chunk -> documento conserva
metadata; el módulo importa sin langchain instalado.
Integration (skip si falta langchain/faiss/modelo): construir vectorstore,
persistir/cargar y recuperar top-k.
"""
import importlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


def test_module_imports_without_langchain():
    # importar el módulo NO debe requerir langchain (imports perezosos)
    mod = importlib.import_module("packages.rag_core.langchain_rag")
    assert hasattr(mod, "build_vectorstore")
    assert hasattr(mod, "quick_query")


def test_doc_payload_preserves_metadata():
    from packages.rag_core.langchain_rag import _doc_payload

    chunk = {
        "chunk_id": "c1",
        "text": "Single bidder red flag definition.",
        "family": "competencia/licitacion",
        "indicator_code": "R018",
        "indicator_name": "Single bidder",
        "block_type": "core",
        "page_start": 25,
        "page_end": 25,
    }
    p = _doc_payload(chunk)
    assert p["page_content"] == chunk["text"]
    assert p["metadata"]["indicator_code"] == "R018"
    assert p["metadata"]["family"] == "competencia/licitacion"
    assert p["metadata"]["chunk_id"] == "c1"


def test_safe_language_in_prompt():
    from packages.rag_core.langchain_rag import SAFE_SYSTEM

    assert "señal de riesgo" in SAFE_SYSTEM
    assert "revisión humana" in SAFE_SYSTEM


@pytest.mark.parametrize("dep", ["langchain_community", "langchain_huggingface"])
def test_integration_build_and_query(dep, tmp_path):
    pytest.importorskip(dep, reason=f"{dep} no instalado (se corre en Colab)")
    pytest.importorskip("faiss")
    from packages.rag_core.langchain_rag import build_vectorstore, get_retriever

    chunks = [
        {"chunk_id": "a", "text": "Single bidder in the tender process.",
         "family": "competencia/licitacion", "indicator_code": "R018",
         "indicator_name": "Single bidder", "block_type": "core",
         "page_start": 1, "page_end": 1},
        {"chunk_id": "b", "text": "Contract delivered with long delays.",
         "family": "ejecucion/contrato", "indicator_code": "R040",
         "indicator_name": "Delays", "block_type": "core",
         "page_start": 2, "page_end": 2},
    ]
    vs = build_vectorstore(chunks, persist_dir=str(tmp_path / "lc_faiss"))
    docs = get_retriever(vs, k=1).invoke("only one bidder participated")
    assert len(docs) == 1
    assert docs[0].metadata.get("indicator_code") in {"R018", "R040"}
