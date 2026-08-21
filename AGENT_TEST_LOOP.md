# Agent test loop

The coding agent may make bounded repair attempts after verification failures.

- Each attempt starts from fresh repository context.
- Edits remain constrained to the repository root.
- ProofPatch reruns verification after every attempt.
- The loop has a mandatory `max_attempts` limit.
- A run is accepted only when verification returns `VERIFIED` for every claim.

This loop does not grant unrestricted shell access or permit infinite autonomous retries.
