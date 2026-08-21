# ProofPatch Coding Agent

The coding agent follows a verification-first model:

1. The model backend receives a coding task and repository path.
2. The backend makes repository changes and returns structured claims.
3. ProofPatch independently collects Git and test evidence.
4. Claims are verified against that evidence.
5. A run is accepted only when every supplied claim is `VERIFIED`.

Unsupported or under-evidenced claims never constitute agent success.

The current runtime intentionally separates the model adapter from verification. A future backend can wrap an actual coding model without changing the verification boundary.
