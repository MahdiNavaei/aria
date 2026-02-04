---
title: "ADR-002: Separation of Brain and Hand via Capability Contract"
status: Accepted
date: "2026-01-31"
owners: Brain/Runtime
---

# ADR-002: Separation of Brain and Hand via Capability Contract

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Brain/Runtime

## Context

The project aims to build an agentic system that can perform real tasks in the environment (web/desktop/IDE), under these constraints:

- **Diverse, swappable backends:** In MVP, browser automation may be Playwright; in later phases Desktop RPA or Molbot tools or Cursor integration may be added. If the "brain" calls tools directly, changing the backend would require changing the Brain, making the project brittle over time.
- **Testability and independent development:** Brain must be testable without real UI execution; Hand must be testable without changing decision logic.
- **Determinism and observability:** UI execution involves timeouts, retries, selector resolution, and recording observations; these concerns are better centralized in an execution layer so a standard trace is produced.
- **Learning support:** Learning needs standard "execution/observation" outputs. If each tool returns its own format, learning becomes hard and fragile.

## Decision

The system is split into two main layers:

- **Brain (Orchestrator):** Decision-maker and planner
- **Hand (Executor):** Executor of capabilities

The formal interface between these layers is a **Capability Contract**:

- **Brain only produces a CapabilityCall:** capability (name), parameters (inputs), context (ExecutionContext including session/step/page refs).
- **Hand only returns an ExecutionResult:** success, output (logical result of the capability), observation or observation_ref (environment state + refs), error (code/message/recoverable).

**Key rules:**

- Brain **must not** call tools (Playwright/Molbot/Desktop/Cursor) directly.
- Hand **must not** perform planning or high-level decision-making.
- Tool selection (tool_id) is entirely inside Hand (tool routing).
- Resolving ui_ref and locator strategy is inside Hand.

## Consequences

### Positive

- **Backend-agnostic Brain:** Adding Desktop/Molbot/Cursor only requires adding an adapter, without changing Brain.
- **Isolation of concerns:** retries/timeouts/selector resolution/observation capturing are centralized in Hand.
- **Consistent observability:** A standard trace is produced for learning and replay.
- **Better testability:** Brain is tested with a mock Hand; Hand is tested with a mock environment.
- **Team scalability:** Different people can develop Brain and Hand independently.

### Negative / Costs

- Need for careful capability catalog design: if capabilities are poorly designed (too granular or too vague), maintenance cost rises.
- Contract and schema overhead: schema, versioning, and backward compatibility must be managed.
- Cross-layer debugging: strong correlation IDs and tooling (replay viewer) are needed to trace back-and-forth.

## Alternatives Considered

- **Brain calls tools directly:** ✅ Faster for a small MVP; ❌ tight coupling to tools and backend; ❌ harder to change tools and extend later; ❌ reduced testability and standard replay.
- **Monolithic agent (framework-centric):** ✅ Simpler development initially; ❌ brittle at scale and with UI/tool changes; ❌ learning and observability scattered and implementation-dependent.
- **Traditional workflow engine (classic RPA):** ✅ Good for deterministic flows; ❌ insufficient for dynamic environments and reasoning/learning; ❌ human correction does not become training data without a separate architecture.

**Conclusion:** Separating Brain and Hand with a capability contract gives the best balance of extensibility, testability, and forward compatibility.

## Notes / Follow-ups

- Capability Catalog and schemas are defined in docs/capabilities.md (or [capability-catalog.md](../capability-catalog.md)).
- ExecutionState and policy/skill integration are defined in docs/orchestration-loop.md.
- New tools are added only via adapters/ and tool_id registration.
- Error code and recoverability standards are specified in docs/failure-handling.md.
