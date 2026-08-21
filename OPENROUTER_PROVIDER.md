# OpenRouter provider

ProofPatch can use OpenRouter as an optional OpenAI-compatible coding-model backend.

Default model:

`nvidia/nemotron-3.5-lightning:free`

Configuration:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

The provider uses the OpenAI Python SDK with OpenRouter's API base URL. It returns only structured edits and claims. Model reasoning fields are not persisted or included in proof reports.

ProofPatch independently applies bounded edits, runs tests, verifies claims, and creates the evidence commitment.
