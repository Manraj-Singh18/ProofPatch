from proofpatch.models import Claim, ClaimStatus, EvidenceItem
from proofpatch.verifier import verify_claim


def test_sql_injection_claim_is_not_verified_without_security_evidence() -> None:
    claim = Claim(
        "sql-1",
        "SQL_INJECTION_ABSENT",
        "the application is protected against SQL injection",
        files=("src/db.py",),
    )
    evidence = (
        EvidenceItem(
            kind="git",
            value={"changed_files": ["src/db.py"]},
            source="git status --porcelain",
        ),
    )

    result = verify_claim(claim, evidence)

    assert result.status == ClaimStatus.INSUFFICIENT_EVIDENCE


def test_sql_injection_evidence_is_explicitly_not_treated_as_generic_test_success() -> None:
    claim = Claim(
        "sql-2",
        "SQL_INJECTION_ABSENT",
        "the application is protected against SQL injection",
    )
    evidence = (
        EvidenceItem(
            kind="tests",
            value={"all_tests_pass": True},
            source="pytest -q",
        ),
    )

    result = verify_claim(claim, evidence)

    assert result.status == ClaimStatus.INSUFFICIENT_EVIDENCE
