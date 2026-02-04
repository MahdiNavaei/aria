---
title: "ARIA — Adaptive Reasoning & Intelligent Automation"
version: v3
date: "2026-02-02"
---

# Architecture Overview

> **ARIA** is an **extensible personal AI assistant**, not just a Job-Apply Agent.
> This document describes the **core** architecture. For **multi-domain and extensibility** architecture see [extensibility-architecture.md](extensibility-architecture.md).

---

## Vision: Personal AI Assistant

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ARIA — Personal AI Assistant                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                              UI Layer                                  │ │
│  │  • Chat Panel   • Live Browser View   • HITL Panel   • Dashboard      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Job-Apply  │  │   Cursor    │  │   Desktop   │  │   Future    │       │
│  │   Domain    │  │   Domain    │  │   Domain    │  │   Domains   │       │
│  │  (Phase 1)  │  │  (Phase 2)  │  │  (Phase 3)  │  │             │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         └────────────────┼────────────────┼────────────────┘              │
│                          ▼                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                       Orchestration Core                               │ │
│  │  • Task Router    • Brain (LLM)    • Policy Engine    • Learning      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                          │                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Data Infrastructure                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │    Kafka    │  │    Redis    │  │   Storage   │  │  Artifacts  │   │ │
│  │  │ (Event Bus) │  │  (State)    │  │(Snapshots)  │  │(Skills/etc) │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key principles:**
1. **Domain-agnostic Core** — Brain/Memory/Events shared across all domains
2. **Plugin-based Domains** — Each domain is a plugin (job_apply, cursor, desktop)
3. **Self-improving** — Learns from mistakes and produces artifacts
4. **User-centric** — Knows the user and personalizes
5. **UI-first HITL** — User is always in control and can intervene

**Related documents:**
- [UI Design](ui-design.md) — UI design and HITL
- [Data Infrastructure](data-infrastructure.md) — Kafka/Redis/Storage architecture
- [Extensibility Architecture](extensibility-architecture.md) — Plugin system and multi-domain
- [Unified Memory](unified-memory.md) — Cross-domain learning
- [User Context](user-context.md) — Persona management
- [Project Structure](project-structure.md) — Code organization

---

## Diagrams (C4-style)

```text
Diagram 1 — Logical Architecture (C4 Container level)
                        +----------------------+
                        |        User          |
                        |  goal / feedback     |
                        +----------+-----------+
                                   |
                                   v
+--------------------------------------------------------------------------+
|                              Brain (Orchestrator)                        |
|  - planning (capabilities)                                               |
|  - policy evaluation                                                     |
|  - skill selection/expansion                                             |
|  - supervision (retry / vision / human)                                  |
|  - state tracking                                                        |
+-------------------+----------------------+-------------------------------+
                    |                      |
                    | capability calls      | reads/writes
                    v                      v
          +-------------------+     +-----------------------+
          |    Hand (Executor)|     |    Artifact Store     |
          |  - tool routing   |     |  skills/policies/uiRef|
          |  - ui_ref resolve |     |  selectors/obs/snaps  |
          |  - deterministic  |     +-----------------------+
          +---------+---------+
                    |
                    | uses adapters (tools in hand)
                    v
        +---------------------------+
        |   Tool Adapters / Tools   |
        |  - Browser/RPA (Playwright)|
        |  - Desktop RPA (future)   |
        |  - Molbot tools (optional)|
        |  - Cursor adapter (future)|
        +-------------+-------------+
                      |
                      v
                +-----------+
                |Environment|
                | Web/OS/IDE|
                +-----------+

   (fallback perception)                         (human supervision)
          +--------------------+                +---------------------+
          |   Eye (Perception) |                | Human-in-the-Loop UI |
          | - screenshot ->    |                | - approve/override   |
          |   bbox/labels      |                | - annotate semantics |
          +---------+----------+                +----------+----------+
                    \                                   /
                     \                                 /
                      \                               /
                       v                             v
                    +--------------------------------------+
                    |             Event Bus                |
                    | (Kafka/Redpanda)                      |
                    | - execution/observation/human/artifact|
                    +--------------------------------------+
```

Key point: Brain never calls tools directly. Brain only sends capabilities to Hand.

```text
Diagram 2 — Control Flow (Happy Path)
User goal
  |
  v
Brain: plan next capability ------------------------+
  |                                                 |
  v                                                 |
Hand: route capability -> tool adapter              |
  |                                                 |
  v                                                 |
Tool executes in environment                         |
  |                                                 |
  v                                                 |
Hand emits: hand.execution + hand.observation       |
  |                                                 |
  v                                                 |
Brain updates state + (optional) triggers learning--+
```

```text
Diagram 3 — Failure Path (Vision + Human Correction + Learning)
Brain plans capability
  |
  v
Hand executes (DOM locator fails) -> hand.execution(success=false)
  |
  v
Hand emits observation (maybe blocker/captcha) -> hand.observation
  |
  v
Brain decides recovery:
  |
  +--> (A) Vision fallback:
  |       Eye consumes screenshot -> eye.perception (bbox + semantic_label)
  |       Hand retries using vision locator -> success
  |
  +--> (B) Human handoff:
          Human clicks/types -> human.action (semantic_label + coords)
          Learning generates:
             - ui_ref update / selector update
             - policy (e.g., captcha_requires_human)
          -> learning.artifact (+ artifact_ref)
```

```text
Diagram 4 — Data Flow (Events vs Artifacts)
              +---------------------+
              |     Event Bus       |
              |  (append-only log)  |
              +----+-----------+----+
                   |           |
     timeline/replay|           | references
                   v           v
       +----------------+   +-------------------+
       | Replay Engine  |   | Artifact Store     |
       | (deterministic)|   | (versioned files)  |
       +----------------+   +-------------------+

Event Bus holds:
- small messages (IDs, refs, metadata)

Artifact Store holds:
- skills/policies/ui_refs/selectors (YAML/JSON)
- snapshots (screenshot/dom/obs) via content refs
```

```text
Diagram 5 — Capability Boundary (important for architecture clarity)
Brain knows:                 Hand/Tools know:
- capability name            - how to execute it
- parameters                 - locators/selectors
- context refs               - UI tech (DOM, coords)
- policies/skills            - backend (Playwright, OS, ...)
```

---

## 0) Scope

This project is an Agentic engine for executing real tasks in digital environments (web/desktop/IDE), designed around the **Plan → Act → Observe → Learn** loop. The MVP focuses on **Job-Apply Automation** (web), but the architecture is ready from the start to extend to Desktop automation and Cursor/IDE integration.

## 1) Design Principles

- **Brain does not know tools** — Brain only works with high-level concepts like capability, parameters, and context. No direct dependency on Playwright/Molbot/Cursor.
- **Hand only executes** — Hand is a uniform execution layer (executor/actuator) whose job is: routing capability to the right tool, resolving ui_ref, and producing execution events.
- **Tools = tools in hand** — Tools are swappable backends. A tool can be Playwright, desktop RPA, Molbot tools, or a Cursor-specific adapter. Tools do not make decisions or learn.
- **Eye only enters on fallback** — Vision is activated when a DOM locator fails or environment state is ambiguous.
- **Everything is an Event** — The system is tracked with versioned events and correlation IDs so replay, observability, and learning are reliable.
- **Learning from trace and human correction** — Learning takes the form of producing reusable artifacts (Skill/Policy/UIRef/Selector), not just prompt tweaking.

## 2) System Components

### 2.1 Brain (Orchestrator)

- **Responsibilities:** Turn goal into executable plan (capability sequence), evaluate policies (guard/override/route), select skill and expand it into steps, supervise (retry/vision fallback/human handoff), maintain ExecutionState and task progress.
- **Inputs:** Events hand.execution, hand.observation, eye.perception, human.action, learning.artifact.
- **Outputs:** agent.plan (plan and steps), agent.error (control/policy/task-block errors), capability calls via Hand interface.

### 2.2 Hand (Executor)

- **Responsibilities:** Map capability to the right adapter (tool routing), deterministic execution with timeout/retry, resolve ui_ref with multi-locator strategy, produce replayable trace.
- **Outputs:** hand.execution (capability execution result), hand.observation (environment state observation with refs).

### 2.3 Tool Adapters (Tools in Hand)

Examples: Browser/RPA adapter (Playwright) for web, Desktop adapter for Windows (later phase), Molbot tools adapter (optional), Cursor adapter for coding tasks and diff/tests (Phase 3). **Rule:** Tools must not do planning/learning; only execute primitive actions.

### 2.4 Eye (Perception)

- **Responsibilities:** Consume screenshot_ref, produce proposals: semantic_label + bbox + confidence, help resolve element when DOM locator fails.
- **Output:** eye.perception.

### 2.5 Human-in-the-Loop (HITL) & UI

- **Responsibilities:** Approve/override on high-risk actions, correct path on failures (click/type), produce learning signal (semantic label + action trace).
- **Output:** human.action.
- **UI Components:** Chat Panel (command), Live Browser View (transparency), HITL Panel (intervention), Activity Log (observability).
- **Details:** [UI Design](ui-design.md)

### 2.6 Learning Engine

- **Responsibilities:** Turn execution trace and human correction into artifacts: UIRef update, Selector/Locator updates, Skill induction, Policy induction.
- **Output:** learning.artifact (with artifact_ref).

## 3) UIRef Abstraction

ui_ref is a **semantic anchor**, not a selector. Each UIRef can have multiple locators (css/xpath/role/text/vision_bbox) with confidence and source.

- UI/DOM changes, but meaning is more stable (e.g. apply_button).
- Human correction and Vision fallback can add new locators to the same UIRef.
- Skills rely on UIRef instead of fragile selectors.
- Resolve location: inside Hand (not Brain).

## 4) Skill vs Policy

- **Skill:** An execution macro: sequence of capabilities; has precondition/postcondition; goal: increase reuse and reduce time-to-completion.
- **Policy:** Decision rule for Brain; guard/override/route (e.g. require_human for captcha or submit); goal: increase safety and alignment with failure patterns.

## 5) Control Flow

### 5.1 Happy Path

User gives goal (agent.command:start) → Brain produces plan (agent.plan) → Brain builds a capability call and gives it to Hand → Hand executes and produces hand.execution → Hand produces hand.observation with refs → Brain updates state and chooses next step → Learning can build artifacts from trace in background (optional).

### 5.2 Failure & Recovery Path

- **Case A (locator failed, recoverable):** Hand: hand.execution(success=false, error=recoverable) → Brain: decides vision fallback → Eye: eye.perception (bbox/label) → Hand: retry with vision/human locator → success.
- **Case B (blocker e.g. captcha):** hand.observation reports blocker → Policy: require_human → Human: human.action → Learning: produces learning.artifact (policy + ui_ref_update).

### 5.3 High-Risk Actions

For high-risk actions (final submit, resume upload, login, sending personal data), Policy/flag can require human confirmation or block capability execution.

## 6) Data Model Overview

### 6.1 Event Bus (Kafka/Redpanda)

Key events (versioned and correlation-friendly): agent.command, agent.plan, hand.execution, hand.observation, eye.perception, human.action, learning.artifact, agent.error.  
Correlation IDs: session_id, trace_id, step_id, execution_id.

**Why Kafka:**
- **Durable** — No event is lost
- **Replayable** — For learning and regression
- **Multi-consumer** — Brain, Learning, UI all consume

**Details:** [Data Infrastructure](data-infrastructure.md)

### 6.2 State Store (Redis)

Real-time state for fast decisions:
- **Session State** — Current session state
- **Working Memory** — Context for LLM
- **Cache** — Selector cache, LLM response cache
- **Flags** — awaiting_human, pause_requested

**Why Redis:**
- **Fast** — sub-millisecond latency
- **TTL** — automatic expiry for session data
- **Pub/Sub** — real-time notifications

**Details:** [Data Infrastructure](data-infrastructure.md)

### 6.3 Artifact Store

Artifacts are stored outside Kafka; Kafka only carries artifact_ref. Types: skills, policies, ui_refs, selectors, observations/snapshots refs. Benefits: versioning, reviewable artifacts, deterministic replay.

## 7) Observability & Replay

Every run is traceable by trace_id and session_id. Replay by joining hand.execution and hand.observation on execution_id. Golden traces for regression: fewer human interventions, higher success rate, fewer retries.

## 8) Security & Privacy (High-Level)

PII in logs must be masked (especially forms and resumes). Screenshot/DOM storage must be controlled by retention policy. Third-party tools must run in sandbox. High-risk gates to prevent unwanted behavior.

## 9) Extensibility

- Add new tool: only a new adapter in adapters/, no change to Brain.
- Add new capability: add schema and mapping in Hand.
- Add Cursor integration: new adapter + coding capabilities, no change to core event model.

## 10) Example Scenarios (Summary)

- **Scenario A — Simple Apply:** open_page → find_job_cards → open_job_post → detect_apply_entry → start_flow → extract_form → fill_form → submit.
- **Scenario B — Captcha + Human Correction + Learning:** detect_apply_entry fails → blocker captcha → human action → ui_ref update + policy created → next runs require_human on captcha.

## 11) Model Stack (Runtime)

Brain, Eye, and (when needed) Coder/ML use local LLM/VLM models (e.g. Ollama). Role-to-model mapping, recommended configuration, and usage rules are in the separate document **[Runtime Model Stack](runtime-models.md)** so the architecture stays model-agnostic while implementation with existing models (e.g. Dorna/Qwen/Gemma/VLM) is specified.

---

**Related documents:**
- [UI Design](ui-design.md) — UI design
- [Data Infrastructure](data-infrastructure.md) — Kafka/Redis/Storage
- [Event Model](event-model.md) — Event schemas
- [Capability Catalog](capability-catalog.md) — Capability list
- [Runtime Models](runtime-models.md) — LLM/VLM models
- [ADR Index](adr/) — Architecture decisions
