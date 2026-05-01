---
title: "Phase 09: Testing and Integration"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 09: Testing and Integration

## Purpose

Phase 09 creates the verification baseline: unit tests, integration tests,
E2E-style scenarios, CI workflows, documentation checks, and production setup.

## v0.2 Refresh

The current private workspace has much broader test and evidence practices. The
public refresh keeps the early test suite but clarifies the next direction:
contract tests, replay tests, and evidence-backed regression checks.

## Public Deliverables

- Unit test suite for core modules.
- Integration tests for API, event, memory, browser, and safety paths.
- E2E markers for full workflow tests.
- GitHub Actions workflow definitions.
- Public v0.2 replay contract tests.

## Known Baseline Note

Some legacy public tests may require modules or fixtures that were not fully
published in the original `v0.1.x` snapshot. The `v0.2` replay contract slice is
therefore verified independently while the public repo is incrementally cleaned.

## Completion Criteria

- New public code has targeted passing tests.
- Test requirements are documented.
- CI can be tightened as the curated release line expands.

## Next

[Phase 10: Safety Module](phase-10-safety.md)

