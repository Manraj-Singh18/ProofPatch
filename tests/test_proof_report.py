from pathlib import Path

from proofpatch.edit_loop import FileEdit
from proofpatch.models import Claim
from proofpatch.proof_report import run_with_proof_report


class Backend:
    def propose_edits(self, task, repo: Path, context, previous):
        return (FileEdit("generated.py", "VALUE = 42\n"),)

    def claims(self, task, repo: Path, context):
        return (Claim("report-1", "ALL_TESTS_PASS", "all tests pass"),)


def test_proof_report_contains_verification_and_commitment(tmp_path: Path) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )

    report = run_with_proof_report(Backend(), "add generated value", tmp_path)

    assert report.accepted is True
    assert report.attempts == 1
    assert len(report.commitment) == 64
    assert report.claims[0]["status"] == "VERIFIED"
    assert {item["kind"] for item in report.evidence} == {
        "git",
        "tests",
        "patch",
        "file-hashes",
        "patch-application",
        "protected-files",
    }

    output = tmp_path / "proof.json"
    report.write(output)
    assert '"accepted": true' in output.read_text()
    assert report.to_json().endswith("}\n") is False
