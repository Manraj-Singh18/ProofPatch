# End-to-end coding agent

The first complete ProofPatch agent flow is:

1. Receive a coding task.
2. Build bounded repository context.
3. Ask the configured OpenAI provider for structured edits and claims.
4. Apply edits only inside the repository.
5. Run the project's test command.
6. Verify claims independently.
7. Retry through the bounded test loop when verification fails.
8. Return a proof report containing the evidence commitment.

The model never controls the final verification decision.
