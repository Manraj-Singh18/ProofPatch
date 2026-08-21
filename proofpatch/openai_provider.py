from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .edit_loop import FileEdit
from .models import Claim
from .provider import AgentRequest, AgentResponse, ModelProvider


class OpenAIProvider:
    """OpenAI-compatible coding provider using the Responses API.

    The provider returns structured edits/claims only. Verification remains
    entirely outside the model boundary.
    """

    def __init__(self, model: str = "gpt-5.6", client: Any | None = None):
        self.model = model
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError("Install the OpenAI Python SDK to use OpenAIProvider") from exc
            self._client = OpenAI()
        return self._client

    def complete(self, request: AgentRequest) -> AgentResponse:
        payload = {
            "task": request.task,
            "repository": {
                "root": request.context.root,
                "head": request.context.head,
                "branch": request.context.branch,
                "files": request.context.files,
                "status": request.context.status,
                "readme": request.context.readme,
            },
            "output_schema": {
                "edits": [{"path": "string", "content": "string"}],
                "claims": [{"claim_id": "string", "claim_type": "string", "assertion": "string", "files": ["string"]}],
            },
        }
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": "Return JSON only. Propose repository edits and claims. Never claim verification status; ProofPatch verifies claims independently.",
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        data = json.loads(response.output_text)
        edits = tuple(FileEdit(str(item["path"]), str(item["content"])) for item in data.get("edits", []))
        claims = tuple(
            Claim(
                str(item["claim_id"]),
                str(item["claim_type"]),
                str(item["assertion"]),
                tuple(str(path) for path in item.get("files", [])),
            )
            for item in data.get("claims", [])
        )
        return AgentResponse(edits=edits, claims=claims)
