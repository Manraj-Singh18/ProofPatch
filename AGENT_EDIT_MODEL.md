# Agent edit-loop boundary

The first edit loop is intentionally narrow:

- the backend proposes complete file replacements;
- paths must resolve inside the repository;
- edits are applied once per run;
- ProofPatch independently collects post-edit evidence;
- claims are accepted only when deterministic verification returns `VERIFIED`.

This is not yet an autonomous retry loop, shell executor, or LLM provider integration. Those are separate tasks so the safety boundary remains reviewable.
