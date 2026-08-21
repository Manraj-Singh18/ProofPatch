from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .agent_test_loop import run_test_loop
from .openai_provider import OpenAIProvider
from .proof_report import ProofReport
from .provider import ProviderBackend


def run_openai_agent(
    task: str,
    repo: str | Path = ".",
    model: str = "gpt-5.6",
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> ProofReport:
    """Run the concrete OpenAI-backed agent through bounded verification and return its proof report."""
    from .proof_report import ProofReport

    backend = ProviderBackend(OpenAIProvider(model=model))
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
