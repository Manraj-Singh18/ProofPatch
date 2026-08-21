from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .commitment import evidence_commitment
from .git_evidence import collect_git_evidence
from .models import Claim, ClaimStatus, EvidenceItem, VerificationResult
from .test_evidence import collect_test_evidence
from .verifier import verify_claim


@dataclass(frozen=True)
class VerificationReport:
    claims: tuple[VerificationResult, ...]
    evidence: tuple[EvidenceItem, ...]
    commitment: str

    @property
    def verified(self) -> bool:
        return bool(self.claims) and all(
            result.status == ClaimStatus.VERIFIED for result in self.claims
        )


def _git_item(repo: str | Path) -> EvidenceItem:
    evidence = collect_git_evidence(repo)
    return EvidenceItem(
        kind="git",
        source="git",
        value={
            "head": evidence.head,
            "branch": evidence.branch,
            "status_porcelain": evidence.status_porcelain,
            "changed_files": evidence.changed_files,
            "diff": evidence.diff,
        },
    )


def _test_item(repo: str | Path, command: Sequence[str]) -> EvidenceItem:
    evidence = collect_test_evidence(repo, command)
    return EvidenceItem(
        kind="tests",
        source=" ".join(command),
        value={
            "command": evidence.command,
            "exit_code": evidence.exit_code,
            "passed": evidence.passed,
            "failed": evidence.failed,
            "errors": evidence.errors,
            "all_tests_pass": evidence.all_tests_pass,
            "raw_output": evidence.raw_output,
        },
    )


def verify_repository(
    repo: str | Path = ".",
    claims: Sequence[Claim] = (),
    test_command: Sequence[str] = ("pytest", "-q"),
) -> VerificationReport:
    """Collect repository evidence, verify claims, and commit the evidence package."""
    evidence = (_git_item(repo), _test_item(repo, test_command))
    results = tuple(verify_claim(claim, evidence) for claim in claims)
    package = {
        "claims": [
            {
                "claim_id": result.claim.claim_id,
                "claim_type": result.claim.claim_type,
                "assertion": result.claim.assertion,
                "files": result.claim.files,
                "status": result.status.value,
                "reason": result.reason,
            }
            for result in results
        ],
        "evidence": [
            {"kind": item.kind, "source": item.source, "value": item.value}
            for item in evidence
        ],
    }
    return VerificationReport(
        claims=results,
        evidence=evidence,
        commitment=evidence_commitment(package),
    )
