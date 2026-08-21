from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceRequirement(str, Enum):
    TEST_EXECUTION = "test_execution"
    GIT_STATE = "git_state"
    SECURITY_ANALYSIS = "security_analysis"


@dataclass(frozen=True)
class ClaimPolicy:
    claim_type: str
    required_evidence: frozenset[EvidenceRequirement]
    supported: bool


POLICIES = {
    "ALL_TESTS_PASS": ClaimPolicy(
        "ALL_TESTS_PASS", frozenset({EvidenceRequirement.TEST_EXECUTION}), True
    ),
    "ONLY_FILES_MODIFIED": ClaimPolicy(
        "ONLY_FILES_MODIFIED", frozenset({EvidenceRequirement.GIT_STATE}), True
    ),
    "SQL_INJECTION_ABSENT": ClaimPolicy(
        "SQL_INJECTION_ABSENT", frozenset({EvidenceRequirement.SECURITY_ANALYSIS}), False
    ),
}


def claim_policy(claim_type: str) -> ClaimPolicy | None:
    """Return the explicit policy for a claim type, if one exists."""
    return POLICIES.get(claim_type)


def can_verify(claim_type: str, available: frozenset[EvidenceRequirement]) -> bool:
    """Return true only when the claim is supported and all required evidence exists."""
    policy = claim_policy(claim_type)
    return policy is not None and policy.supported and policy.required_evidence <= available
