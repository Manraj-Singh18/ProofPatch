from pathlib import Path

from proofpatch.agent_test_loop import run_test_loop
from proofpatch.edit_loop import FileEdit
from proofpatch.models import Claim
from proofpatch.pipeline import verify_repository


class MismatchedBackend:
    def propose_edits(self, task, repo, context, previous):
        return (FileEdit("generated.py", "VALUE = 42\n"),)

    def claims(self, task, repo, context):
        return (Claim("claim", "ALL_TESTS_PASS", "all tests pass"),)


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "generated.py").write_text("VALUE = 1\n")
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    return tmp_path


def test_proposed_patch_must_match_actual_file_content(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    backend = MismatchedBackend()
    import proofpatch.agent_test_loop as loop
    original_apply = loop._apply_edits

    def apply_mismatched(repo, edits):
        (repo / "generated.py").write_text("VALUE = 43\n")

    loop._apply_edits = apply_mismatched
    try:
        run = run_test_loop(backend, "fix generated", root, max_attempts=1)
    finally:
        loop._apply_edits = original_apply

    assert run.accepted is False
    application = [item for item in run.verification.evidence if item.kind == "patch-application"]
    assert application
    assert application[0].value["matches_proposed"] is False


def test_evidence_commitment_detects_tampering(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "generated.py").write_text("VALUE = 42\n")
    report = verify_repository(root, (Claim("claim", "ALL_TESTS_PASS", "all tests pass"),), test_command=("pytest", "-q"))
    evidence = list(report.evidence)
    evidence[0] = type(evidence[0])(evidence[0].kind, evidence[0].source, {"tampered": True}, evidence[0].metadata)
    tampered = type(report)(report.claims, tuple(evidence), report.commitment)
    assert report.commitment_valid() is True
    assert tampered.commitment_valid() is False
