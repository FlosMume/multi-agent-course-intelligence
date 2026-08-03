# ADR-001: Framework-Neutral Core

**Status:** Accepted
**Date:** 2026-08-02

## Context

The project compares four orchestration frameworks. If each implementation
defines its own inputs, outputs, tools, or evaluation method, the result becomes
four unrelated demonstrations rather than a controlled comparison.

## Decision

Create a framework-neutral domain core containing Pydantic models, structural
protocols, security rules, benchmark contracts, and evaluation records. Place
all framework code in outward adapters that depend on the core. The core must
not import any framework package.

## Consequences

Benefits include fairer comparison, reusable tests, clearer teaching, easier
model substitution, and reduced framework lock-in. Costs include conversion
code and the possibility that a framework-native feature does not fit perfectly
into the common contract. Such features may be measured as extensions, but may
not silently change the baseline task.
