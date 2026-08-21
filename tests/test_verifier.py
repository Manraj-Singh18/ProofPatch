from proofpatch.models import Claim, ClaimStatus, EvidenceItem
from proofpatch.verifier import verify_claim


def test_all_tests_pass_verified() -> None:
    claim = Claim("c1", "ALL_TESTS_PASS", "all tests pass")
    evidence = (EvidenceItem("tests", {"all_tests_pass": True}, "pytest"),)
    result = verify_claim(claim, evidence)
    assert result.status == ClaimStatus.VERIFIED


def test_all_tests_pass_contradicted() -> None:
    claim = Claim("c1", "ALL_TESTS_PASS", "all tests pass")
    evidence = (EvidenceItem("tests", {"all_tests_pass": False}, "pytest"),)
    result = verify_claim(claim, evidence)
    assert result.status == ClaimStatus.CONTRADICTED


def test_all_tests_pass_insufficient() -> None:
    claim = Claim("c1", "ALL_TESTS_PASS", "all tests pass")
    assert verify_claim(claim).status == ClaimStatus.INSUFFICIENT_EVIDENCE


def test_only_files_modified_verified() -> None:
    claim = Claim("c2", "ONLY_FILES_MODIFIED", "only a.py changed", files=("a.py",))
    evidence = (EvidenceItem("git", {"changed_files": ["a.py"]}, "git"),)
    assert verify_claim(claim, evidence).status == ClaimStatus.VERIFIED


def test_only_files_modified_contradicted() -> None:
    claim = Claim("c2", "ONLY_FILES_MODIFIED", "only a.py changed", files=("a.py",))
    evidence = (EvidenceItem("git", {"changed_files": ["a.py", "b.py"]}, "git"),)
    assert verify_claim(claim, evidence).status == ClaimStatus.CONTRADICTED


def test_unknown_claim_is_insufficient() -> None:
    claim = Claim("c3", "UNKNOWN", "unknown")
    assert verify_claim(claim).status == ClaimStatus.INSUFFICIENT_EVIDENCE
