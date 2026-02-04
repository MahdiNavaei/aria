# ARIA Project Documentation

> **ARIA** — Adaptive Reasoning & Intelligent Automation
> 
> An **extensible personal AI assistant** that learns from its mistakes and can perform various tasks: from job applications to coding with Cursor and Desktop automation.

---

## Document Index

### 🏗️ Architecture and Vision

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | **Architecture Overview:** Brain / Hand / Eye / HITL / Learning, design principles, diagrams |
| [extensibility-architecture.md](extensibility-architecture.md) | **Extensibility Architecture:** Plugin system, Domain plugins, Task Router, Multi-domain, **MCP Protocol** |
| [unified-memory.md](unified-memory.md) | **Unified Memory System:** Working/Episodic/Semantic memory, Cross-domain learning, **Mem0 integration** |
| [user-context.md](user-context.md) | **User Context Management:** Profile, Preferences, Personalization |
| [ui-design.md](ui-design.md) | **🆕 UI Design:** Chat Panel, Live View, HITL Panel, Dashboard, WebSocket streaming |
| [data-infrastructure.md](data-infrastructure.md) | **🆕 Data Infrastructure:** Kafka (Event Bus), Redis (State), Storage (Artifacts) |

### ⚙️ Models and Resources

| Document | Description |
|----------|-------------|
| [runtime-models.md](runtime-models.md) | **Local LLM/VLM Models (Ollama):** Role mapping for Brain, Eye, Coder, ML |
| [system-specs.md](system-specs.md) | **System Specifications and Limitations:** RAM, GPU, VRAM |
| [model-management-strategy.md](model-management-strategy.md) | **Model Management Strategy:** Multiple concurrent models, cold start, configuration |
| [references-and-tools.md](references-and-tools.md) | **References and Tools:** Similar projects, recommended tools, **Clone vs Idea**, LangGraph, Mem0, MCP |

### 💻 Code Quality and Structure

| Document | Description |
|----------|-------------|
| [project-structure.md](project-structure.md) | **Folder Structure:** core, plugins, adapters, api, tests |
| [code-standards.md](code-standards.md) | **Code Quality Standards:** SOLID, Clean Code, Type Hints, Testing |

### Architecture Decision Records (ADR)

| Document | Topic |
|----------|-------|
| [adr/ADR-001-event-sourcing.md](adr/ADR-001-event-sourcing.md) | Event-Sourcing for Execution Trace (Kafka/Redpanda) |
| [adr/ADR-002-brain-hand-capability-contract.md](adr/ADR-002-brain-hand-capability-contract.md) | Separation of Brain and Hand with Capability Contract |
| [adr/ADR-003-uiref-multi-locator.md](adr/ADR-003-uiref-multi-locator.md) | UIRef as Semantic Anchor with Multi-Locator |
| [adr/ADR-004-skills-vs-policies.md](adr/ADR-004-skills-vs-policies.md) | Skills and Policies as Separate Artifacts |
| [adr/ADR-005-artifact-store-refs-only.md](adr/ADR-005-artifact-store-refs-only.md) | Artifact Store Outside Event Bus (refs only in events) |
| [adr/ADR-006-hitl-first-class.md](adr/ADR-006-hitl-first-class.md) | Human-in-the-Loop as Official Tool |
| [adr/ADR-007-vision-fallback.md](adr/ADR-007-vision-fallback.md) | Vision (Eye) Only in Failure/Ambiguity Path |
| [adr/ADR-008-content-addressed-refs.md](adr/ADR-008-content-addressed-refs.md) | Content-Addressed References for Snapshots (SHA-256) |
| [adr/ADR-009-safety-gates.md](adr/ADR-009-safety-gates.md) | Safety Gates for High-Risk Capabilities |
| [adr/ADR-010-metrics-and-success-criteria.md](adr/ADR-010-metrics-and-success-criteria.md) | **Metrics and Success Criteria** (lightweight) |
| **[adr/README.md](adr/README.md)** | **ADR Index:** ADR → Layer mapping (Brain/Hand/Eye/Learning/Safety), explicit Non-Goals, link to ADR-010 |

### Technical Specifications — System Components

| Document | Description |
|----------|-------------|
| [contracts-and-schemas.md](contracts-and-schemas.md) | **Contracts and Schemas:** UIRef, Skill, Policy, ExecutionState, CapabilityCall, Brain↔Hand Interface |
| [event-model.md](event-model.md) | Event Model Specification: topics, schema, correlation, Producer/Consumer, Canonical Timeline |
| [artifact-store.md](artifact-store.md) | Artifact Store Specification: categorization, naming, lifecycle, retention |
| [capability-catalog.md](capability-catalog.md) | Capability Catalog: MVP + revised version with JD↔Resume Matching |
| [tool-adapter-contract.md](tool-adapter-contract.md) | Tool Adapter Contract: interface, errors, Safety Gates, UIRef, Cursor/Molbot |
| [error-taxonomy.md](error-taxonomy.md) | **Error Taxonomy:** All error codes, categories, recoverable, actions |

### Technical Specifications — Matching and Learning

| Document | Description |
|----------|-------------|
| [matching-spec.md](matching-spec.md) | **JD↔Resume Matching:** Scoring layers, hard filters, LLM justification, thresholds, evidence |
| [learning-loop.md](learning-loop.md) | Learning Loop Design: signals, learning units, promotion, **safeguards and anti-poison** |
| [outcome-tracking.md](outcome-tracking.md) | **Outcome Tracking:** applied → interview → offer, calibration, analysis |

### Technical Specifications — Quality and Testing

| Document | Description |
|----------|-------------|
| [testing-strategy.md](testing-strategy.md) | **Testing Strategy:** Unit, Integration, E2E, Regression, coverage targets |
| [replay-and-regression.md](replay-and-regression.md) | **Replay and Regression:** Golden Traces, diff, metrics, CI integration |

### Technical Specifications — Safety and Operations

| Document | Description |
|----------|-------------|
| [safety-and-guardrails.md](safety-and-guardrails.md) | Safety & Guardrails: Risk classification, domain, captcha, PII, audit |
| [observability.md](observability.md) | **Observability:** Logging, Metrics (Prometheus), Tracing, Dashboards, Alerting |
| [configuration.md](configuration.md) | **Configuration Management:** .env, secrets, feature flags, validation |
| [deployment-guide.md](deployment-guide.md) | **Deployment Guide:** Local setup, Docker, Production, troubleshooting |

---

## Suggested Study Path

### Level 1: Understanding Architecture (Initial Study)
1. [architecture.md](architecture.md) — Overview, Vision, UI/Data layers
2. [extensibility-architecture.md](extensibility-architecture.md) — Plugin system, **MCP Protocol**
3. [ui-design.md](ui-design.md) — **🆕** UI design and HITL
4. [data-infrastructure.md](data-infrastructure.md) — **🆕** Kafka/Redis/Storage
5. [references-and-tools.md](references-and-tools.md) — **Clone vs Idea**, tools

### Level 2: Contracts and Components (Before Coding)
6. [contracts-and-schemas.md](contracts-and-schemas.md) — **Essential for code**
7. [unified-memory.md](unified-memory.md) — Memory system, **Mem0 integration**
8. [event-model.md](event-model.md) — Kafka events
9. [capability-catalog.md](capability-catalog.md) — Capability list
10. [error-taxonomy.md](error-taxonomy.md) — Error codes

### Level 3: Matching and Logic (Brain Coding)
11. [matching-spec.md](matching-spec.md) — JD↔Resume
12. [learning-loop.md](learning-loop.md) — Learning from Kafka events, safeguards

### Level 4: Quality and Operations (Before Production)
13. [project-structure.md](project-structure.md) — Folder structure (including ui/)
14. [code-standards.md](code-standards.md) — Code standards
15. [testing-strategy.md](testing-strategy.md) — Testing
16. [replay-and-regression.md](replay-and-regression.md) — Regression
17. [observability.md](observability.md) — Logging/metrics
18. [configuration.md](configuration.md) — Config
19. [deployment-guide.md](deployment-guide.md) — Deploy

### Level 5: Reference
- [safety-and-guardrails.md](safety-and-guardrails.md) + [adr/](adr/) — Decisions
- [runtime-models.md](runtime-models.md) — LLM/VLM models
- [outcome-tracking.md](outcome-tracking.md) — After MVP
- [system-specs.md](system-specs.md) — Hardware limitations
- [model-management-strategy.md](model-management-strategy.md) — Model management
