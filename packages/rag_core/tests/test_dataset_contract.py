"""GATE de aceptacion de la Fase 1 (dataset).

Valida el contrato del dataset `data/processed/redflags_units.jsonl` y la
integracion minima con `packages/rag_core/loaders.py`.

Solo depende de la stdlib + pytest. Si el dataset (o las dependencias del
loader) no estan disponibles, los tests hacen `pytest.skip` con un mensaje
claro en lugar de fallar.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# Localizacion de rutas (subiendo desde __file__ con pathlib).
#   __file__ = .../packages/rag_core/tests/test_dataset_contract.py
#   parents[0] = tests, [1] = rag_core, [2] = packages, [3] = raiz del repo
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "data" / "processed" / "redflags_units.jsonl"
LOADERS_PATH = REPO_ROOT / "packages" / "rag_core" / "loaders.py"
RAW_DIR = REPO_ROOT / "data" / "raw"

# --------------------------------------------------------------------------- #
# Esquema esperado de cada unidad.
# --------------------------------------------------------------------------- #
REQUIRED_KEYS = {
    "doc_id",
    "parent_doc_id",
    "source_file",
    "page_start",
    "page_end",
    "section",
    "block_type",
    "family",
    "stage",
    "indicator_code",
    "indicator_name",
    "hash",
    "text",
}

VALID_SECTIONS = {"indicator", "metodologia"}
VALID_BLOCK_TYPES = {"core", "formula", "example", "section"}
VALID_FAMILIES = {
    "planeacion",
    "competencia/licitacion",
    "adjudicacion",
    "ejecucion/contrato",
    "metodologia",
}
# Las 4 familias de indicador que deben estar presentes (sin metodologia).
INDICATOR_FAMILIES = {
    "planeacion",
    "competencia/licitacion",
    "adjudicacion",
    "ejecucion/contrato",
}

MIN_LINES = 100
INDICATOR_NAME_MIN_RATIO = 0.95

# Una linea cuyo primer renglon sea solo un numero (de pagina).
PAGE_NUMBER_ONLY_RE = re.compile(r"^\s*\d+\s*$")


# --------------------------------------------------------------------------- #
# Fixtures / helpers.
# --------------------------------------------------------------------------- #
def _skip_if_no_dataset() -> None:
    if not DATASET_PATH.exists():
        pytest.skip(
            f"Dataset no encontrado en {DATASET_PATH}. "
            "Genera la Fase 1.1 antes de correr el GATE de datos."
        )


@pytest.fixture(scope="module")
def units() -> list[dict]:
    """Carga y parsea el JSONL una sola vez por modulo.

    Hace skip si el archivo no existe; falla si alguna linea no es JSON valido.
    """
    _skip_if_no_dataset()

    parsed: list[dict] = []
    with DATASET_PATH.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:  # noqa: PERF203
                pytest.fail(
                    f"Linea {lineno} de {DATASET_PATH.name} no es JSON valido: {exc}"
                )
            assert isinstance(obj, dict), f"Linea {lineno} no es un objeto JSON"
            parsed.append(obj)
    return parsed


# --------------------------------------------------------------------------- #
# TESTS UNIT (sobre el JSONL).
# --------------------------------------------------------------------------- #
def test_dataset_exists_and_has_min_lines(units: list[dict]) -> None:
    assert len(units) >= MIN_LINES, (
        f"Se esperaban >= {MIN_LINES} unidades, se encontraron {len(units)}."
    )


def test_every_unit_has_all_required_keys(units: list[dict]) -> None:
    for i, unit in enumerate(units):
        missing = REQUIRED_KEYS - set(unit.keys())
        assert not missing, f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) sin claves: {sorted(missing)}"


def test_family_values_are_valid_and_complete(units: list[dict]) -> None:
    seen_families: set[str] = set()
    for i, unit in enumerate(units):
        fam = unit.get("family")
        assert fam not in (None, "unknown"), (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) con family invalida: {fam!r}"
        )
        assert fam in VALID_FAMILIES, (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) con family fuera de esquema: {fam!r}"
        )
        seen_families.add(fam)

    missing_indicator_families = INDICATOR_FAMILIES - seen_families
    assert not missing_indicator_families, (
        f"Faltan familias de indicador en el dataset: {sorted(missing_indicator_families)}"
    )


def test_section_and_block_type_in_schema(units: list[dict]) -> None:
    for i, unit in enumerate(units):
        section = unit.get("section")
        block_type = unit.get("block_type")
        assert section in VALID_SECTIONS, (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) con section invalida: {section!r}"
        )
        assert block_type in VALID_BLOCK_TYPES, (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) con block_type invalido: {block_type!r}"
        )


def test_indicator_name_present_in_most_indicator_units(units: list[dict]) -> None:
    indicator_units = [u for u in units if u.get("section") == "indicator"]
    if not indicator_units:
        pytest.skip("No hay unidades con section=='indicator' en el dataset.")

    def _has_name(u: dict) -> bool:
        name = u.get("indicator_name")
        return isinstance(name, str) and name.strip() != ""

    with_name = sum(1 for u in indicator_units if _has_name(u))
    ratio = with_name / len(indicator_units)
    assert ratio >= INDICATOR_NAME_MIN_RATIO, (
        f"Solo {with_name}/{len(indicator_units)} ({ratio:.1%}) unidades de indicador "
        f"tienen indicator_name; se requiere >= {INDICATOR_NAME_MIN_RATIO:.0%}."
    )


def test_text_is_non_empty_and_not_only_page_number(units: list[dict]) -> None:
    for i, unit in enumerate(units):
        text = unit.get("text")
        assert isinstance(text, str) and text.strip() != "", (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) con text vacio."
        )
        first_line = text.splitlines()[0] if text.splitlines() else text
        assert not PAGE_NUMBER_ONLY_RE.match(first_line), (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) empieza con un numero de pagina: "
            f"{first_line!r}"
        )


def test_text_is_not_only_layout_labels(units: list[dict]) -> None:
    """Evita unidades cuyo texto sea solo una lista de etiquetas de layout.

    Heuristica: si todas las lineas no vacias son etiquetas de layout cortas
    (p.ej. 'Header', 'Footer', 'Page 3', 'Table'), la unidad no aporta contenido.
    """
    layout_label_re = re.compile(
        r"^\s*(header|footer|page\s*\d*|figure\s*\d*|table\s*\d*|"
        r"image|caption|title|section|content|body|left|right|top|bottom)\s*:?\s*$",
        re.IGNORECASE,
    )
    for i, unit in enumerate(units):
        text = unit.get("text", "")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            continue  # ya cubierto por el test de text vacio
        all_labels = all(layout_label_re.match(ln) for ln in lines)
        assert not all_labels, (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) parece ser solo etiquetas "
            f"de layout: {lines!r}"
        )


def test_parent_doc_id_integrity(units: list[dict]) -> None:
    """Si parent_doc_id no es null, debe existir como doc_id de una unidad core."""
    core_doc_ids = {
        u.get("doc_id") for u in units if u.get("block_type") == "core"
    }
    for i, unit in enumerate(units):
        parent = unit.get("parent_doc_id")
        if parent is None:
            continue
        assert parent in core_doc_ids, (
            f"Unidad #{i} (doc_id={unit.get('doc_id')!r}) referencia "
            f"parent_doc_id={parent!r} que no existe como doc_id de una unidad core."
        )


# --------------------------------------------------------------------------- #
# TEST INTEGRATION (loaders.py).
# --------------------------------------------------------------------------- #
def _import_loaders_module():
    """Importa loaders.py desde su ruta absoluta via importlib."""
    if not LOADERS_PATH.exists():
        pytest.skip(f"loaders.py no encontrado en {LOADERS_PATH}.")
    spec = importlib.util.spec_from_file_location("rag_core_loaders", LOADERS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _detect_public_loader(module):
    """Detecta la funcion de carga publica del modulo.

    Prefiere `load_pdf`; si no, busca una funcion `load_*` sin argumentos
    obligatorios. Devuelve None si no encuentra ninguna.
    """
    if hasattr(module, "load_pdf") and callable(module.load_pdf):
        return module.load_pdf
    for name in dir(module):
        if name.startswith("load_"):
            candidate = getattr(module, name)
            if callable(candidate):
                return candidate
    return None


def test_loaders_module_imports():
    """El modulo loaders.py debe importarse sin error (skip si falta fitz)."""
    try:
        module = _import_loaders_module()
    except ModuleNotFoundError as exc:
        pytest.skip(f"Dependencia faltante para importar loaders.py: {exc}")
    assert module is not None


def test_loader_output_matches_schema():
    """Ejecuta el loader publico sobre el PDF y valida la 1a unidad.

    Hace skip si faltan dependencias (pymupdf/fitz) o el PDF de entrada.
    """
    if importlib.util.find_spec("fitz") is None:
        pytest.skip("pymupdf (import fitz) no esta instalado; se omite integracion.")

    pdfs = sorted(RAW_DIR.glob("*.pdf")) if RAW_DIR.exists() else []
    if not pdfs:
        pytest.skip(f"No hay PDF en {RAW_DIR}; se omite integracion.")

    try:
        module = _import_loaders_module()
    except ModuleNotFoundError as exc:
        pytest.skip(f"Dependencia faltante para importar loaders.py: {exc}")

    loader = _detect_public_loader(module)
    if loader is None:
        pytest.skip("No se detecto una funcion de carga publica (load_*) en loaders.py.")

    try:
        result = loader()
    except TypeError:
        pytest.skip(
            "La funcion de carga publica requiere argumentos; no se puede "
            "invocar automaticamente en este GATE."
        )

    assert isinstance(result, list) and result, (
        "El loader debe devolver una lista no vacia de dicts."
    )
    first = result[0]
    assert isinstance(first, dict), "La 1a unidad cargada no es un dict."
    missing = REQUIRED_KEYS - set(first.keys())
    assert not missing, (
        f"La 1a unidad del loader no cumple el esquema; faltan claves: {sorted(missing)}"
    )
