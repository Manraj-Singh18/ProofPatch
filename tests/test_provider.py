from pathlib import Path

from proofpatch.edit_loop import FileEdit
from proofpatch.models import Claim
from proofpatch.provider import AgentRequest, AgentResponse, ProviderBackend


class FakeProvider:
    def complete(self, request: AgentRequest) -> AgentResponse:
        assert request.task == "add feature"
        assert request.context.branch == "main"
        return AgentResponse(
            edits=(FileEdit("app.py", "VALUE = 1\n"),),
            claims=(Claim("p1", "ALL_TESTS_PASS", "all tests pass"),),
        )


def test_provider_backend_translates_model_response(tmp_path: Path) -> None:
    class Context:
        branch = "main"

    backend = ProviderBackend(FakeProvider())
    edits = backend.propose_edits("add feature", tmp_path, Context())
    claims = backend.claims("add feature", tmp_path, Context())
    assert edits[0].path == "app.py"
    assert claims[0].claim_type == "ALL_TESTS_PASS"
