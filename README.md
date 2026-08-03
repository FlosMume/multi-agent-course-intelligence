# Multi-Agent Course Intelligence System

A teaching and portfolio project for comparing LangChain, LangGraph, CrewAI,
and AutoGen against the same course-intelligence problem, data contracts,
model configuration, test cases, and evaluation rubric.

Phase 0 establishes the framework-neutral foundation. It deliberately contains
no framework-specific agents.

## Phase 0 contents

- project charter and architecture;
- reproducible local-first environment plan;
- shared Pydantic data models and Python protocols;
- security boundaries and human-approval rules;
- framework-comparison rubric;
- deterministic tests using a fake model client;
- phased implementation roadmap and completion record.

## Target environment

- WSL2 Ubuntu under `/home/myunix/edu/multi-agent-course-intelligence/`
- Python 3.11 or newer (Python 3.12 is recommended)
- Ollama as the default local inference service
- optional, explicitly enabled cloud-model configuration
- Git, Ruff, and Pytest

See [`docs/environment-plan.md`](docs/environment-plan.md) for setup and
verification commands.

## Phase 0 validation

After extracting the files, initialize the working path first, then create and
activate the environment:

```bash
cd /home/myunix/edu/multi-agent-course-intelligence/
git init
git branch -M main
python -m pip install -e '.[dev]'
python -m ruff check .
python -m pytest
```

Unit tests are offline. They must not contact Ollama or a cloud provider.

## Documentation map

- [`docs/project-charter.md`](docs/project-charter.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/environment-plan.md`](docs/environment-plan.md)
- [`docs/repository-structure.md`](docs/repository-structure.md)
- [`docs/common-data-models.md`](docs/common-data-models.md)
- [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md)
- [`docs/security-boundaries.md`](docs/security-boundaries.md)
- [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md)
- [`docs/phase-records/phase-0-completion-record.md`](docs/phase-records/phase-0-completion-record.md)

## Current status

Phase 0: complete. Phase 1 will build a small framework-neutral reference
workflow and benchmark fixtures after separate approval.
