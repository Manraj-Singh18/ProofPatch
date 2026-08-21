from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Sequence

from .agent_test_loop import run_test_loop
from .edit_loop import EditBackend
from .models import ClaimStatus


@dataclass(frozen=True)
class ProofReport:
    task: str
    attempts: int
    accepted: bool
    commitment: str
    claims: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    def write(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json() + "\n")


def run_with_proof_report(
    backend: EditBackend,
    task: str,
    repo: str | Path = ".",
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> ProofReport:
    """Run the bounded agent loop and materialize its verification proof report."""
    run = run_test_loop(
        backend,
        task,
        repo,
        test_command=test_command,
        max_attempts=max_attempts,
    )
    verification = run.verification
    claims = tuple(
        {
            "claim_id": result.claim.claim_id,
            "claim_type": result.claim.claim_type,
            "assertion": result.claim.assertion,
            "status": result.status.value,
            "reason": result.reason,
        }
        for result in verification.claims
    )
    evidence = tuple(
        {"kind": item.kind, "source": item.source, "value": item.value}
        for item in verification.evidence
    )
    return ProofReport(
        task=task,
        attempts=run.attempts,
        accepted=verification.verified,
        commitment=verification.commitment,
        claims=claims,
        evidence=evidence,
    )
