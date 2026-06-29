"""Tests for Agent IO helper scripts."""

import subprocess
from pathlib import Path


def test_agent_io_new_creates_run_and_updates_queue(tmp_path):
    repo = Path.cwd()
    script = repo / "scripts" / "agent-io-new.sh"

    work = tmp_path / "repo"
    (work / "progress" / "agent_io").mkdir(parents=True)
    (work / "progress" / "agent_io" / "_TEMPLATE_REQUEST.md").write_text(
        "---\nrun_id: RUN_ID\nagent: AGENT\nmodel: MODEL\nrole: ROLE\n---\n\n# REQUEST\n",
        encoding="utf-8",
    )
    (work / "progress" / "agent_io" / "_TEMPLATE_RESPONSE.md").write_text(
        "---\nrun_id: RUN_ID\nagent: AGENT\nmodel: MODEL\n---\n\n# RESPONSE\n",
        encoding="utf-8",
    )
    (work / "progress" / "agent_io" / "_TEMPLATE_REVIEW.md").write_text(
        "---\nrun_id: RUN_ID\nreviewer: dante-os\n---\n\n# REVIEW\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "bash",
            str(script),
            "claude",
            "final-ragas-audit",
            "--model",
            "Opus-4.8",
            "--role",
            "read-only auditor",
        ],
        cwd=work,
        text=True,
        capture_output=True,
        check=True,
    )

    run_id = result.stdout.strip().splitlines()[-1]
    run_dir = work / "progress" / "agent_io" / "runs" / run_id
    assert run_id.endswith("-claude-final-ragas-audit")
    assert (run_dir / "REQUEST.md").exists()
    assert (run_dir / "RESPONSE.md").exists()
    assert (run_dir / "REVIEW.md").exists()
    assert (run_dir / "STATUS.md").exists()

    queue = (work / "progress" / "agent_io" / "QUEUE.md").read_text(encoding="utf-8")
    assert "## Active Run" in queue
    assert f"**Run ID:** {run_id}" in queue
    assert f"progress/agent_io/runs/{run_id}/REQUEST.md" in queue
    assert f"progress/agent_io/runs/{run_id}/RESPONSE.md" in queue
    assert f"progress/agent_io/runs/{run_id}/REVIEW.md" in queue

    request = (run_dir / "REQUEST.md").read_text(encoding="utf-8")
    assert "agent: claude" in request
    assert "model: Opus-4.8" in request
    assert "role: read-only auditor" in request
