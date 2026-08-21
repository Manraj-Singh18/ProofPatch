from proofpatch.models import Claim, ClaimStatus, EvidenceItem, VerificationResult


def test_claim_status_is_explicit():
    assert [status.value for status in ClaimStatus] == [
        "VERIFIED",
        "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE",
    ]


def test_verification_result_preserves_claim_and_evidence():
    claim = Claim(
        claim_id="claim-001",
        claim_type="TESTS_PASS",
        assertion="All tests pass",
    )
    evidence = EvidenceItem(
        kind="test_result",
        value={"executed": 2, "passed": 2},
        source="pytest",
    )

    result = VerificationResult(
        claim=claim,
        status=ClaimStatus.VERIFIED,
        evidence=(evidence,),
        reason="All discovered tests passed.",
    )

    assert result.claim == claim
    assert result.status is ClaimStatus.VERIFIED
    assert result.evidence == (evidence,)
