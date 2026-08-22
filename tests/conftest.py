from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def git_repository(tmp_path: Path) -> None:
    """Give repository-dependent tests a minimal Git history."""
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".proofpatch-test-init").write_text("init\n")
    subprocess.run(["git", "add", ".proofpatch-test-init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=ProofPatch Tests",
            "-c",
            "user.email=tests@example.com",
            "commit",
            "-m",
            "test repository init",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
