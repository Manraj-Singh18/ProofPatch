# OpenAI provider

The OpenAI provider is an optional model adapter. It reads credentials through the OpenAI SDK environment configuration and does not store secrets in the repository.

The model receives the task plus bounded repository context and returns structured edits and claims. ProofPatch then applies the edits within its repository boundary and independently verifies the claims.

The provider never supplies `VERIFIED`, `CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`; those statuses are produced only by ProofPatch.
