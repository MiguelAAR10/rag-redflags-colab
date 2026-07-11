"""GATE F19 — intake multi-formato + reindexación inteligente.

Deterministas, sin red: el embed_fn y el cliente Qdrant se inyectan como
fakes que cuentan llamadas. Verifica el contrato central: al re-subir un
documento modificado, SOLO los chunks cambiados generan embeddings; los
intactos reutilizan su punto; los eliminados se borran; y queda un
ChangeEvent con los conteos.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.db import init_db
from app.main import app


PARRAFO = (
    "Las especificaciones tecnicas del proceso de contratacion deben ser "
    "objetivas y no dirigidas a un proveedor especifico segun la guia. "
)


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("RAG_VECTOR_STORE", "faiss")
    monkeypatch.setenv("RAG_GROUNDING_METHOD", "lexical")
    monkeypatch.setenv("RAG_INDEX_SUBJECT_DOCS", "0")
    reset_settings_cache()
    init_db()
    return tmp_path


# --------------------------------------------------------------------------- #
# Chunking determinista
# --------------------------------------------------------------------------- #


class TestChunking:
    def test_deterministic(self):
        from app.services.reindex import chunk_text

        text = "\n\n".join(PARRAFO + str(i) for i in range(20))
        assert chunk_text(text) == chunk_text(text)

    def test_editing_one_paragraph_changes_few_hashes(self):
        from app.services.reindex import chunk_hash, chunk_text

        paras = [PARRAFO + str(i) for i in range(20)]
        original = "\n\n".join(paras)
        paras[10] = "Este parrafo fue completamente modificado en la adenda."
        modified = "\n\n".join(paras)

        h_orig = {chunk_hash(c) for c in chunk_text(original)}
        h_mod = {chunk_hash(c) for c in chunk_text(modified)}
        changed = len(h_mod - h_orig)
        total = len(h_mod)
        assert changed < total, "editar 1 parrafo no debe invalidar todos los chunks"

    def test_giant_paragraph_is_split(self):
        from app.services.reindex import chunk_text

        text = "x" * 5000
        chunks = chunk_text(text, target=1200)
        assert all(len(c) <= 1200 for c in chunks)
        assert "".join(chunks) == text


# --------------------------------------------------------------------------- #
# Intake multi-formato
# --------------------------------------------------------------------------- #


class TestMultiFormatIntake:
    def _long_text(self):
        return PARRAFO * 10

    def test_txt_upload(self, temp_env):
        client = TestClient(app)
        resp = client.post(
            "/api/tdrs/upload",
            files={"file": ("tdr.txt", self._long_text().encode(), "text/plain")},
            data={"auto_analyze": "false"},
        )
        assert resp.status_code == 200, resp.text

    def test_docx_upload(self, temp_env, tmp_path):
        docx_mod = pytest.importorskip("docx")
        doc = docx_mod.Document()
        for i in range(12):
            doc.add_paragraph(PARRAFO + f"Seccion {i}.")
        path = tmp_path / "tdr.docx"
        doc.save(path)

        client = TestClient(app)
        resp = client.post(
            "/api/tdrs/upload",
            files={"file": ("tdr.docx", path.read_bytes(),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"auto_analyze": "false"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["char_count"] > 200

    def test_unsupported_extension_rejected(self, temp_env):
        client = TestClient(app)
        resp = client.post(
            "/api/tdrs/upload",
            files={"file": ("tdr.exe", b"MZ" + b"x" * 500, "application/octet-stream")},
            data={"auto_analyze": "false"},
        )
        assert resp.status_code == 400
        assert "no soportado" in resp.json()["detail"].lower()


# --------------------------------------------------------------------------- #
# Reindexación inteligente (diff + eventos + embeddings incrementales)
# --------------------------------------------------------------------------- #


class _FakeQdrant:
    def __init__(self):
        self.upserted = []
        self.deleted = []
        self.collections = set()

    def collection_exists(self, name):
        return name in self.collections

    def create_collection(self, collection_name, vectors_config):
        self.collections.add(collection_name)

    def upsert(self, collection_name, points):
        self.upserted.extend(points)

    def delete(self, collection_name, points_selector):
        self.deleted.extend(points_selector.points)


class TestSmartReindex:
    def _texts(self):
        paras = [PARRAFO + f"Clausula {i}." for i in range(20)]
        v1 = "\n\n".join(paras)
        paras[5] = "Adenda: el monto del contrato se incrementa en 40 por ciento."
        v2 = "\n\n".join(paras)
        return v1, v2

    def _upload(self, client, text):
        resp = client.post(
            "/api/tdrs/upload",
            data={"pasted_text": text, "auto_analyze": "false"},
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    def test_first_version_has_chunks_and_no_event(self, temp_env):
        from sqlmodel import select

        from app.db import get_session
        from app.models import ChangeEvent, DocChunk

        client = TestClient(app)
        v1, _ = self._texts()
        out = self._upload(client, v1)
        assert out["reindex"]["chunks_total"] > 0
        assert out["reindex"]["chunks_added"] == out["reindex"]["chunks_total"]
        assert out["reindex"]["change_event_id"] is None

        # Acotado a ESTA versión: get_engine() es singleton y la base puede
        # contener filas de otros tests de la misma corrida.
        with get_session() as session:
            chunks = session.exec(
                select(DocChunk).where(DocChunk.tdr_version_id == out["version_id"])
            ).all()
            events = session.exec(
                select(ChangeEvent).where(ChangeEvent.tdr_id == out["tdr_id"])
            ).all()
        assert len(chunks) == out["reindex"]["chunks_total"]
        assert events == []

    def test_reupload_same_content_is_noop(self, temp_env):
        client = TestClient(app)
        v1, _ = self._texts()
        out = self._upload(client, v1)
        resp = client.post(
            f"/api/tdrs/{out['tdr_id']}/upload",
            data={"pasted_text": v1},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["unchanged"] is True
        assert body["version_id"] == out["version_id"]

    def test_modified_content_creates_event_with_diff(self, temp_env):
        from sqlmodel import select

        from app.db import get_session
        from app.models import ChangeEvent

        client = TestClient(app)
        v1, v2 = self._texts()
        out = self._upload(client, v1)
        resp = client.post(
            f"/api/tdrs/{out['tdr_id']}/upload",
            data={"pasted_text": v2},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["unchanged"] is False
        summary = body["reindex"]
        assert summary["chunks_added"] >= 1
        assert summary["chunks_kept"] >= 1
        assert summary["chunks_added"] < summary["chunks_total"], (
            "solo los chunks cambiados deben contarse como added"
        )
        assert summary["change_event_id"] is not None

        with get_session() as session:
            event = session.get(ChangeEvent, summary["change_event_id"])
        assert event.chunks_added == summary["chunks_added"]
        assert event.chunks_removed == summary["chunks_removed"]
        assert event.chunks_kept == summary["chunks_kept"]

    def test_incremental_embedding_only_added_chunks(self, temp_env):
        """Con indexación habilitada, SOLO los chunks nuevos se embeben y
        los eliminados se borran de Qdrant (fake, sin red)."""
        from sqlmodel import Session, select

        from app.db import get_engine
        from app.models import Tdr, TdrVersion
        from app.services.reindex import chunk_text, reindex_version

        v1, v2 = self._texts()
        embed_calls = []

        def fake_embed(texts):
            embed_calls.append(list(texts))
            return [[0.1] * 4 for _ in texts]

        fake_client = _FakeQdrant()

        with Session(get_engine()) as session:
            tdr = Tdr(filename="x.txt")
            session.add(tdr)
            session.flush()
            ver1 = TdrVersion(tdr_id=tdr.id, sha256="a" * 64, file_path="",
                              text_path="", char_count=len(v1))
            session.add(ver1)
            session.flush()
            s1 = reindex_version(
                session, tdr_id=tdr.id, version=ver1, text=v1,
                prev_version=None, index_enabled=True,
                embed_fn=fake_embed, qdrant_client=fake_client,
            )
            ver2 = TdrVersion(tdr_id=tdr.id, sha256="b" * 64, file_path="",
                              text_path="", char_count=len(v2))
            session.add(ver2)
            session.flush()
            s2 = reindex_version(
                session, tdr_id=tdr.id, version=ver2, text=v2,
                prev_version=ver1, index_enabled=True,
                embed_fn=fake_embed, qdrant_client=fake_client,
            )
            session.commit()

        # v1: se embebe todo; v2: SOLO los added
        assert len(embed_calls[0]) == s1["chunks_total"]
        assert len(embed_calls[1]) == s2["chunks_added"]
        assert s2["chunks_added"] < s2["chunks_total"]
        # puntos eliminados = chunks removed
        assert len(fake_client.deleted) == s2["chunks_removed"]
        # total upserts = todos los de v1 + solo added de v2
        assert len(fake_client.upserted) == s1["chunks_total"] + s2["chunks_added"]
