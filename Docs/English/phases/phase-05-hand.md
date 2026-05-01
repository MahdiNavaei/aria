---
title: "Phase 05: Hand Execution"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 05: Hand Execution

## Purpose

Phase 05 implements the execution boundary: browser actions, desktop actions,
form filling, ML adapter calls, and capability routing.

## v0.2 Refresh

The private system hardened Hand around capability contracts, safety checks,
idempotency, runtime-domain validation, and evidence generation. The public
refresh presents Hand as a guarded boundary rather than a direct automation
helper.

## Public Deliverables

- Browser adapter based on Playwright-style execution.
- Desktop adapter concepts for local automation.
- Capability abstraction between Brain and tools.
- Vendor extension points for browser-use, Skyvern, and OpenAdapt.

## Runtime Boundaries

- Hand executes approved capabilities.
- Safety policy is checked before sensitive execution.
- Results are normalized into structured capability outcomes.
- Browser/desktop implementation details stay behind adapters.

## Completion Criteria

- Capability names and parameters are explicit.
- Execution results can be logged and traced.
- Hand does not bypass HITL or safety gates.

## Next

[Phase 06: Job Apply Plugin](phase-06-job-apply.md)

