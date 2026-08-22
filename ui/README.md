# ProofPatch UI

Minimal browser UI for the localhost ProofPatch API.

## Run

From the repository root, start the API:

```bash
python -m proofpatch.http_api
```

Serve this directory from a second terminal:

```bash
cd ui
python -m http.server 8080
```

Open `http://127.0.0.1:8080`.

The API remains bound to `127.0.0.1` and the browser sends requests only to the local ProofPatch service.
