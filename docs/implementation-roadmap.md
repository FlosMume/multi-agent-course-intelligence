# Phased Implementation Roadmap

## Phase 0 — Foundation and governance

Define the charter, architecture, environment, repository, shared contracts,
evaluation rubric, security boundaries, and roadmap. Validate the models and
offline fake client. Do not implement framework agents.

**Exit gate:** documents are consistent; core tests and lint pass; Phase 0
Completion Record is accepted.

## Phase 1 — Native Python reference workflow

Implement the smallest readable course-intelligence workflow without an agent
framework. Add Ollama through the model-client protocol, safe tool interfaces,
structured output repair, fixtures, and end-to-end offline tests.

**Teaching purpose:** reveal the mechanisms that frameworks later package.

## Phase 2 — LangChain

Express the same workflow with LangChain components. Preserve common models,
tools, limits, benchmark inputs, and observable outputs.

**Question:** how effectively does a component-and-pipeline abstraction support
this use case?

## Phase 3 — LangGraph

Implement explicit state, conditional routing, revision loops, checkpoints, and
human approval.

**Question:** when does a graph make cyclic and stateful work clearer and safer?

## Phase 4 — CrewAI

Implement the responsibilities as role-based agents and tasks, keeping the same
acceptance criteria and security boundaries.

**Question:** how well does role-oriented orchestration communicate team design
and accelerate development?

## Phase 5 — AutoGen

Implement the workflow as controlled multi-agent conversation with explicit
termination and tool rules.

**Question:** where is conversational coordination valuable, and where does it
increase unpredictability or cost?

## Phase 6 — Comparative evaluation

Run identical normal, edge, failure, and adversarial cases. Collect repeated-run
measurements, human rubric scores, implementation complexity, and qualitative
observations.

**Exit gate:** results are reproducible and claims distinguish measurement from
interpretation.

## Phase 7 — Teaching and portfolio packaging

Produce lesson plans, lab instructions, annotated code tours, demonstrations,
interview explanations, diagrams, a technical report, and a repository landing
page. Sanitize and license all public examples.

## Chat organization

The current conversation remains the umbrella chat. A separate chat may be used
for each implementation phase to keep working context manageable. Each phase
chat begins with the preceding Completion Record and ends with a new record for
the umbrella chat.
