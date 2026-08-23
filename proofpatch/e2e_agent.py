from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .agent_test_loop import run_test_loop
from .local_provider import LocalModelProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider
from .proof_report import ProofReport, _maybe_anchor
from .provider import ProviderBackend


def _report(task: str, run) -> ProofReport:
    verification = run.verification
    claims = tuple(
        {
            "claim_id": r.claim.claim_id,
            "claim_type": r.claim.claim_type,
            "assertion": r.claim.assertion,
            "status": r.status.value,
            "reason": r.reason,
        }
        for r in verification.claims
    )
    evidence = tuple(
        {"kind": e.kind, "source": e.source, "value": e.value}
        for e in verification.evidence
    )
    return ProofReport(
        task=task,
        attempts=run.attempts,
        accepted=verification.verified,
        commitment=verification.commitment,
        claims=claims,
        evidence=evidence,
        ethereum_anchor=_maybe_anchor(verification.commitment, verification.verified),
    )


def run_local_agent(
    task: str,
    repo: str | Path = ".",
    model: str = "qwen2.5-coder:7b",
    base_url: str = "http://127.0.0.1:11434",
    timeout: float = 120.0,
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> ProofReport:
    """Run the coding agent entirely against a localhost Ollama model."""
    backend = ProviderBackend(LocalModelProvider(model=model, base_url=base_url, timeout=timeout))
    return _report(task, run_test_loop(backend, task, repo, test_command=test_command, max_attempts=max_attempts))


def run_openrouter_agent(
    task: str,
    repo: str | Path = ".",
    model: str = "nvidia/nemotron-3.5-lightning:free",
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> ProofReport:
    backend = ProviderBackend(OpenRouterProvider(model=model))
    return _report(task, run_test_loop(backend, task, repo, test_command=test_command, max_attempts=max_attempts))


def run_openai_agent(
    task: str,
    repo: str | Path = ".",
    model: str = "gpt-5.6",
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> ProofReport:
    backend = ProviderBackend(OpenAIProvider(model=model))
    return _report(task, run_test_loop(backend, task, repo, test_command=test_command, max_attempts=max_attempts))
