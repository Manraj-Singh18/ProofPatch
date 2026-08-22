from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .edit_loop import FileEdit
from .models import Claim
from .provider import AgentRequest, AgentResponse


class LocalModelError(RuntimeError):
    """Raised when the localhost model cannot produce a valid response."""


class LocalModelProvider:
    """Provider for a local Ollama chat endpoint."""

    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://127.0.0.1:11434", timeout: float = 90.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, request: AgentRequest) -> dict[str, Any]:
        repository = {
            "files": request.context.files,
            "status": request.context.status,
            "readme": request.context.readme,
        }
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 512},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a local coding agent. Return ONLY one JSON object. "
                        "The object must contain an edits array. Each edit has path and content. "
                        "Do not explain your answer. Do not include markdown. "
                        "Do not modify tests. ProofPatch verifies tests independently."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"task": request.task, "repository": repository}, ensure_ascii=False),
                },
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LocalModelError(
                f"local model timed out or is unavailable at {self.base_url}"
            ) from exc
        try:
            response_data = json.loads(raw)
            content = response_data["message"]["content"]
            data: Any = json.loads(content) if isinstance(content, str) else content
        except (KeyError, TypeError, ValueError) as exc:
            raise LocalModelError("local model returned invalid JSON") from exc
        if not isinstance(data, dict) or not isinstance(data.get("edits", []), list):
            raise LocalModelError("local model response must contain an edits array")
        return data

    def complete(self, request: AgentRequest) -> AgentResponse:
        data = self._request(request)
        edits = tuple(FileEdit(str(item["path"]), str(item["content"])) for item in data.get("edits", []))
        # Claims are deliberately generated locally by ProofPatch verification.
        # The model is not trusted to assert that its own changes passed tests.
        claims: tuple[Claim, ...] = ()
        return AgentResponse(edits=edits, claims=claims)
