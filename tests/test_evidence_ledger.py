from pathlib import Path

from proofpatch.agent_test_loop import run_test_loop
from proofpatch.edit_loop import FileEdit


class LedgerBackend:
    raw_response = '{"edits":[{"path":"calculator.py","content":"def add(a, b):\\n    return a + b\\n"}]}'

    def propose_edits(self, task, repo, context, previous):
        return (FileEdit("calculator.py", "def add(a, b):\n    return a + b\n"),)

    def claims(self, task, repo, context):
        from proofpatch.models import Claim
        return (Claim("ledger-tests", "ALL_TESTS_PASS", "all tests pass"),)


def test_ledger_records_proposal_application_and_test_evidence(tmp_path: Path) -> None:
    (tmp_path / "calculator.py").write_text("def add(a, b):\n    return -1\n")
    (tmp_path / "test_calculator.py").write_text(
        "from calculator import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    )
    report = run_test_loop(LedgerBackend(), "fix add", tmp_path, max_attempts=1)
    assert report.accepted is True
    kinds = {item.kind for item in report.verification.evidence}
    assert {"patch", "file-hashes", "patch-application", "protected-files", "tests"} <= kinds
    patch_application = next(item for item in report.verification.evidence if item.kind == "patch-application")
    assert patch_application.value["applied_matches_proposal"] is True
    protected = next(item for item in report.verification.evidence if item.kind == "protected-files")
    assert protected.value["unchanged"] is True
    model = next(item for item in report.verification.evidence if item.kind == "model-response")
    assert model.value["raw"] == LedgerBackend.raw_response
