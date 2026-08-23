from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .edit_loop import FileEdit, _is_protected_path, _is_test_path
from .models import Claim
from .provider import AgentRequest, AgentResponse


_SOURCE_EXTENSIONS = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java")
_PLACEHOLDER_PATHS = {
    "path/to/your/file",
    "path/to/your/file.py",
    "path/to/file",
    "path/to/file.py",
}
_PROTECTED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


class LocalModelError(RuntimeError):
    """Raised when the localhost model cannot produce a valid response."""


class LocalModelProvider:
    """Provider for a local Ollama chat endpoint."""

    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://127.0.0.1:11434", timeout: float = 300.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _source_context(root: str, files: tuple[str, ...], limit: int = 12000) -> dict[str, str]:
        """Read bounded non-test source files so the local model can make grounded edits."""
        result: dict[str, str] = {}
        used = 0
        base = Path(root)
        for relative in files:
            # Do not spend the context budget on virtualenv/toolchain code. Those
            # files sort before the project's source files and previously consumed
            # the entire 12k budget before calculator.py was ever presented to the model.
            if _is_protected_path(relative) or not relative.endswith(_SOURCE_EXTENSIONS):
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
    def _test_context(root: str, files: tuple[str, ...], limit: int = 8000) -> dict[str, str]:
        """Read project tests as immutable requirements; the model may inspect them but never edit existing tests."""
        result: dict[str, str] = {}
        used = 0
        base = Path(root)
        for relative in files:
            normalized = relative.replace("\\", "/").strip("/")
            parts = normalized.split("/") if normalized else ()
            if any(part in _PROTECTED_DIRECTORIES for part in parts):
                continue
            if not _is_test_path(normalized):
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

    @staticmethod
    def _validate_edit_paths(edits: tuple[FileEdit, ...], source_context: dict[str, str]) -> None:
        """Reject placeholder or ungrounded paths before they can become a no-op patch."""
        source_paths = set(source_context)
        for edit in edits:
            path = edit.path.replace("\\", "/").strip()
            if path in _PLACEHOLDER_PATHS:
                raise LocalModelError(
                    f"local model returned a placeholder edit path: {edit.path!r}; "
                    "it must choose a real source file from the supplied source context"
                )
            if path in source_paths:
                continue
            if _is_test_path(path):
                # New regression/security tests are valid proposals. The edit loop
                # independently rejects attempts to modify an existing test file.
                continue
            if path.endswith(_SOURCE_EXTENSIONS):
                # New source files are allowed, but they must use a real source-file path.
                continue
            raise LocalModelError(
                f"local model returned an ungrounded edit path: {edit.path!r}; "
                "choose an existing source file, a new source file, or a new regression test"
            )

    def complete(self, request: AgentRequest) -> AgentResponse:
        source_context = self._source_context(request.context.root, request.context.files)
        test_context = self._test_context(request.context.root, request.context.files)
        editable_source_files = tuple(source_context)
        payload = {
            "model": self.model,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["path", "content"],
                        },
                    }
                },
                "required": ["edits"],
            },
            "options": {"temperature": 0, "num_predict": 1024, "num_ctx": 4096},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a local coding agent. Return exactly one JSON object and nothing else. "
                        "Schema: {\"edits\":[{\"path\":\"relative/path\",\"content\":\"complete file contents\"}]}. "
                        "The task must be completed by changing source code when the current source does not satisfy it. "
                        "If the task describes a failing test or requested bug fix, an empty edits array is NOT a valid solution "
                        "unless the supplied source already satisfies the task. Inspect the supplied source and read-only test "
                        "contents to determine the smallest required source change. Never modify an existing test file or an "
                        "existing test_*.py file. You MAY CREATE a new regression/security test when the task requires one. "
                        "Never modify a file under a tests/ directory that already exists. Never modify runtime/toolchain "
                        "directories such as .venv, .git, __pycache__, .pytest_cache, node_modules, or similar. Make the smallest "
                        "source-only change plus any genuinely new regression test needed. Use the supplied source and tests as "
                        "ground truth. Return complete contents for every changed or newly created file. IMPORTANT: choose edit "
                        "paths ONLY from the named files in repository.source, unless you are creating a genuinely new source or "
                        "regression test file. Do not copy placeholder/example paths such as path/to/your/file. Do not use markdown "
                        "fences or explanations."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task": request.task,
                            "repository": {
                                "editable_source_files": editable_source_files,
                                "source": source_context,
                                "tests_read_only": test_context,
                                "status": request.context.status,
                                "readme": request.context.readme,
                            },
                        },
                        ensure_ascii=False,
                    ),
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
            raise LocalModelError(f"local model timed out or is unavailable at {self.base_url} after {self.timeout:.0f}s") from exc

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
        self._validate_edit_paths(edits, source_context)
        return AgentResponse(edits=edits, claims=(), raw_response=content if isinstance(content, str) else json.dumps(content, sort_keys=True))
