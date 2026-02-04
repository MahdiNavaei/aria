---
title: "ADR-004: Skills and Policies as Separate Artifacts"
status: Accepted
date: "2026-01-31"
owners: Brain/Learning
---

# ADR-004: Skills and Policies as Separate Artifacts

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Brain/Learning

## Context

The system must both **do the work** and **know when/how to do it**, but these are different kinds of decisions:

- **Macro execution vs decision rules:** Sometimes we want to run a flow in a reusable way (e.g. "apply on simple form"). Sometimes we want to decide "when may we submit?" or "what do we do if we see captcha?".
- **Explainability and maintainability:** If we mix macro and rules in one structure, in practice: debugging is hard; changing one part has unintended effects on another; learning produces vague, unreviewable artifacts.
- **Different learning signals:** Skills are mainly built from success traces and human demos. Policies are mainly built from failure patterns, blockers, risk gates, and supervision.
- **Different scope:** A skill is usually domain- or pattern-specific (Greenhouse/Lever/…). A policy can be global (captcha → human) or domain-specific (prefer skill X).

## Decision

Two separate artifacts are defined:

**1) Skill**

- An execution macro including: precondition (domain/page_signature/form_type…), steps[] (sequence of capability calls + ui_ref mappings), fallback (retry/vision/human at macro level), postcondition (success indicators).
- Goal of Skill: increase reuse, reduce time-to-completion, reduce need for the planner to handle repetitive detail.

**2) Policy**

- A decision rule including: conditions[] (based on context/history/observation/error), actions[] (block/require_human/require_vision/set_parameter/prefer_skill/abort…).
- Goal of Policy: guardrails, routing, safety gates, and systematic response to failure patterns.

**Key rules:**

- Brain evaluates policies before executing each capability.
- Skill selection/expansion happens after policy evaluation (so policy can limit or reroute execution).
- Both Skill and Policy are stored as versioned artifacts in the Artifact Store.

## Consequences

### Positive

- **Clear separation of concerns:** Skill = "how to do it"; Policy = "when/under what conditions to do it".
- **Higher explainability:** Decisions are auditable: which policy triggered? which skill was chosen?
- **Clear learning pipeline:** Skill induction and policy induction have separate, optimizable paths.
- **Reviewability:** Artifacts can be reviewed in PRs (especially on GitHub).

### Negative / Costs

- Two artifact types and lifecycles: versioning, promotion, and deprecation processes are needed for both.
- Need to prioritize policies: conflicts must be resolved with priority/ordering.
- Need match logic for skills: skill matching may choose wrong; precise preconditions and metrics are needed.

## Alternatives Considered

- **Single DSL (Skill including rules):** ✅ One file for everything; ❌ high complexity, hard to debug and learn; ❌ "macro vs guard" boundary is blurred.
- **Policy embedded in prompt/planner:** ✅ Fast for prototyping; ❌ not auditable or versionable; ❌ more drift and nondeterminism; ❌ reliable learning is harder.
- **Hard-coded guards inside Hand:** ✅ Simple execution; ❌ coupling and less flexibility; ❌ weaker Brain-level safety and explainability.

**Conclusion:** Separating Skill and Policy is the best option for maintainability, explainability, and learning.

## Notes / Follow-ups

- Skill schema is documented in docs/skills.md and Policy schema in docs/policies.md.
- Policy conflict resolution is defined by priority.
- Skill matching has minimal criteria: domain/page_signature match, form_type match (in MVP).
- Learning should record statistics for: skill success rate, policy trigger outcomes.
