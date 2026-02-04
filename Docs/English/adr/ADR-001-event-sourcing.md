---
title: "ADR-001: Event-Sourcing for Execution Trace (Kafka/Redpanda)"
status: Accepted
date: "2026-01-31"
owners: Brain/Platform
---

# ADR-001: Event-Sourcing for Execution Trace (Kafka/Redpanda)

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Brain/Platform

## Context

This project is an Agentic Automation Engine that must satisfy several key needs at once:

- **Replay and Regression Testing:** Automated execution on UI/web is inherently nondeterministic (UI changes, network slows, pop-ups appear). To maintain quality we must be able to replay a run as a "timeline" and measure system behavior on known traces.
- **Observability and Debuggability:** Without a structured trace, diagnosing "which step, with which tool, on which page, with what observation" failed is difficult—especially when fallbacks (vision/human) are involved.
- **Learning from real execution:** The project aims to build Skills from success traces; Policies from failure patterns; and to update UIRef/Selector from human correction. This is not reliable without a standard, joinable log.
- **Service decoupling:** Brain, Hand, Eye, HITL, and Learning must be developed loosely-coupled with minimal synchronous dependencies.

## Decision

The system uses **Event-Sourcing** to record task execution:

- Every action and its outcome are recorded as versioned, append-only events.
- Kafka/Redpanda is used as the **Event Bus**.
- Messages are lightweight and carry only **refs** (not heavy files).
- Large snapshots (screenshot/dom/observation payloads) and learning artifacts (skill/policy/ui_ref/selector) are stored in the **Artifact Store**; events only record *_ref.

**Key event types:** agent.command, agent.plan, hand.execution, hand.observation, eye.perception, human.action, learning.artifact, agent.error.

**Correlation IDs:** So that the timeline can be reconstructed, every event includes session_id, trace_id, step_id, execution_id (when applicable).

## Consequences

### Positive

- **Replay-ready by design:** replay-cli can reconstruct a run by joining hand.execution and hand.observation on execution_id.
- **Reliable regression testing:** golden traces are defined as datasets of events; algorithm/skill/policy changes are measured against them.
- **Natural learning pipeline:** the learning engine can consume events and produce artifacts without direct coupling to the runtime.
- **Decoupling and extensibility:** Brain/Hand/Eye/HITL evolve independently; only the event and capability contract are shared.
- **Better explainability:** Decisions and outcomes (especially policy triggers and human handoff) are auditable.

### Negative / Costs

- Infrastructure and operational complexity: need for a broker (Kafka/Redpanda), consumer groups, and retention management.
- Ordering / idempotency: with at-least-once delivery, consumers must be idempotent and correlation must be precise.
- Data governance: snapshots may contain PII; masking/retention and deletion workflows must be defined.
- Additional tooling: need for tools such as replay, event viewer, and artifact index.

## Alternatives Considered

- **Logging only in DB (Postgres):** ✅ Simpler for MVP; ❌ replay and ordering become harder; ❌ weaker decoupling and tighter runtime–storage coupling.
- **Plain log files (JSONL):** ✅ Fast and no infra; ❌ multi-worker and multi-service are harder; ❌ real-time consumers and observability are more difficult.
- **Monolithic agent without event bus:** ✅ Simple to start; ❌ weak scalability, replay, learning, and audit.

**Conclusion:** Given replay/learning/decoupling needs, Event-Sourcing is the best option.

## Notes / Follow-ups

- Exact topic map and schema versioning are defined in [docs/event-model.md](../event-model.md).
- Artifact Store and naming convention are specified in [docs/artifact-store.md](../artifact-store.md).
- For PII and snapshot retention, a docs/security-and-privacy.md document is needed.
- Replay determinism and golden traces are defined in docs/replay-and-regression.md.
