from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
CI = REPO / ".github" / "workflows" / "ci.yml"


def test_ci_runs_python_and_frontend_quality_gates():
    workflow = CI.read_text(encoding="utf-8")
    for required in (
        "actions/checkout@v6",
        "actions/setup-python@v6",
        "python -m pip install -e .",
        "python -m pytest -q",
        "actions/setup-node@v6",
        "cache-dependency-path: apps/web/package-lock.json",
        "npm ci",
        "npm run lint",
        "npm run build",
        "working-directory: apps/web",
    ):
        assert required in workflow, f"CI no ejecuta gate requerido: {required}"
