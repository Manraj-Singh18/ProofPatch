from pathlib import Path

from proofpatch.openai_provider import OpenAIProvider
from proofpatch.provider import AgentRequest
from proofpatch.repository_context import RepositoryContext


class FakeResponse:
    output_text = '{"edits":[{"path":"app.py","content":"VALUE = 1\\n"}],"claims":[{"claim_id":"c1","claim_type":"ALL_TESTS_PASS","assertion":"all tests pass","files":[]}]}'


class FakeResponses:
    def create(self, **kwargs):
        assert kwargs["model"] == "test-model"
        return FakeResponse()


class FakeClient:
    responses = FakeResponses()


def test_openai_provider_translates_structured_model_response(tmp_path: Path) -> None:
    context = RepositoryContext(
        root=str(tmp_path),
        head="abc",
        branch="main",
        files=("README.md",),
        status=(),
        readme="# Demo",
    )
    provider = OpenAIProvider(model="test-model", client=FakeClient())
    response = provider.complete(AgentRequest("add feature", context))
    assert response.edits[0].path == "app.py"
    assert response.claims[0].claim_type == "ALL_TESTS_PASS"
