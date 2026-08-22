import json
import threading
import urllib.request

from http.server import ThreadingHTTPServer

from proofpatch.http_api import ProofPatchHandler


def test_http_api_create_and_get_job() -> None:
    ProofPatchHandler.service = __import__("proofpatch.api", fromlist=["LocalAgentService"]).LocalAgentService()
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProofPatchHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        request = urllib.request.Request(
            base + "/jobs",
            data=json.dumps({"task": "fix add", "repo": "."}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            assert response.status == 201
            job = json.loads(response.read())
        assert job["status"] == "queued"

        with urllib.request.urlopen(base + "/jobs/" + job["id"]) as response:
            assert response.status == 200
            fetched = json.loads(response.read())
        assert fetched["id"] == job["id"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
