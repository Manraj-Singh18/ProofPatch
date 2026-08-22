from pathlib import Path

from proofpatch.agent_test_loop import run_test_loop
from proofpatch.edit_loop import FileEdit


class SourceOnlyBackend:
    def propose_edits(self, task, repo, context, previous):
        return (FileEdit("calculator.py", "def add(a, b):\n    return a + b\n"),)

    def claims(self, task, repo, context):
        return ()


class TestEditingBackend:
    def propose_edits(self, task, repo, context, previous):
        return (FileEdit("test_calculator.py", "def test_add():\n    assert True\n"),)

    def claims(self, task, repo, context):
        return ()


def _fixture(tmp_path: Path) -> Path:
    (tmp_path / "calculator.py").write_text("def add(a, b):\n    return -1\n")
    (tmp_path / "test_calculator.py").write_text(
        "from calculator import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    )
    return tmp_path


def test_source_edit_is_allowed(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    run = run_test_loop(SourceOnlyBackend(), "fix add", root, max_attempts=1)
    assert (root / "calculator.py").read_text().strip() == "def add(a, b):\n    return a + b"


def test_test_edit_is_rejected(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    run = run_test_loop(TestEditingBackend(), "fix add", root, max_attempts=1)
    assert run.accepted is False
    assert "test_calculator.py" in run.verification.claims[0].reason
    assert (root / "test_calculator.py").read_text().startswith("from calculator import add")
