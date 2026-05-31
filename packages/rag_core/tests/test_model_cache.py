"""
Gate del FIX — los cargadores de modelos están cacheados (no recargan).

Unit deterministas: cada loader está envuelto por lru_cache (expone cache_info)
+ test funcional con un SentenceTransformer falso que cuenta construcciones.
"""
import pytest


def test_embedding_loader_is_cached():
    from packages.rag_core.embeddings import _load_model
    assert hasattr(_load_model, "cache_info"), "_load_model debe estar lru_cached"
    assert hasattr(_load_model, "cache_clear")


def test_reranker_loader_is_cached():
    from packages.rag_core.rerankers import _load_cross_encoder
    assert hasattr(_load_cross_encoder, "cache_info")


def test_qwen_loader_is_cached():
    from packages.rag_core.agent import _load_qwen
    assert hasattr(_load_qwen, "cache_info")


def test_qwen_loader_supports_4bit_env():
    """Verifica (estático, sin descargar modelo) que _load_qwen soporta RAG_QWEN_4BIT."""
    import inspect
    from packages.rag_core.agent import _load_qwen
    src = inspect.getsource(_load_qwen.__wrapped__ if hasattr(_load_qwen, "__wrapped__") else _load_qwen)
    assert "RAG_QWEN_4BIT" in src
    assert "load_in_4bit" in src or "BitsAndBytesConfig" in src


def test_embedding_model_loaded_once(monkeypatch):
    """Dos llamadas a _load_model NO deben construir el modelo dos veces."""
    pytest.importorskip("sentence_transformers")
    import sentence_transformers
    from packages.rag_core import embeddings

    calls = {"n": 0}

    class _FakeST:
        def __init__(self, *a, **k):
            calls["n"] += 1

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", _FakeST)
    embeddings._load_model.cache_clear()
    try:
        m1 = embeddings._load_model("fake-model-x")
        m2 = embeddings._load_model("fake-model-x")
        assert m1 is m2            # mismo objeto (cacheado)
        assert calls["n"] == 1     # construido una sola vez
    finally:
        embeddings._load_model.cache_clear()
