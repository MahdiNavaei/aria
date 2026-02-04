---
title: "ADR-010: Metrics and Success Criteria (Light)"
status: Accepted
date: "2026-02-02"
owners: Brain / Learning / Platform
---

# ADR-010: Metrics and Success Criteria (Light)

**Status:** Accepted  
**Date:** 2026-02-02  
**Owners:** Brain / Learning / Platform

This ADR is lightweight: it defines **which metrics define ARIA system success** and are used for evaluation, regression, and Learning improvement.

---

## Context

For an agentic engine that automates Job-Apply we need to know:

- **When does the system work "well"?** (success rate, time to completion, number of human interventions)
- **When do we have regression?** (comparison with golden traces, locator failures)
- **How effective is Learning?** (reduction in human interventions, increase in locator success)

Without explicit metric definitions: evaluation becomes subjective; improvement cannot be measured; for MVP and public display (GitHub / interviews) the story is weak.

---

## Decision

A set of **system-level metrics** and **success criteria** are defined as follows. These are not necessarily all implemented in MVP but are recorded as the **definition of success** and **Observability target**.

### 1) Execution metrics

| Metric | Definition | Target (example) |
|-------|--------|-------------|
| **Task completion rate** | Percentage of sessions that reached "successful task completion" (e.g. one full apply). | Increase over time; before/after Learning comparison. |
| **Step success rate** | Percentage of hand.execution steps with success=true vs total steps. | Baseline for detecting regression. |
| **Human intervention count** | Number of times human.action or human.confirm was invoked in a session. | Decrease with Learning and UIRef/Skill improvement. |
| **Vision fallback rate** | Percentage of steps that succeeded via eye.perception (vision fallback). | Decrease with better locators and Learning. |
| **Time to completion** | Time from agent.command:start to task completion (or agent.error). | Decrease with Skill and optimization. |

### 2) Failure & recovery metrics

| Metric | Definition | Target (example) |
|-------|--------|-------------|
| **Recoverable failure rate** | Percentage of hand.execution failures that led to success via vision or human. | Indicates effectiveness of fallback. |
| **Blocker rate (captcha/login)** | Percentage of sessions or steps where blocker_type=captcha or login_wall was reported. | For policy and HITL; not for "reducing" via bypass. |
| **Locator failure by ui_ref** | Count of element_not_found failures per ui_ref or domain. | Identify where Learning should update UIRef. |

### 3) Learning and artifact metrics

| Metric | Definition | Target (example) |
|-------|--------|-------------|
| **Artifact promotion rate** | Number of learning.artifact items promoted to "validated" or "production". | Indicates effectiveness of Learning. |
| **UIRef coverage** | Number of ui_refs with at least one successful locator in the last N runs. | Coverage and health of UIRefs. |
| **Skill reuse count** | Number of times a skill from the Artifact Store was used and succeeded. | Value of learning assets. |

### 4) Safety and policy metrics

| Metric | Definition | Target (example) |
|-------|--------|-------------|
| **High-risk actions with confirmation** | Percentage of high-risk actions performed with human.confirm. | Should be 100% unless explicit override. |
| **Safety gate triggers** | Number of times policy caused block or pause. | For audit and policy review. |

### 5) Success criteria (high level)

- **MVP "success":** At least one end-to-end flow completed (search → extract → match → decide → apply with human confirmation) without crash; events and trace are replayable.
- **Learning "success":** At least one learning.artifact (e.g. ui_ref_update or policy) produced from a real session and stored in the Artifact Store.
- **Regression "stable":** Re-running on a golden trace (or subset) preserves or improves step success rate.

These criteria do not replace manual testing and human judgment; they are a **shared definition of success** for the team and evaluation.

---

## Consequences

### Positive

- Clear definition of "success" for display and evaluation.
- Basis for dashboard and Observability (e.g. Grafana / Kafka consumer for aggregations).
- Aligned with ADR-001 (event-sourcing) and the learning loop: metrics are derived from the same events and artifacts.

### Negative / Neutral

- Full implementation of metrics in MVP may be light (e.g. only task completion and human intervention count).
- Defining "golden trace" and regression environment requires maintenance.

---

## Notes / Follow-ups

- Exact metrics (thresholds, units, retention) are defined in a separate document or in configuration.
- If external benchmarks are used (e.g. OSWorld-style), similar metrics can be defined for comparison.
- **Alignment with Learning:** Execution and Learning metrics in this ADR align with section 7 of [learning-loop.md](../learning-loop.md) (Core KPIs and Learning KPIs); for exact definitions see learning-loop §7.
- **Dependencies:** [learning-loop.md](../learning-loop.md) (learning units and §7 metrics), [event-model.md](../event-model.md) (event types for aggregation), [safety-and-guardrails.md](../safety-and-guardrails.md) (high-risk and confirmation).
