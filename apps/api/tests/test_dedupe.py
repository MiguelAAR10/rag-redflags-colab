"""GATE F18 — dedupe de análisis por versión (spec 006).

Re-analizar la misma versión (mismo sha256 de texto) no crea un run nuevo:
devuelve el run completado existente. force=True re-analiza explícitamente.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.google_llm import make_fake_generate_fn
from app.config import reset_settings_cache
from app.db import init_db
from app.main import app


FAKE_RETRIEVED_CHUNKS = [
    {
        "chunk_id": "test-r010",
        "text": (
            "El plazo de entrega es de 5 dias habiles. Los plazos muy cortos "
            "pueden reducir la competencia y requieren revision humana."
        ),
        "indicator_name": "Bidding period too short",
        "indicator_code": "R010",
        "page_start": 10,
        "page_end": 12,
    }
]


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    # Hermético: sin red aunque el .env local del dev diga qdrant/gemini
    monkeypatch.setenv("RAG_VECTOR_STORE", "faiss")
    monkeypatch.setenv("RAG_GROUNDING_METHOD", "lexical")
    monkeypatch.setenv("RAG_INDEX_SUBJECT_DOCS", "false")
    reset_settings_cache()
    init_db()
    return tmp_path


def _upload_tdr(client: TestClient, text: str) -> int:
    response = client.post(
        "/api/tdrs/upload",
        data={"pasted_text": text, "auto_analyze": "false"},
    )
    assert response.status_code == 200, response.text
    return response.json()["tdr_id"]


def test_same_version_returns_existing_run(temp_env):
    from app.services.orchestrator import queue_analysis

    client = TestClient(app)
    text = "TDR de prueba: adjudicación directa con un solo oferente. " * 20
    tdr_id = _upload_tdr(client, text)

    fake = make_fake_generate_fn()
    run1 = queue_analysis(
        tdr_id, generate_fn=fake, retrieved_chunks=FAKE_RETRIEVED_CHUNKS
    )
    run2 = queue_analysis(
        tdr_id, generate_fn=fake, retrieved_chunks=FAKE_RETRIEVED_CHUNKS
    )

    assert run1 == run2, "misma versión completada no debe re-analizarse"


def test_force_creates_new_run(temp_env):
    from app.services.orchestrator import queue_analysis

    client = TestClient(app)
    text = "TDR de prueba: plazos de entrega imposibles de cumplir. " * 20
    tdr_id = _upload_tdr(client, text)

    fake = make_fake_generate_fn()
    run1 = queue_analysis(
        tdr_id, generate_fn=fake, retrieved_chunks=FAKE_RETRIEVED_CHUNKS
    )
    run2 = queue_analysis(
        tdr_id,
        generate_fn=fake,
        retrieved_chunks=FAKE_RETRIEVED_CHUNKS,
        force=True,
    )

    assert run2 != run1, "force=True debe crear un run nuevo"


def test_failed_run_does_not_block_retry(temp_env):
    from app.services.orchestrator import queue_analysis

    client = TestClient(app)
    text = "TDR de prueba: especificaciones dirigidas a una marca única. " * 20
    tdr_id = _upload_tdr(client, text)

    def broken_fn(query, chunks, system_prompt):
        raise RuntimeError("LLM caído")

    run1 = queue_analysis(
        tdr_id,
        generate_fn=broken_fn,
        retrieved_chunks=FAKE_RETRIEVED_CHUNKS,
    )

    fake = make_fake_generate_fn()
    run2 = queue_analysis(
        tdr_id, generate_fn=fake, retrieved_chunks=FAKE_RETRIEVED_CHUNKS
    )
    assert run2 != run1, "un run fallido no debe bloquear el reintento"
