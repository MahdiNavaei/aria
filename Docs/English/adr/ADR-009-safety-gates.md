---
title: "ADR-009: Safety Gates for High-Risk Capabilities (Policy-Based Confirmation)"
status: Accepted
date: "2026-01-31"
owners: Safety/Brain
---

# ADR-009: Safety Gates for High-Risk Capabilities (Policy-Based Confirmation)

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Safety/Brain

## Context

This project is an execution agent that can perform actions with real, irreversible effect. In the Job-Apply scenario and later developments we have several categories of high-risk actions:

- **Final submit/apply:** May wrongly apply to the wrong position; may submit multiple times (spam).
- **File uploads:** Resume and personal information (PII) are sensitive; there is a risk of wrong file/format selection.
- **Login / credential entry:** Risk of leak and abuse; requires access control and minimal logging.
- **Actions with external side effects:** Sending message/email; payment/purchase (future phases); system changes on desktop/IDE.

Without guardrails: risk of harm to user/accounts; lower trust and publishability of the project; high risk for GitHub and job interviews.

## Decision

A safety policy (Safety Gate) is applied in the Brain in a **policy-driven** way:

- A set of capabilities is defined as **High-Risk** (in MVP at least: submit_application, upload_resume, login).
- Before executing a high-risk capability: policy can enable **require_human** or **confirmation_required**; without confirmation, execution is blocked or the task is paused.
- All these decisions and confirmations are recorded as events: trigger policy (in trace); human confirmation (in human.action or dedicated confirm event); capability execution result (hand.execution).

**Key rules:**

- Default: High-risk actions require human confirmation (configurable).
- Domain allowlist for high-risk actions is recommended (e.g. only specified job boards).
- Rate limiting and dedup (to prevent multiple submits) must be considered.

## Consequences

### Positive

- **Lower risk of unwanted behavior:** The system cannot blindly submit/upload/login.
- **Higher trust for public display:** For GitHub/interviews, it shows engineering maturity.
- **Explainability and audit:** It is clear which policy constrained the decision and when the human confirmed.
- **Good basis for compliance:** For more serious use, this model can be extended to organizational rules.

### Negative / Costs

- Less full automation: the user must intervene at some points.
- UX complexity: the "request confirmation" experience must be clear.
- More configuration: allowlist/denylist and risk levels must be managed.
- Edge cases: if a site has auto-submit or multi-step submit, gating must be designed correctly.

## Alternatives Considered

- **No gates:** ✅ More complete automation; ❌ very high and unacceptable risk for a real execution system.
- **Hard-coded if-statements inside Hand:** ✅ Simple; ❌ coupling and less flexibility; ❌ weak explainability and policy management.
- **Prompt-only safety (in LLM):** ✅ Fast; ❌ unreliable and prone to drift; ❌ weak audit and enforceability.

**Conclusion:** Policy-based safety gates are the best option for enforceable safety.

## Notes / Follow-ups

- The High-Risk capability list and risk levels are formalized in [docs/safety-and-guardrails.md](../safety-and-guardrails.md).
- Exact confirmation flow is defined in docs/hitl.md (or the HITL section).
- Suggested metrics: number_of_high_risk_blocks, number_of_high_risk_confirmations, dedup_prevented_submits.
- Domain allowlist/denylist must be connected to the policy layer.
