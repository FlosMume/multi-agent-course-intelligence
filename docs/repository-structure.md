# Repository Structure

```text
multi-agent-course-intelligence/
├── docs/                    # Charter, architecture, governance, and records
├── examples/                # Later: synthetic inputs and expected outputs
├── src/course_intelligence/
│   ├── config.py            # Local-first validated settings
│   ├── models/              # Shared framework-neutral contracts
│   └── protocols/           # Model-client and orchestrator interfaces
├── tests/
│   ├── fakes/               # Deterministic model test double
│   └── test_*.py            # Offline contract and settings tests
├── .env.example             # Placeholders and safe defaults only
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

## Future additions

Framework adapters will be isolated rather than mixed into the domain layer:

```text
src/course_intelligence/adapters/
├── native/
├── langchain/
├── langgraph/
├── crewai/
└── autogen/
```

Benchmark fixtures and evaluation runners will later live under dedicated
`benchmarks/` and `evaluation/` packages. They are not created in Phase 0
because their executable behaviour belongs to later phases.

## Import rule

The `models`, `protocols`, and evaluation contracts must never import a framework
package. Adapters may import the shared core; the shared core may not import an
adapter. This one-way dependency makes the comparison maintainable and fair.
