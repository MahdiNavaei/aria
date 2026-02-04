# ADR Index (Architecture Decision Records)

This document is the map of ARIA ADRs: **which ADR connects to which layer** and the project's **explicit Non-Goals**.

---

## 1) ADR-to-Layer Map

| ADR | Topic | Brain | Hand | Eye | Learning | Safety | Data/Cross |
|-----|--------|:-----:|:----:|:---:|:--------:|:------:|:----------:|
| [ADR-001](ADR-001-event-sourcing.md) | Event-Sourcing (Kafka/Redpanda) | ● | ● | ● | ● | — | ● Event Bus |
| [ADR-002](ADR-002-brain-hand-capability-contract.md) | Separation of Brain and Hand via Capability Contract | ● | ● | — | — | — | — |
| [ADR-003](ADR-003-uiref-multi-locator.md) | UIRef as Semantic Anchor with Multi-Locator | ● | ● | — | ● | — | — |
| [ADR-004](ADR-004-skills-vs-policies.md) | Skills and Policies as Separate Artifacts | ● | — | — | ● | — | — |
| [ADR-005](ADR-005-artifact-store-refs-only.md) | Artifact Store outside Event Bus (refs-only) | — | ● | — | ● | — | ● Artifact Store |
| [ADR-006](ADR-006-hitl-first-class.md) | Human-in-the-Loop as First-Class Tool | ● | ● | — | ● | ● | — |
| [ADR-007](ADR-007-vision-fallback.md) | Vision (Eye) Only on Failure/Ambiguity Path | ● | ● | ● | — | — | — |
| [ADR-008](ADR-008-content-addressed-refs.md) | Content-Addressed References (SHA-256) for Snapshot | — | ● | — | ● | — | ● Artifact Store |
| [ADR-009](ADR-009-safety-gates.md) | Safety Gates for High-Risk Capabilities | ● | — | — | — | ● | — |
| [ADR-010](ADR-010-metrics-and-success-criteria.md) | Success Criteria and System Metrics | ● | ● | — | ● | — | ● Observability |

**Note:** ● = This layer is directly affected by the decision or owns its implementation.

---

## 2) Explicit Non-Goals

The project **deliberately** does not do the following. Defining Non-Goals explicitly reflects design maturity and scope of responsibility.

| Non-Goal | Brief description |
|--------|-------------|
| **Bypass Captcha** ❌ | The system is not designed to bypass or break captcha. When facing captcha/anti-bot: **require_human** and pause; continue after human action. |
| **Full Automation Without Human** ❌ | Full automation with no human checkpoint is not a goal. High-risk actions (submit, upload, login) require human confirmation by default. |
| **Replace Human Judgment on Apply/Skip** ❌ | The final decision "apply or not" may be delegated to the human (agent.decide → review). The system does not blindly apply to all listings. |
| **Store Raw PII in Events** ❌ | Raw PII (e.g. form text, resume) is not stored in events; only refs and metadata for audit. |
| **Tool as Decision-Maker** ❌ | Tools (Hand adapters) do not make decisions or learn; they only execute primitive actions. Brain and Learning are separate. |
| **Vision-First for Every Step** ❌ | Eye is only activated on the failure/ambiguity path; not as the default path for every step (per ADR-007). |

**References:** Safety and Captcha details in [safety-and-guardrails.md](../safety-and-guardrails.md); Safety Gates in [ADR-009](ADR-009-safety-gates.md).

---

## 3) Metrics and Success Criteria

A lightweight ADR defining **which metrics define system success** is in a separate document:

→ **[ADR-010: Metrics and Success Criteria](ADR-010-metrics-and-success-criteria.md)**

---

## 4) Suggested ADR Reading Order

1. **Execution and data foundation:** ADR-001 → ADR-002 → ADR-005 → ADR-008  
2. **UI and fallback:** ADR-003 → ADR-007  
3. **Learning and policy:** ADR-004 → ADR-006  
4. **Safety:** ADR-009 + [safety-and-guardrails.md](../safety-and-guardrails.md)  
5. **Evaluation:** ADR-010 (metrics)
