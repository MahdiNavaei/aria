---
title: "Event Model Specification"
version: v2
date: "2026-02-02"
---

# Event Model Specification

**Version:** v1 (2026-01-31)

## 1) Purpose

This document defines the system event standard so that:

- replay and regression testing is possible
- observability and debugging is standardized
- learning engine can consume events
- services remain loosely-coupled

## 2) High-Level Rules

### 2.1 "Refs-only" for Heavy Payloads

Kafka only carries lightweight messages. Heavy data (screenshot/DOM/artifacts) are stored in Artifact Store and only refs come in events: **screenshot_ref**, **dom_snapshot_ref**, **observation_ref**, **artifact_ref**.

### 2.2 Mandatory Correlation IDs

Every event must be joinable in the timeline.

- **Required IDs:** session_id (one run), trace_id (one goal/execution story), event_id (unique).
- **Contextual IDs:** step_id (logical step in plan), execution_id (actual execution of a capability by Hand), parent_event_id (for chaining events, optional).

## 3) Topic Map (v1)

### 3.1 Core Topics

- agent.command.v1
- agent.plan.v1
- hand.execution.v1
- hand.observation.v1
- agent.error.v1

### 3.2 Optional / Advanced Topics

- eye.perception.v1
- human.action.v1
- learning.artifact.v1

**Rule:** Minimal MVP can have only core; but schemas are defined from the start.

## 4) Base Event Envelope (Common)

All events have these fields: **schema_version** (e.g., "1.0"), **event_id**, **event_type**, **produced_at** (ISO-8601 UTC), **session_id**, **trace_id**, **step_id** (if related to step).

**Optional fields (for reproducibility and debugging):**

- **model_id** (optional): Identifier of LLM/VLM model used to produce this output (e.g., in agent.plan or eye.perception). Useful for replay and model version comparison.

**Constraints:** produced_at must be UTC; event_id must be unique at topic level; event_type must match topic (e.g., hand.execution).

## 5) Ordering & Delivery Semantics

### 5.1 Delivery Guarantee

Base assumption: **at-least-once delivery**. Therefore consumers must: be idempotent; handle duplicate events correctly (with event_id).

### 5.2 Ordering Expectation

Within one execution_id typically: first hand.execution, then hand.observation. But system must tolerate observation arriving late.

### 5.3 Partitioning Recommendation

Suggested partition key: **session_id** or **trace_id** (preferably trace_id so one goal stays in one partition).

## 6) Error Taxonomy

- **6.1 Tool/Execution-level errors (in hand.execution):** includes recoverable=true/false; examples: element_not_found, timeout, stale_element.
- **6.2 Orchestrator-level errors (in agent.error):** examples: policy_blocked, risk_gate_denied, max_retries_exceeded, invalid_goal.

## 7) Event Types (Schemas Summary)

### 7.1 agent.command (topic: agent.command.v1)

Purpose: start/stop/pause a run. **Key fields:** command (start/pause/resume/stop), goal (for start). **Use cases:** start job-apply session; pause for human handoff.

### 7.2 agent.plan (topic: agent.plan.v1)

Purpose: planner output: list of steps and capabilities. **Key fields:** plan_id, steps[]: {step_id, capability, parameters}. **Rules:** plan must be deterministic relative to state snapshot at plan time; plan change must produce new event (new plan_id).

### 7.3 hand.execution (topic: hand.execution.v1)

Purpose: result of actual execution of a capability. **Key fields:** execution_id, capability, tool_id, success, error (if fail), observation_ref (optional but recommended). **Recoverability:** if recoverable=true → Brain allowed to retry/vision/human; if recoverable=false → Brain must abort or escalate.

### 7.4 hand.observation (topic: hand.observation.v1)

Purpose: environment state after execution. **Key fields:** execution_id (for join), url, domain, page_signature, screenshot_ref, dom_snapshot_ref, blockers[], visible_ui_refs[] (optional). **Notes:** blockers can trigger policy (captcha/login_wall).

### 7.5 eye.perception (topic: eye.perception.v1)

Purpose: vision proposals for resolving element or detecting UI. **Key fields:** screenshot_ref, proposals[]: {semantic_label, confidence, bbox/ui_ref_patch}. **Rules:** Eye never executes, only proposes.

### 7.6 human.action (topic: human.action.v1)

Purpose: record human correction or confirmation. **Key fields:** action_type (click/type/scroll/drag/key_press), coordinates/text, semantic_label (very important for learning). **Notes:** This event is the basis for UIRef update and skill induction.

### 7.7 learning.artifact (topic: learning.artifact.v1)

Purpose: learning output as versioned artifact. **Key fields:** artifact_type (skill/policy/selector/ui_ref_update), artifact_id, artifact_ref, reason. **Rules:** event only gives ref; artifact payload is in store.

### 7.8 agent.error (topic: agent.error.v1)

Purpose: orchestrator-level errors. **Key fields:** severity (info/warning/error/fatal), code, message, context (optional).

## 8) Replay Contract

### 8.1 Minimal Replay Inputs

To replay a run, at minimum these are needed: all events related to one trace_id; required artifact refs: observations/snapshots, skill/policy versions (at execution time).

### 8.2 Replay Output

Sorted timeline; KPIs: success rate, retries, vision triggers, human interventions, time-to-completion.

## 9) Versioning Strategy

### 9.1 Schema version

schema_version in payload; topic version in topic name (*.v1).

### 9.2 Backward/Forward Compatibility

Adding new field: allowed (consumer should ignore). Removing/renaming field: requires major bump (v2).

## 10) Privacy & Retention Notes (High-Level)

Snapshots may contain PII; retention for events and snapshots is separate; deleting run should include: clearing snapshot refs, deleting/masking observation payloads, preserving minimal event metadata if needed (configurable).

## 11) Producer / Consumer Matrix

| Event Type       | Topic                 | Producer        | Primary Consumers                    | Purpose                              |
|------------------|-----------------------|-----------------|--------------------------------------|--------------------------------------|
| agent.command    | agent.command.v1      | UI/CLI          | Brain                                | Start/stop/pause run                 |
| agent.plan       | agent.plan.v1         | Brain           | Hand, Replay, Observability           | Publish plan and steps                |
| hand.execution   | hand.execution.v1     | Hand            | Brain, Replay, Observability, Learning | Capability execution result (success/error) |
| hand.observation | hand.observation.v1   | Hand            | Brain, Replay, Learning, Observability | Environment state after execution + refs        |
| eye.perception   | eye.perception.v1     | Eye             | Brain, Hand (indirect), Learning     | Vision proposals (bbox/labels)      |
| human.action     | human.action.v1       | HITL UI         | Brain, Learning, Replay              | Human correction/confirmation                  |
| learning.artifact| learning.artifact.v1  | Learning Engine | Brain, Replay, Observability         | Produce/update skill/policy/ui_ref/selector |
| agent.error      | agent.error.v1        | Brain           | Observability, Replay                | Orchestrator/policy/risk level errors  |

**Ownership Rules:** Brain is the only producer for agent.plan and agent.error; Hand is the only producer for hand.*; Eye is only producer for eye.perception; Human gateway is only producer for human.action; Learning engine is only producer for learning.artifact.

## 12) Canonical Timeline — Job-Apply (8 Sequential Events)

Correlation in this example: session_id = sess_20260131T092355Z_TR5C9J, trace_id = trace_3KJ8Q2M1PD.

1. **agent.command — start:** Start a goal. Key: goal.
2. **agent.plan — steps:** Brain publishes plan. Key: steps[] including step_id and capability.
3. **hand.execution — web.open_page:** Hand executes a capability with specified tool. Key: execution_id, tool_id, success=true.
4. **hand.observation — after open_page:** Environment state is recorded. Key: url/domain/page_signature, screenshot_ref, dom_snapshot_ref.
5. **hand.execution — web.detect_apply_entry (fails):** locator fails. Key: success=false, error.code=element_not_found, recoverable=true.
6. **hand.observation — blocker detected:** System realizes the real problem is captcha. Key: blockers=[captcha].
7. **human.action — user solves captcha + clicks Apply:** HITL intervenes and human correction becomes data. Key: action_type=click, semantic_label=apply_button, coordinates.
8. **learning.artifact — ui_ref_update (+ optional policy):** Learning output from human correction. Key: artifact_type=ui_ref_update, artifact_ref=...; Optional: another learning.artifact for policy: captcha_requires_human.

### 12.1 Join Rules (for replay engine)

- Main join: hand.execution.execution_id ↔ hand.observation.execution_id.
- Trigger rules: hand.observation.blockers → policy evaluation; hand.execution.error.recoverable=true → retry/vision/human decision.
- Learning linkage: human.action.semantic_label + screenshot_ref → ui_ref_update.

### 12.2 Extractable KPIs

time_to_completion, retries_count, vision_fallbacks, human_interventions, skill_reuse_rate.

## 13) Event Field Validation Rules and Content Constraints

These rules are mandatory for implementing and testing consumer/producer.

### 13.1 Required Fields (every event)

- **All events:** schema_version, event_id, event_type, produced_at (ISO-8601 UTC), session_id, trace_id.
- **hand.execution:** execution_id, capability, success; in case of failure: error.code, error.recoverable.
- **hand.observation:** execution_id (for join); at least one of: url, page_signature, screenshot_ref, dom_snapshot_ref.
- **agent.plan:** plan_id, steps[] with step_id and capability.
- **human.action:** action_type, and at least one of: semantic_label, coordinates, screenshot_ref.

### 13.2 Payload Constraints

- **Maximum payload size per message (MVP suggestion):** 256 KB. Heavy payloads should only come as refs in events.
- **Allowed ref formats:** URI with defined schemes (file://, s3:// or equivalent; or content-addressed identifier like shot_sha256_<hex>); refer to [artifact-store.md](artifact-store.md) and ADR-008.

### 13.3 PII and Prohibited Content in Events

**Never place in event payload:**

- Full resume text (resume body)
- Passwords, tokens, API keys
- Full form field content (name, email, phone as raw)
- Any data defined as PII in [safety-and-guardrails.md](safety-and-guardrails.md)

**Allowed:** only refs (e.g., candidate_profile_ref, artifact_ref), unique identifiers, and non-sensitive metadata. Refer to [safety-and-guardrails.md](safety-and-guardrails.md) section 8.

---

## 14) Related Documents

- **Data Infrastructure:** [data-infrastructure.md](data-infrastructure.md) — Kafka topics, retention, consumer groups
- **Architecture:** [architecture.md](architecture.md) — Event Bus component
- **Artifact Store:** [artifact-store.md](artifact-store.md) — ref storage
- **Learning Loop:** [learning-loop.md](learning-loop.md) — event consumption for learning
- **UI Design:** [ui-design.md](ui-design.md) — WebSocket streaming from Kafka

---

**Summary:**

> Events are published on **Kafka**. **Correlation IDs** for replay. **Refs** for heavy payloads. Kafka config details in [data-infrastructure.md](data-infrastructure.md).
