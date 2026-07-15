from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SAMPLES_DIR = ROOT / "data" / "samples"
PAGE = ROOT / "apps" / "web" / "src" / "app" / "documentos" / "page.tsx"
SAMPLES_README = SAMPLES_DIR / "README.md"
DEMO_PDFS = (
    "tdr-tce-01626-2023-essalud-comite-nulo.pdf",
    "tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf",
    "tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf",
    "tdr-contraloria-bid-seguimiento-contractual.pdf",
    "tdr-predes-zona-segura-los-olivos.pdf",
    "tdr-pronied-infraestructura-educativa.pdf",
)
DEMO_PDF_BASE = (
    "https://raw.githubusercontent.com/MiguelAAR10/"
    "rag-redflags-colab/main/data/samples"
)


def test_canonical_demo_pdfs_exist_once_and_have_pdf_signature() -> None:
    actual_pdfs = {path.name for path in SAMPLES_DIR.glob("*.pdf")}

    assert len(DEMO_PDFS) == 6
    assert len(set(DEMO_PDFS)) == 6
    assert actual_pdfs == set(DEMO_PDFS)
    for filename in DEMO_PDFS:
        pdf_path = SAMPLES_DIR / filename
        assert pdf_path.stat().st_size > 0
        with pdf_path.open("rb") as pdf_file:
            assert pdf_file.read(5) == b"%PDF-"


def test_documentos_page_contains_demo_catalog_raw_base_and_safe_copy() -> None:
    page_source = PAGE.read_text(encoding="utf-8")

    assert "DEMO_PDF_BASE" in page_source
    assert DEMO_PDF_BASE in page_source
    assert all(filename in page_source for filename in DEMO_PDFS)
    assert "fuentes públicas de demostración" in page_source
    assert "señales de riesgo potenciales" in page_source
    assert "requiere revisión humana" in page_source


def test_sample_documentation_uses_safe_non_accusatory_language() -> None:
    documentation = SAMPLES_README.read_text(encoding="utf-8").lower()
    for unsafe_claim in (
        "irregularidad confirmada",
        "confirman jurídicamente una irregularidad",
        "corrupción confirmada",
        "fraude confirmado",
    ):
        assert unsafe_claim not in documentation
    assert "decisiones oficiales" in documentation
    assert "requiere revisión humana" in documentation
