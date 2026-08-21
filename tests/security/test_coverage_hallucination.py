from pathlib import Path

from proofpatch.test_evidence import collect_test_evidence
from proofpatch.verifier import verify_claim
from proofpatch.models import Claim, ClaimStatus, EvidenceItem


def test_claim_is_contradicted_when_suite_contains_failure(tmp_path: Path) -> None:
    (tmp_path / "test_one.py").write_text("def test_one():\n    assert True\n")
    (tmp_path / "test_two.py").write_text("def test_two():\n    assert False\n")

    evidence = collect_test_evidence(tmp_path)
    claim = Claim("coverage-1", "ALL_TESTS_PASS", "all tests pass")
    item = EvidenceItem(
        kind="tests",
        value={
            "all_tests_pass": evidence.all_tests_pass,
            "passed": evidence.passed,
            "failed": evidence.failed,
            "errors": evidence.errors,
            "exit_code": evidence.exit_code,
        },
        source="pytest -q",
    )

    result = verify_claim(claim, (item,))

    assert evidence.passed == 1
    assert evidence.failed == 1
    assert result.status == ClaimStatus.CONTRADICTED


def test_claim_is_verified_only_when_observed_suite_passes(tmp_path: Path) -> None:
    (tmp_path / "test_one.py").write_text("def test_one():\n    assert True\n")

    evidence = collect_test_evidence(tmp_path)
    claim = Claim("coverage-2", "ALL_TESTS_PASS", "all tests pass")
    item = EvidenceItem(
        kind="tests",
        value={"all_tests_pass": evidence.all_tests_pass, "passed": evidence.passed},
        source="pytest -q",
    )

    assert verify_claim(claim, (item,)).status == ClaimStatus.VERIFIED
