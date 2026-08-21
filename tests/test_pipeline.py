from pathlib import Path

from proofpatch.models import Claim, ClaimStatus
from proofpatch.pipeline import verify_repository


def test_pipeline_verifies_passing_tests_and_commits_evidence(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    claims = (Claim("c1", "ALL_TESTS_PASS", "all tests pass"),)

    report = verify_repository(tmp_path, claims)

    assert report.claims[0].status == ClaimStatus.VERIFIED
    assert len(report.commitment) == 64
    assert report.verified is True
    assert {item.kind for item in report.evidence} == {"git", "tests"}


def test_pipeline_contradicts_unexpected_file_claim(tmp_path: Path) -> None:
    import subprocess

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-b", "main")
    (tmp_path / "src.py").write_text("one\n")
    git("add", "src.py")
    git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init")
    (tmp_path / "src.py").write_text("two\n")
    (tmp_path / "extra.py").write_text("extra\n")

    claims = (Claim("c2", "ONLY_FILES_MODIFIED", "only src.py changed", files=("src.py",)),)
    report = verify_repository(tmp_path, claims)

    assert report.claims[0].status == ClaimStatus.CONTRADICTED
    assert report.verified is False


def test_pipeline_does_not_verify_unsupported_security_claim(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    claims = (Claim("c3", "SQL_INJECTION_ABSENT", "no SQL injection"),)

    report = verify_repository(tmp_path, claims)

    assert report.claims[0].status == ClaimStatus.INSUFFICIENT_EVIDENCE
    assert report.verified is False
