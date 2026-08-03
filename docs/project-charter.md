# Project Charter

## Project identity

**Name:** Multi-Agent Course Intelligence System

**Type:** teaching demonstration, engineering comparison, and portfolio project

**Primary audience:** AI engineering learners, instructors, and technical reviewers
**Phase 0 date:** 2026-08-02 (America/Toronto)

## Purpose

The project will implement one course-intelligence use case four times—with
LangChain, LangGraph, CrewAI, and AutoGen—while holding the problem, inputs,
data models, model configuration, tests, and scoring criteria constant. The
goal is to teach framework selection through reproducible evidence rather than
through feature lists or isolated demonstrations.

## Teaching problem

Given a structured course brief and approved source materials, the system will
help an instructor produce and review:

1. a requirements analysis;
2. measurable learning outcomes;
3. a weekly teaching plan;
4. outcome-to-assessment alignment;
5. learning activities and resource suggestions;
6. a quality, evidence, and risk review.

All examples will use synthetic or public course information. The system is an
instructional decision-support tool; it is not an autonomous academic authority.

## Objectives

- Create a fair, framework-neutral comparison baseline.
- Demonstrate multi-agent decomposition, coordination, review, and recovery.
- Separate orchestration quality from model quality.
- Provide readable Python with type hints and explanatory comments.
- Make tests deterministic and independent of network services.
- Teach observability, evaluation, security, and human oversight as core design
  concerns rather than later additions.
- Produce credible portfolio evidence relevant to an AI engineering instructor.

## In scope

- a shared course-intelligence domain model;
- local Ollama inference and optional cloud-model adapters;
- identical benchmark cases for all implementations;
- orchestration traces, evaluation results, and comparative analysis;
- bounded, allowlisted tools;
- instructor-facing documentation, exercises, and demonstrations.

## Out of scope

- framework-specific agents during Phase 0;
- production learning-management-system integration;
- processing identifiable student records;
- autonomous grading or disciplinary decisions;
- unrestricted web, shell, email, calendar, or filesystem access;
- declaring one framework universally superior.

## Stakeholders

| Stakeholder | Interest | Responsibility |
|---|---|---|
| Project owner/instructor | teaching readiness and portfolio quality | scope, approval, interpretation |
| Learners | clear and reproducible demonstrations | execute labs and analyze evidence |
| Technical reviewers | sound design and fair comparison | review code, tests, and conclusions |
| Course users | useful planning output | provide requirements and approve results |

## Success criteria

The completed project succeeds when:

- all four implementations accept and return the same validated contracts;
- all implementations run against the same model and benchmark cases;
- offline tests pass without Ollama or cloud access;
- every substantive output can cite evidence or identify itself as a proposal;
- failures, retries, tool calls, and human interventions are observable;
- the comparison report distinguishes measured results from interpretation;
- a learner can explain when and why each framework is suitable.

## Constraints and assumptions

- Python 3.11+; Python 3.12 is the reference version.
- WSL2 Ubuntu is the development environment, with the working path beginning
  at `/home/myunix/edu/multi-agent-course-intelligence/`.
- `git init` initializes that working path before installation and validation.
- Ollama is the default inference service.
- Cloud models require explicit opt-in and separate credentials.
- Framework versions will be pinned when each framework phase begins.
- Each phase requires approval and ends with a completion record.

## Principal risks

| Risk | Mitigation |
|---|---|
| Framework APIs change | pin versions per phase and record them |
| Model variability distorts comparison | fixed model, temperature, fixtures, and repeated runs |
| Framework-specific conveniences alter the task | enforce common contracts and benchmark inputs |
| Hallucinated course requirements | evidence records, validation, and instructor review |
| Runaway agent dialogue | turn, time, output, and tool limits |
| Cloud cost or data exposure | local-first default and explicit cloud opt-in |

## Governance

Decisions that change comparison fairness, security boundaries, core data
models, or benchmark cases require an Architecture Decision Record (ADR).
Every phase records scope, files changed, validation evidence, open issues, and
the decision required for the next phase.
