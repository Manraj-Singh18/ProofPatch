# Agent provider boundary

ProofPatch exposes a provider-neutral `ModelProvider` interface.

A provider receives:

- the user's coding task;
- deterministic repository context.

It returns:

- proposed file edits;
- claims about the resulting repository state.

The provider does not produce verification status. ProofPatch independently applies bounded edits, executes evidence collection, verifies claims, and generates the proof commitment.

A concrete hosted-model integration is intentionally separate from this interface so credentials, network access, model selection, and provider-specific policy can be reviewed independently.
