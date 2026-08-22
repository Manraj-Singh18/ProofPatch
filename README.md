# PatchProof

PatchProof verifies engineering claims against deterministic repository evidence.

AI proposes the change; PatchProof independently observes the repository, protects tests, runs verification, and produces a cryptographic evidence commitment. The commitment can optionally be anchored to Ethereum as a public timestamp/notary layer.

## Development

The implementation is developed task-by-task on dedicated branches.

Current task: adversarial verification and Ethereum proof anchoring.

## Run locally

```bash
python -m pytest -q
python -m proofpatch.http_api
```

Serve `ui/` separately on port 8080.

See `ETHEREUM_ANCHOR.md` for optional Ethereum testnet anchoring.
