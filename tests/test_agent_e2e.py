from pathlib import Path

from proofpatch.edit_loop import FileEdit
from proofpatch.models import Claim
from proofpatch.openai_provider import OpenAIProvider
from proofpatch.provider import AgentResponse
from proofpatch.repository_context import RepositoryContext
from proofpatch.e2e_agent import run_openai_agent


class FakeResponse:
    output_text = '{"edits":[{"path":"generated.py","content":"VALUE = 42\\n"}],"claims":[{"claim_id":"e2e-1","claim_type":"ALL_TESTS_PASS","assertion":"all tests pass","files":[]}]}'


class FakeResponses:
    def create(self, **kwargs):
        return FakeResponse()


class FakeClient:
    responses = FakeResponses()


def test_e2e_flow_produces_verified_proof(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    monkeypatch.setattr(
        "proofpatch.e2e_agent.OpenAIProvider",
        lambda model: OpenAIProvider(model=model, client=FakeClient()),
    )

    report = run_openai_agent("add a generated value", tmp_path, max_attempts=2)

    assert report.accepted is True
    assert report.attempts == 1
    assert report.claims[0]["status"] == "VERIFIED"
    assert len(report.commitment) == 64


def test_e2e_flow_includes_optional_ethereum_anchor(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    from generated import VALUE\n    assert VALUE == 42\n"
    )
    monkeypatch.setattr(
        "proofpatch.e2e_agent.OpenAIProvider",
        lambda model: OpenAIProvider(model=model, client=FakeClient()),
    )
    calls = []

    def fake_anchor(commitment: str, accepted: bool):
        calls.append((commitment, accepted))
        return {"network": "Ethereum testnet", "transaction_hash": "0xabc"}

    monkeypatch.setattr("proofpatch.e2e_agent._maybe_anchor", fake_anchor)

    report = run_openai_agent("add a generated value", tmp_path, max_attempts=2)

    assert report.accepted is True
    assert report.ethereum_anchor == {"network": "Ethereum testnet", "transaction_hash": "0xabc"}
    assert calls == [(report.commitment, True)]
