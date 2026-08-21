# ProofPatch Security Model Boundary

ProofPatch only verifies claims for which it has an explicit claim policy and the required deterministic evidence.

## Currently supported

- `ALL_TESTS_PASS` requires test-execution evidence.
- `ONLY_FILES_MODIFIED` requires Git-state evidence.

## Explicitly unsupported

- `SQL_INJECTION_ABSENT` requires security-analysis evidence, but that evidence type is not yet implemented. The claim therefore cannot be verified.
- Unknown claim types cannot be verified.

A successful unrelated check must never be treated as evidence for a different security property. Unsupported claims resolve to `INSUFFICIENT_EVIDENCE`, not `VERIFIED`.
