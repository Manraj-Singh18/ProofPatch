from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .edit_loop import FileEdit, _is_test_path
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

    @staticmethod
    def _source_context(root: str, files: tuple[str, ...], limit: int = 16000) -> dict[str, str]:
        """Read a bounded set of non-test source files so the local model can make grounded edits."""
        result: dict[str, str] = {}
        used = 0
        base = Path(root)
        for relative in files:
            if _is_test_path(relative) or not relative.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java")):
                continue
            path = base / relative
            if not path.is_file():
                continue
            try:
                content = path.read_text(errors="replace")
            except OSError:
                continue
            remaining = limit - used
            if remaining <= 0:
                break
            result[relative] = content[:remaining]
            used += min(len(content), remaining)
        return result

    @staticmethod
    def _parse_content(content: str) -> dict[str, Any]:
        """Parse JSON even when a local model adds fences or a short preamble."""
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        decoder = json.JSONDecoder()
        candidates = [text]
        start = text.find("{")
        if start >= 0 and start != 0:
            candidates.append(text[start:])
        for candidate in candidates:
            try:
                value, _ = decoder.raw_decode(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise LocalModelError("local model returned invalid or truncated JSON")

    def complete(self, request: AgentRequest) -> AgentResponse:
        source_context = self._source_context(request.context.root, request.context.files)
        payload = {
            "model": self.model,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {"edits": {"type": "array", "items": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
                "required": ["edits"],
            },
            "options": {"temperature": 0, "num_predict": 2048},
            "messages": [
                {"role": "system", "content": "You are a local coding agent. Return exactly one JSON object and nothing else. Schema: {\"edits\":[{\"path\":\"relative/path\",\"content\":\"complete file contents\"}]}. Never modify any test file, test_*.py file, or file under a tests/ directory. Make the smallest source-only change needed for the task. Use the supplied source contents as ground truth. Do not use markdown fences or explanations."},
                {"role": "user", "content": json.dumps({"task": request.task, "repository": {"files": request.context.files, "status": request.context.status, "readme": request.context.readme, "source": source_context}}, ensure_ascii=False)},
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
        except (KeyError, TypeError, ValueError) as exc:
            raise LocalModelError("local model returned an invalid Ollama response") from exc
        data = self._parse_content(content if isinstance(content, str) else json.dumps(content))
        if not isinstance(data.get("edits", []), list):
            raise LocalModelError("local model JSON did not contain an edits array")
        try:
            edits = tuple(FileEdit(str(item["path"]), str(item["content"])) for item in data["edits"])
        except (KeyError, TypeError) as exc:
            raise LocalModelError("local model JSON contained an invalid edit") from exc
        return AgentResponse(edits=edits, claims=(), raw_response=content if isinstance(content, str) else json.dumps(content, sort_keys=True))
