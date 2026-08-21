from __future__ import annotations

from .models import Claim, ClaimStatus, EvidenceItem, VerificationResult


def _result(claim: Claim, status: ClaimStatus, evidence: tuple[EvidenceItem, ...], reason: str) -> VerificationResult:
    return VerificationResult(claim=claim, status=status, evidence=evidence, reason=reason)


def verify_claim(claim: Claim, evidence: tuple[EvidenceItem, ...] = ()) -> VerificationResult:
    """Evaluate a supported claim against supplied deterministic evidence."""
    if claim.claim_type == "ALL_TESTS_PASS":
        tests = tuple(item for item in evidence if item.kind == "tests")
        if not tests:
            return _result(claim, ClaimStatus.INSUFFICIENT_EVIDENCE, (), "No test evidence supplied")
        passed = any(bool(item.value.get("all_tests_pass")) for item in tests if isinstance(item.value, dict))
        failed = any(not bool(item.value.get("all_tests_pass")) for item in tests if isinstance(item.value, dict))
        if passed and not failed:
            return _result(claim, ClaimStatus.VERIFIED, tests, "Test evidence reports all tests passing")
        return _result(claim, ClaimStatus.CONTRADICTED, tests, "Test evidence reports a failing or unsuccessful test run")

    if claim.claim_type == "ONLY_FILES_MODIFIED":
        git = tuple(item for item in evidence if item.kind == "git")
        if not git:
            return _result(claim, ClaimStatus.INSUFFICIENT_EVIDENCE, (), "No Git evidence supplied")
        actual = set()
        for item in git:
            if isinstance(item.value, dict):
                actual.update(item.value.get("changed_files", ()))
        expected = set(claim.files)
        if actual == expected:
            return _result(claim, ClaimStatus.VERIFIED, git, "Observed changed files match the claim")
        return _result(claim, ClaimStatus.CONTRADICTED, git, f"Expected {sorted(expected)}, observed {sorted(actual)}")

    return _result(claim, ClaimStatus.INSUFFICIENT_EVIDENCE, evidence, f"Unsupported claim type: {claim.claim_type}")
