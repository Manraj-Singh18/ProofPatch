from pathlib import Path

import pytest

from proofpatch.edit_loop import EditBackend, EditLoopError, FileEdit, run_edit_loop
from proofpatch.models import Claim


class Backend:
    def propose_edits(self, task: str, repo: Path, context):
        return (FileEdit("generated.py", "VALUE = 42\n"),)

    def claims(self, task: str, repo: Path, context):
        return (Claim("edit-1", "ALL_TESTS_PASS", "all tests pass"),)


class EscapeBackend:
    def propose_edits(self, task: str, repo: Path, context):
        return (FileEdit("../outside.txt", "blocked\n"),)

    def claims(self, task: str, repo: Path, context):
        return ()


def test_edit_loop_applies_edit_and_verifies(tmp_path: Path) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    run = run_edit_loop(Backend(), "add generated value", tmp_path)
    assert (tmp_path / "generated.py").read_text() == "VALUE = 42\n"
    assert run.accepted is True


def test_edit_loop_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(EditLoopError):
        run_edit_loop(EscapeBackend(), "write outside repo", tmp_path)
