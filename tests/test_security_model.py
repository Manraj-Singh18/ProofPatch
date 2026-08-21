from proofpatch.security_model import (
    EvidenceRequirement,
    can_verify,
    claim_policy,
)


def test_supported_claim_requires_its_evidence() -> None:
    assert can_verify(
        "ALL_TESTS_PASS", frozenset({EvidenceRequirement.TEST_EXECUTION})
    ) is True
    assert can_verify("ALL_TESTS_PASS", frozenset()) is False


def test_file_scope_requires_git_state() -> None:
    assert can_verify(
        "ONLY_FILES_MODIFIED", frozenset({EvidenceRequirement.GIT_STATE})
    ) is True
    assert can_verify("ONLY_FILES_MODIFIED", frozenset()) is False


def test_security_claim_is_explicitly_unsupported() -> None:
    policy = claim_policy("SQL_INJECTION_ABSENT")
    assert policy is not None
    assert policy.supported is False
    assert can_verify(
        "SQL_INJECTION_ABSENT", frozenset({EvidenceRequirement.SECURITY_ANALYSIS})
    ) is False


def test_unknown_claim_has_no_policy() -> None:
    assert claim_policy("UNKNOWN") is None
    assert can_verify("UNKNOWN", frozenset()) is False
