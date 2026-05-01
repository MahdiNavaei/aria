---
title: "Phase 07: Learning Loop"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 07: Learning Loop

## Purpose

Phase 07 teaches ARIA to learn from successful traces, failed attempts, human
feedback, and repeated action patterns.

## v0.2 Refresh

The private workspace later expanded learning into teacher/judge workflows,
policy candidates, skill extraction, effect tracking, and guarded rollout. This
public refresh documents the early learning loop without exposing private data.

## Public Deliverables

- Event consumption for execution and human feedback.
- Skill extraction concept from repeated successful traces.
- Policy learning concept from approvals, denials, and corrections.
- UIRef refinement from execution outcomes.

## Learning Boundaries

- Learning candidates are not automatically trusted.
- Promotion requires evidence, confidence, and rollback thinking.
- Private traces should be summarized or redacted before public examples.

## Completion Criteria

- Learning inputs are tied to trace/session ids.
- Learned skills and policies have explicit metadata.
- Feedback cannot silently mutate runtime policy without governance.

## Next

[Phase 08: UI and Dashboard](phase-08-ui.md)
