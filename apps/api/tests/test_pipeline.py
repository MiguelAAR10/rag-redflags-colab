"""Integration test: full pipeline with a fake LLM.

This test does NOT call Gemini. It uses the deterministic fake
generate_fn and walks through the orchestrator end to end.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.google_llm import make_fake_generate_fn
from app.config import reset_settings_cache
from app.db import init_db
from app.main import app
from app.models import TdrVersion
from app.services.intake import persist_intake


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
def temp_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    # Hermético: sin red aunque el .env local del dev diga qdrant/gemini
    monkeypatch.setenv("RAG_VECTOR_STORE", "faiss")
    monkeypatch.setenv("RAG_GROUNDING_METHOD", "lexical")
    monkeypatch.setenv("RAG_INDEX_SUBJECT_DOCS", "false")
    reset_settings_cache()
    init_db()
    return tmp_path


def _seed_text_version(upload_dir: str, text: str, sha: str) -> tuple[str, str]:
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    text_path = upload_path / f"{sha}.txt"
    text_path.write_text(text, encoding="utf-8")
    return str(text_path), ""


def test_pipeline_end_to_end(temp_upload_dir):
    client = TestClient(app)

    # 1) Upload text via API
    text = (
        "TDR de prueba sobre adjudicación. Plazo de entrega muy corto, "
        "especificaciones técnicas subjetivas. " * 30
    )
    response = client.post(
        "/api/tdrs/upload",
        data={"pasted_text": text, "auto_analyze": "false"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    tdr_id = payload["tdr_id"]

    # 2) Manually run analysis with fake generate_fn
    from sqlmodel import select

    from app.db import get_session
    from app.services.orchestrator import queue_analysis

    with get_session() as session:
        v = session.exec(
            select(TdrVersion).where(TdrVersion.tdr_id == tdr_id)
        ).one()
        version_id = v.id

    run_id = queue_analysis(
        tdr_id,
        generate_fn=make_fake_generate_fn(),
        retrieved_chunks=FAKE_RETRIEVED_CHUNKS,
    )

    # 3) Verify status
    status = client.get(f"/api/runs/{run_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"

    # 4) Get dossier JSON
    dossier = client.get(f"/api/tdrs/{tdr_id}/dossier")
    assert dossier.status_code == 200
    body = dossier.json()
    assert body["risk_level"] in {"Bajo", "Medio", "Alto", "Evidencia insuficiente"}
    assert body["evidence"]["status"] in {"sufficient", "weak", "insufficient"}
    assert "disclaimer" in body
    assert "No es una acusaci\u00f3n" in body["disclaimer"]


def test_health_endpoint(temp_upload_dir):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_home_renders(temp_upload_dir):
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "TDR" in response.text


def test_upload_form_renders(temp_upload_dir):
    client = TestClient(app)
    response = client.get("/tdrs/upload")
    assert response.status_code == 200
    assert "Subir" in response.text


def test_upload_rejects_empty(temp_upload_dir):
    client = TestClient(app)
    response = client.post("/tdrs/upload")
    assert response.status_code == 400


def test_list_tdrs_empty(temp_upload_dir):
    client = TestClient(app)
    response = client.get("/tdrs")
    assert response.status_code == 200
    assert "Mis revisiones" in response.text
