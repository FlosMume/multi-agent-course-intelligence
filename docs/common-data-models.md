# Common Data Models

Pydantic v2 supplies runtime validation, JSON serialization, readable schemas,
and broad compatibility across the selected frameworks. Strict models reject
unexpected fields so configuration errors and framework-specific leakage become
visible early.

## Model groups

| Group | Models | Purpose |
|---|---|---|
| Course definition | `CourseProfile`, `LearningOutcome` | describes the teaching context |
| Evidence | `SourceDocument`, `EvidenceItem` | distinguishes supported claims from proposals |
| Work request | `CourseIntelligenceTask`, `TaskType` | supplies identical framework inputs |
| Collaboration | `AgentRole`, `AgentMessage` | records role boundaries and communication |
| Output | `CoursePlan`, `CourseModule`, `AssessmentPlan` | provides a validated common result |
| Review | `ReviewFinding`, `FindingSeverity` | records defects and recommendations |
| Evaluation | `RunTrace`, `TraceStep`, `EvaluationResult` | supports fair comparison |

## Important design choices

- Identifiers are explicit strings to keep serialized fixtures readable.
- Times are timezone-aware UTC datetimes.
- Proposed content and evidence-backed claims remain distinguishable.
- Learning outcomes and assessments link through identifiers rather than copied
  text.
- Rubric scores use a zero-to-five scale and validate their bounds.
- Extra fields are rejected to reveal incompatible adapter output.

## Versioning

Serialized benchmark cases will include a schema version. Breaking contract
changes require a new version and an ADR. Old benchmark results are not compared
directly with a new schema unless they are deliberately migrated.
