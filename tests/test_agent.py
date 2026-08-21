from pathlib import Path

from proofpatch.agent import CodingAgent
from proofpatch.models import Claim, ClaimStatus


class PassingBackend:
    def solve(self, task: str, repo: Path):
        (repo / "test_agent_generated.py").write_text(
            "def test_generated():\n    assert True\n"
        )
        return (Claim("agent-1", "ALL_TESTS_PASS", "all tests pass"),)


class UnsupportedSecurityBackend:
    def solve(self, task: str, repo: Path):
        return (Claim("agent-2", "SQL_INJECTION_ABSENT", "no SQL injection"),)


def test_agent_accepts_only_verified_run(tmp_path: Path) -> None:
    run = CodingAgent(PassingBackend()).run("add a passing test", tmp_path)
    assert run.accepted is True
    assert run.verification.claims[0].status == ClaimStatus.VERIFIED


def test_agent_rejects_unverified_claim(tmp_path: Path) -> None:
    run = CodingAgent(UnsupportedSecurityBackend()).run("prove SQL safety", tmp_path)
    assert run.accepted is False
    assert run.verification.claims[0].status == ClaimStatus.INSUFFICIENT_EVIDENCE
