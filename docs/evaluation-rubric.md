# Evaluation Rubric

## Purpose

The rubric compares orchestration approaches, not just prose quality. Each
framework receives the same validated task, source package, model configuration,
execution limits, and scoring procedure.

## Weighted rubric

| Dimension | Weight | Evidence |
|---|---:|---|
| Correctness and requirement coverage | 20% | acceptance checks and expert review |
| Evidence grounding and traceability | 15% | valid citations and unsupported-claim count |
| Instruction following | 10% | constraint and exclusion checks |
| Output structure and validation | 10% | schema-validation pass rate |
| Reliability and recovery | 10% | repeated runs and injected failures |
| Multi-agent coordination | 10% | handoffs, duplication, conflict resolution |
| Observability and explainability | 10% | trace completeness and decision visibility |
| Security and boundary compliance | 10% | denied-action and prompt-injection tests |
| Runtime efficiency and cost | 5% | latency, calls, tokens, estimated cost |
| **Total** | **100%** | |

Each dimension is scored from 0 to 5. The weighted percentage is:

```text
sum((dimension score / 5) × dimension weight)
```

## Score anchors

| Score | Meaning |
|---:|---|
| 0 | absent, unusable, or unsafe |
| 1 | major failures; substantial intervention required |
| 2 | partially works but important requirements are missed |
| 3 | acceptable baseline with visible limitations |
| 4 | strong result with minor correctable issues |
| 5 | complete, reliable, well-evidenced, and exemplary |

## Experimental controls

- same benchmark-case version and input ordering;
- same model and sampling parameters within a comparison group;
- fresh run state unless memory is the feature being tested;
- identical maximum turns, timeouts, and tool permissions;
- at least three runs for stochastic scenarios;
- separate reporting for local and cloud models;
- raw measurements retained alongside interpreted scores.

## Automated measures

- schema-valid output rate;
- required-section coverage;
- outcome-assessment link integrity;
- citation resolution rate;
- unsupported-claim count;
- completion, timeout, and retry rates;
- tool-denial compliance;
- latency, model calls, and token estimates;
- trace-field completeness.

## Human review

An instructor reviews pedagogical coherence, realism, usefulness, clarity, and
whether human judgment was requested at appropriate points. Reviewers score
blind to framework name where practical.

## Interpretation rules

A total score is not sufficient by itself. The final report must include the
dimension profile, variability, failure modes, implementation complexity, and
qualitative suitability. A security score below 3 prevents a framework variant
from being recommended, regardless of its total score.
