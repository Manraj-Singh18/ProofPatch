from pathlib import Path

from proofpatch.agent_test_loop import run_test_loop
from proofpatch.edit_loop import FileEdit
from proofpatch.models import Claim


class TestEditBackend:
    def propose_edits(self, task, repo, context, previous):
        return (FileEdit("test_generated.py", "def test_generated():\n    assert True\n"),)

    def claims(self, task, repo, context):
        return (Claim("claim", "ALL_TESTS_PASS", "all tests pass"),)


class FailingBackend:
    def propose_edits(self, task, repo, context, previous):
        return (FileEdit("generated.py", "VALUE = 41\n"),)

    def claims(self, task, repo, context):
        return (Claim("claim", "ALL_TESTS_PASS", "all tests pass"),)


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "generated.py").write_text("VALUE = 1\n")
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    return tmp_path


def test_modifying_test_is_rejected(tmp_path: Path) -> None:
    run = run_test_loop(TestEditBackend(), "fix generated", _repo(tmp_path), max_attempts=1)
    assert run.accepted is False
    assert "test files" in run.verification.claims[0].reason.lower()


def test_failing_tests_override_model_claim(tmp_path: Path) -> None:
    run = run_test_loop(FailingBackend(), "fix generated", _repo(tmp_path), max_attempts=1)
    assert run.accepted is False
    assert any(result.status.value != "VERIFIED" for result in run.verification.claims)
    tests = [item for item in run.verification.evidence if item.kind == "tests"]
    assert tests
    assert tests[0].value["exit_code"] != 0
