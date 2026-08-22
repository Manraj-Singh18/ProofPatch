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
    """Provider for a local Ollama-compatible chat endpoint."""

    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, request: AgentRequest) -> AgentResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": "You are a local coding agent. Return JSON only with keys edits and claims. Each edit has path and content. Each claim has claim_id, claim_type, assertion, and files. Never claim tests passed; ProofPatch verifies that independently."},
                {"role": "user", "content": json.dumps({"task": request.task, "repository": {"root": request.context.root, "branch": request.context.branch, "files": request.context.files, "status": request.context.status, "readme": request.context.readme}}, ensure_ascii=False)},
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
        except urllib.error.URLError as exc:
            raise LocalModelError(f"local model unavailable at {self.base_url}; start Ollama and pull {self.model}") from exc
        try:
            response_data = json.loads(raw)
            content = response_data["message"]["content"]
            data: Any = json.loads(content) if isinstance(content, str) else content
            edits = tuple(FileEdit(str(item["path"]), str(item["content"])) for item in data.get("edits", []))
            claims = tuple(Claim(str(item["claim_id"]), str(item["claim_type"]), str(item["assertion"]), tuple(str(path) for path in item.get("files", []))) for item in data.get("claims", []))
        except (KeyError, TypeError, ValueError) as exc:
            raise LocalModelError("local model returned invalid structured output") from exc
        return AgentResponse(edits=edits, claims=claims)
