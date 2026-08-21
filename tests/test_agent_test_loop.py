from pathlib import Path

from proofpatch.agent_test_loop import run_test_loop
from proofpatch.edit_loop import FileEdit
from proofpatch.models import Claim


class RepairBackend:
    def __init__(self):
        self.calls = 0

    def propose_edits(self, task, repo: Path, context, previous):
        self.calls += 1
        if self.calls == 1:
            return (FileEdit("generated.py", "VALUE = 41\n"),)
        return (FileEdit("generated.py", "VALUE = 42\n"),)

    def claims(self, task, repo: Path, context):
        return (Claim("loop-1", "ALL_TESTS_PASS", "all tests pass"),)


def test_test_loop_repairs_failure_with_bounded_retry(tmp_path: Path) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    run = run_test_loop(RepairBackend(), "make test pass", tmp_path, max_attempts=3)
    assert run.accepted is True
    assert run.attempts == 2


def test_test_loop_stops_at_attempt_limit(tmp_path: Path) -> None:
    class NeverRepair:
        def propose_edits(self, task, repo, context, previous):
            return (FileEdit("generated.py", "VALUE = 41\n"),)

        def claims(self, task, repo, context):
            return (Claim("loop-2", "ALL_TESTS_PASS", "all tests pass"),)

    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    run = run_test_loop(NeverRepair(), "make test pass", tmp_path, max_attempts=2)
    assert run.accepted is False
    assert run.attempts == 2
