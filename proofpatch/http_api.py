from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .api import LocalAgentService


_ALLOWED_ORIGINS = frozenset({
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://[::1]:8080",
})


class PatchProofHandler(BaseHTTPRequestHandler):
    service = LocalAgentService()

    def _cors_origin(self) -> str:
        origin = self.headers.get("Origin", "")
        if origin in _ALLOWED_ORIGINS:
            return origin
        return "http://127.0.0.1:8080"

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", self._cors_origin())
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            return

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid JSON"})
            return

        if parsed.path == "/jobs":
            task = payload.get("task")
            repo = payload.get("repo")
            if not isinstance(task, str) or not task.strip() or not isinstance(repo, str) or not repo.strip():
                self._json(400, {"error": "task and repo are required"})
                return
            job = self.service.submit(task, repo)
            self._json(201, self.service.as_dict(job.id) or {})
            return

        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "run":
            job = self.service.get(parts[1])
            if job is None:
                self._json(404, {"error": "job not found"})
                return
            self.service.start(job.id)
            self._json(202, self.service.as_dict(job.id) or {})
            return
        self._json(404, {"error": "not found"})

    def do_GET(self) -> None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "jobs":
            job = self.service.as_dict(parts[1])
            if job is None:
                self._json(404, {"error": "job not found"})
            else:
                self._json(200, job)
            return
        self._json(404, {"error": "not found"})

    def log_message(self, format: str, *args) -> None:
        return


# Backwards-compatible name used by the existing test suite and integrations.
# Keep the public alias while the product-facing class uses the PatchProof name.
ProofPatchHandler = PatchProofHandler


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    """Start the local PatchProof HTTP API. It binds to localhost by default."""
    server = ThreadingHTTPServer((host, port), PatchProofHandler)
    print(f"PatchProof API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
