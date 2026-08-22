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

    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, request: AgentRequest) -> AgentResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {"edits": {"type": "array", "items": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
                "required": ["edits"],
            },
            "options": {"temperature": 0, "num_predict": 1024},
            "messages": [
                {"role": "system", "content": "You are a local coding agent. Return only JSON matching the schema. Return complete file contents for files that must change. Do not modify tests. Do not explain your answer."},
                {"role": "user", "content": json.dumps({"task": request.task, "repository": {"files": request.context.files, "status": request.context.status, "readme": request.context.readme}}, ensure_ascii=False)},
            ],
        }
        req = urllib.request.Request(f"{self.base_url}/api/chat", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LocalModelError(f"local model timed out or is unavailable at {self.base_url}") from exc

        try:
            response_data = json.loads(raw)
            content = response_data["message"]["content"]
            data: Any = json.loads(content) if isinstance(content, str) else content
        except (KeyError, TypeError, ValueError) as exc:
            raise LocalModelError("local model returned invalid or truncated JSON") from exc
        if not isinstance(data, dict) or not isinstance(data.get("edits", []), list):
            raise LocalModelError("local model JSON did not contain an edits array")
        try:
            edits = tuple(FileEdit(str(item["path"]), str(item["content"])) for item in data["edits"])
        except (KeyError, TypeError) as exc:
            raise LocalModelError("local model JSON contained an invalid edit") from exc
        return AgentResponse(edits=edits, claims=(), raw_response=content if isinstance(content, str) else json.dumps(content, sort_keys=True))
