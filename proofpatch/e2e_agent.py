from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .agent_test_loop import run_test_loop
from .openrouter_provider import OpenRouterProvider
from .proof_report import ProofReport
from .provider import ProviderBackend


def _report(task: str, run) -> ProofReport:
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


def run_openrouter_agent(
    task: str,
    repo: str | Path = ".",
    model: str = "nvidia/nemotron-3.5-lightning:free",
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> ProofReport:
    """Run the OpenRouter-backed agent through bounded verification."""
    backend = ProviderBackend(OpenRouterProvider(model=model))
    return _report(
        task,
        run_test_loop(
            backend,
            task,
            repo,
            test_command=test_command,
            max_attempts=max_attempts,
        ),
    )
