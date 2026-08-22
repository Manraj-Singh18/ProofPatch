from pathlib import Path

from proofpatch.openrouter_provider import OpenRouterProvider
from proofpatch.provider import AgentRequest
from proofpatch.repository_context import RepositoryContext


class FakeMessage:
    content = '{"edits":[{"path":"calculator.py","content":"def add(a, b):\\n    return a + b\\n"}],"claims":[{"claim_id":"or-1","claim_type":"ALL_TESTS_PASS","assertion":"all tests pass","files":[]}]}'


class FakeChoice:
    message = FakeMessage()


class FakeCompletion:
    choices = [FakeChoice()]


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "nvidia/nemotron-3.5-lightning:free"
        assert kwargs["messages"][0]["role"] == "system"
        return FakeCompletion()


class FakeChat:
    completions = FakeCompletions()


class FakeClient:
    chat = FakeChat()


def test_openrouter_provider_parses_structured_response(tmp_path: Path) -> None:
    context = RepositoryContext(
        root=str(tmp_path),
        head="abc",
        branch="main",
        files=("calculator.py", "test_calculator.py"),
        status=(),
        readme="",
    )
    provider = OpenRouterProvider(client=FakeClient())
    response = provider.complete(AgentRequest("fix calculator", context))

    assert response.edits[0].path == "calculator.py"
    assert "a + b" in response.edits[0].content
    assert response.claims[0].claim_type == "ALL_TESTS_PASS"
