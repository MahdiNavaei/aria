---
title: "ADR-006: Human-in-the-Loop as First-Class Tool (HITL)"
status: Accepted
date: "2026-01-31"
owners: Brain/Safety/Learning
---

# ADR-006: Human-in-the-Loop as First-Class Tool (HITL)

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Brain/Safety/Learning

## Context

In real automation (especially job-apply on the web), there are scenarios that are not **fully automatic** or **safe/reliable**:

**Real blockers:** captcha, login wall / email verification, complex consent/cookie modals, anti-bot challenges. These are either technically hard or should not be bypassed for ethical/legal reasons.

**High-risk actions:** Final submit, resume/personal file upload, credential entry, actions with external and irreversible effect.

**Need to learn from human correction:** If a human intervenes but the system only treats it as "done outside the system," we lose: data for learning; we do not fix selector drift; we do not produce skill/policy. So human intervention must be a **formal signal**.

**Explainability and audit:** In a project that may be public (GitHub), it must be clear: where the system decided to stop; where human confirmation was required; what was done by the human.

## Decision

Human-in-the-Loop is defined as a **formal, first-class tool** in the architecture, not a workaround.

- Brain can enable **require_human** in specific conditions (via Policy or Safety Gate).
- The human UI/interface receives the action (click/type/confirm).
- The outcome is recorded as a versioned event: **human.action**
- The learning engine uses human.action for: UIRef update, selector update, policy induction.

**Key rules:**

- Bypassing captcha or circumventing limits is not a system goal. The standard path is: **human solve** + record event.
- High-risk actions are not executed without human confirmation (by default).
- Human action always includes correlation IDs so it can be reconstructed in replay.

## Consequences

### Positive

- **Higher operational robustness:** The system does not "die" when facing blockers and has a clear path.
- **Better safety and compliance:** System behavior is controllable and auditable.
- **Real learning signal:** Human correction becomes an artifact and reduces failure in subsequent runs.
- **Explainability:** It is clear where automation stopped and why.

### Negative / Costs

- Less full automation: some tasks will always require human intervention.
- Need for good handoff UX: the human experience must be clear (what is needed? where to click?).
- State machine complexity: the brain must manage pause/resume and human gating states.
- Privacy: human action may include sensitive information in context; minimalism and masking must be applied.

## Alternatives Considered

- **Remove HITL and aim for full automation:** ❌ Fails in practice on captcha/login or enters high-risk/inappropriate territory; ❌ low safety and higher risk of unwanted behavior.
- **HITL outside the system (manual without recording):** ✅ Simpler; ❌ learning is lost; ❌ replay and audit are incomplete.
- **Hard-coded rules without human action event:** ✅ Deterministic execution; ❌ behavior does not generalize across diverse UIs; ❌ data feedback loop is lost.

**Conclusion:** HITL as a formal tool is the best trade-off between robustness, safety, and learning.

## Notes / Follow-ups

- human.action schema is defined in [docs/event-model.md](../event-model.md).
- The list of "high-risk capabilities" is formalized in [docs/safety-and-guardrails.md](../safety-and-guardrails.md).
- Default policy: captcha → require_human; submit/upload/login → confirmation/human (configurable).
- Related learning artifacts: learning.artifact(type=ui_ref_update), learning.artifact(type=policy) for recurring patterns.
