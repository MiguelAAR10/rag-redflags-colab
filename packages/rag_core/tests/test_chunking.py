"""
GATE de aceptación de la Fase 2 (chunking).

Valida que chunk_units respete size, overlap, herencia de metadata,
y generación de reporte comparativo.

Depende de stdlib + pytest. Si el dataset no existe, hace skip.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# Localización de rutas
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "data" / "processed" / "redflags_units.jsonl"
CHUNKERS_PATH = REPO_ROOT / "packages" / "rag_core" / "chunkers.py"

# --------------------------------------------------------------------------- #
# Import chunkers (skip si no existe)
# --------------------------------------------------------------------------- #
if not CHUNKERS_PATH.exists():
    pytest.skip(f"No existe {CHUNKERS_PATH}", allow_module_level=True)

import importlib.util
spec = importlib.util.spec_from_file_location("chunkers", CHUNKERS_PATH)
chunkers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chunkers)

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def sample_units():
    """Unidades de prueba sintéticas."""
    return [
        {
            "doc_id": "test_001",
            "source_file": "test.pdf",
            "page_start": 1,
            "page_end": 1,
            "family": "planeacion",
            "indicator_code": "R001",
            "indicator_name": "Test indicator",
            "block_type": "core",
            "text": "Este es un texto de prueba para verificar que el chunking funciona correctamente. " * 20,
        },
        {
            "doc_id": "test_002",
            "source_file": "test.pdf",
            "page_start": 2,
            "page_end": 2,
            "family": "competencia/licitacion",
            "indicator_code": "R002",
            "indicator_name": "Another test",
            "block_type": "formula",
            "text": "Texto corto.",
        },
    ]


@pytest.fixture(scope="module")
def real_units():
    """Unidades reales del dataset (skip si no existe)."""
    if not DATASET_PATH.exists():
        pytest.skip(f"Dataset no encontrado: {DATASET_PATH}")
    units = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                units.append(json.loads(line))
    return units


# --------------------------------------------------------------------------- #
# Tests sobre datos sintéticos
# --------------------------------------------------------------------------- #

class TestChunkUnitsSynthetic:
    """Tests con unidades sintéticas (no dependen del dataset)."""

    def test_chunk_respects_size(self, sample_units):
        """Ningún chunk excede el tamaño especificado."""
        chunks = chunkers.chunk_units(sample_units, size=512, overlap=64)
        for chunk in chunks:
            assert chunk["n_chars"] <= 512, (
                f"Chunk {chunk['chunk_id']} excede size: {chunk['n_chars']} > 512"
            )

    def test_chunk_overlap_exists(self, sample_units):
        """Chunks contiguos del mismo padre comparten texto (overlap > 0)."""
        chunks = chunkers.chunk_units(sample_units, size=256, overlap=64)
        # Encontrar chunks del mismo padre con índices consecutivos
        by_parent = {}
        for c in chunks:
            by_parent.setdefault(c["doc_id"], []).append(c)

        overlaps_found = 0
        for parent_id, parent_chunks in by_parent.items():
            if len(parent_chunks) <= 1:
                continue
            parent_chunks.sort(key=lambda c: c["chunk_index"])
            for i in range(1, len(parent_chunks)):
                prev_text = parent_chunks[i - 1]["text"]
                curr_text = parent_chunks[i]["text"]
                # Verificar que hay overlap (texto en común)
                shared = False
                for ovl in range(min(len(prev_text), len(curr_text)), 0, -1):
                    if prev_text[-ovl:] == curr_text[:ovl]:
                        shared = True
                        break
                if shared:
                    overlaps_found += 1

        assert overlaps_found > 0, "No se encontró overlap entre chunks consecutivos"

    def test_short_text_single_chunk(self, sample_units):
        """Textos cortos generan un solo chunk."""
        chunks = chunkers.chunk_units(sample_units, size=1024, overlap=128)
        # test_002 tiene texto corto
        doc2_chunks = [c for c in chunks if c["doc_id"] == "test_002"]
        assert len(doc2_chunks) == 1
        assert doc2_chunks[0]["chunk_index"] == 0

    def test_metadata_inheritance(self, sample_units):
        """Cada chunk hereda metadata de su unidad padre."""
        chunks = chunkers.chunk_units(sample_units, size=256, overlap=64)
        required_meta = [
            "doc_id", "source_file", "page_start", "page_end",
            "family", "indicator_code", "indicator_name", "block_type",
        ]
        for chunk in chunks:
            for key in required_meta:
                assert key in chunk, f"Falta key '{key}' en chunk {chunk['chunk_id']}"

            # Verificar que el doc_id apunta al padre correcto
            parent = next((u for u in sample_units if u["doc_id"] == chunk["doc_id"]), None)
            assert parent is not None, f"No se encontró padre para chunk {chunk['chunk_id']}"
            assert chunk["family"] == parent["family"]
            assert chunk["indicator_code"] == parent["indicator_code"]
            assert chunk["indicator_name"] == parent["indicator_name"]
            assert chunk["block_type"] == parent["block_type"]

    def test_chunk_index_sequential(self, sample_units):
        """Los índices de chunk son secuenciales por padre."""
        chunks = chunkers.chunk_units(sample_units, size=256, overlap=64)
        by_parent = {}
        for c in chunks:
            by_parent.setdefault(c["doc_id"], []).append(c)

        for parent_id, parent_chunks in by_parent.items():
            if len(parent_chunks) > 1:
                indices = [c["chunk_index"] for c in sorted(parent_chunks, key=lambda c: c["chunk_index"])]
                assert indices == list(range(len(indices))), (
                    f"Índices no secuenciales para {parent_id}: {indices}"
                )

    def test_chunk_id_unique(self, sample_units):
        """Todos los chunk_id son únicos."""
        chunks = chunkers.chunk_units(sample_units, size=128, overlap=32)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids)), "chunk_id duplicados encontrados"

    def test_empty_text_skipped(self):
        """Unidades con texto vacío se ignoran."""
        units = [{"doc_id": "empty", "text": ""}]
        chunks = chunkers.chunk_units(units, size=512, overlap=64)
        assert len(chunks) == 0

    def test_invalid_params(self):
        """Parámetros inválidos lanzan ValueError."""
        units = [{"doc_id": "x", "text": "hola"}]
        with pytest.raises(ValueError):
            chunkers.chunk_units(units, size=0, overlap=0)
        with pytest.raises(ValueError):
            chunkers.chunk_units(units, size=100, overlap=100)
        with pytest.raises(ValueError):
            chunkers.chunk_units(units, size=100, overlap=-1)


# --------------------------------------------------------------------------- #
# Tests sobre datos reales
# --------------------------------------------------------------------------- #

class TestChunkUnitsReal:
    """Tests con unidades reales del dataset (requieren Fase 1)."""

    def test_real_dataset_chunks(self, real_units):
        """El dataset real se puede chunkificar sin errores."""
        assert len(real_units) > 0
        chunks = chunkers.chunk_units(real_units, size=1024, overlap=128)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["n_chars"] <= 1024

    def test_real_metadata_consistency(self, real_units):
        """Metadata consistente en chunks del dataset real."""
        chunks = chunkers.chunk_units(real_units, size=512, overlap=64)
        by_parent = {}
        for c in chunks:
            by_parent.setdefault(c["doc_id"], []).append(c)

        for parent_id, parent_chunks in by_parent.items():
            families = set(c["family"] for c in parent_chunks)
            assert len(families) == 1, f"Family inconsistente en {parent_id}: {families}"

    def test_compare_configs_runs(self, real_units):
        """La función de comparación genera un reporte válido."""
        configs = [
            (512, 64, "small"),
            (1024, 128, "medium"),
        ]
        report = chunkers.compare_chunk_configs(real_units, configs)
        assert "configs" in report
        assert len(report["configs"]) == 2
        for cfg in report["configs"]:
            assert cfg["total_chunks"] > 0
            assert cfg["avg_chunk_len"] > 0
            assert cfg["max_chunk_len"] <= cfg["size"]


# --------------------------------------------------------------------------- #
# Tests de integración / script principal
# --------------------------------------------------------------------------- #

class TestChunkingScript:
    """Valida que el script se ejecuta y produce outputs."""

    def test_main_script_runs(self, real_units, tmp_path):
        """El bloque __main__ produce archivos esperados."""
        if not DATASET_PATH.exists():
            pytest.skip("Dataset no disponible")

        out_chunks = tmp_path / "chunks.jsonl"
        out_report = tmp_path / "report.json"

        # Simular ejecución del main
        units = real_units
        configs = [
            (512, 64, "small"),
            (1024, 128, "medium"),
            (2048, 256, "large"),
        ]
        report = chunkers.compare_chunk_configs(units, configs)
        recommended = chunkers.chunk_units(units, size=1024, overlap=128)
        chunkers.save_chunks(recommended, out_chunks)

        with open(out_report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        assert out_chunks.exists()
        assert out_report.exists()

        # Validar que los chunks se pueden cargar
        loaded = chunkers.load_units(out_chunks)
        assert len(loaded) == len(recommended)
        for c in loaded:
            assert "chunk_id" in c
            assert "doc_id" in c
            assert "n_chars" in c
            assert c["n_chars"] <= 1024