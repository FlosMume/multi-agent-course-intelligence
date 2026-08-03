# Security Boundaries

## Trust model

User instructions, course documents, retrieved text, model output, and agent
messages are untrusted until validated. A document may provide course content;
it cannot grant permissions or change system policy.

## Boundary rules

1. Tools are denied by default and enabled through an explicit allowlist.
2. No `eval()`, arbitrary Python execution, or unrestricted shell command tool.
3. File tools are confined to configured project-data directories.
4. Unit tests cannot call the network, Ollama, or a cloud provider.
5. Cloud inference is disabled by default and requires explicit configuration.
6. Secrets never appear in source code, fixtures, logs, prompts, or Git history.
7. Agent loops have maximum turns, timeouts, and output-size limits.
8. Model output must pass schema and domain validation before use.
9. Errors are returned as structured failures; silent fallback is prohibited.
10. Traces exclude secrets and minimize copied source content.

## Prohibited data and actions

- identifiable student records, grades, accommodations, or disciplinary data;
- autonomous grading, admission, employment, or disciplinary decisions;
- sending messages or publishing content;
- purchasing, financial transactions, or account changes;
- deleting or overwriting external files;
- installing software or changing infrastructure through an agent tool;
- bypassing authentication, permissions, or safety controls.

## Human-approval gates

Human approval is required before:

- changing the official course outline or assessment weighting;
- accepting a final course plan;
- using non-public or sensitive source material;
- enabling a cloud provider;
- adding a new tool permission;
- publishing benchmark conclusions;
- pushing the repository to a public remote.

## Prompt-injection defence

Course documents are wrapped as data and labelled with their source. The system
ignores embedded instructions that request secrets, tool access, policy changes,
or communication outside the task. Tests will include malicious document text
to verify that adapters preserve these boundaries.

## Threat scenarios for later phases

| Scenario | Expected behaviour |
|---|---|
| Document says “ignore previous rules” | treat it as quoted course content |
| Model requests an unknown tool | deny and record the request |
| Output contains an unknown field | fail validation and request correction |
| Ollama is unavailable | return a bounded, actionable error |
| Turn limit is reached | stop and return an incomplete status |
| Cloud flag is false but cloud model is named | configuration validation fails |

## Logging and retention

Logs use trace identifiers and operational metadata. Full prompts and documents
are not logged by default. Runtime logs and generated artifacts remain ignored
by Git until a reviewed, sanitized example is deliberately promoted to a fixture.
