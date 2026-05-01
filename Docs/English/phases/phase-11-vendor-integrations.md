---
title: "Phase 11: Vendor Integrations"
version: v0.2-preview
date: "2026-05-01"
status: public-preview
priority: high
public_scope: curated
---

# Phase 11: Vendor Integrations

## Purpose

Phase 11 defines how ARIA uses selected vendor projects without letting them
collapse the platform boundary.

The vendor projects are useful, but ARIA's architecture remains responsible for
contracts, safety, HITL, observability, and learning.

## Integration Targets

| Vendor | Role in ARIA | Boundary |
|---|---|---|
| AIHawk | LinkedIn-oriented job application automation | job apply plugin adapter |
| Skyvern | vision-assisted form workflows | browser/form filling adapter |
| OpenAdapt | learn-by-demonstration and desktop recording | learning and skill extraction bridge |
| browser-use | natural-language browser automation patterns | browser adapter fallback/extension |

## v0.2 Public Scope

This preview documents the integration boundaries and keeps vendored code under
license-governed directories. It does not publish private credentials,
production profiles, or private application traces.

## Design Rules

- Vendor integrations must be adapters, not hidden orchestration owners.
- Vendor events should be normalized into ARIA event envelopes.
- HITL and Safety remain authoritative.
- Vendor outputs should be converted into typed ARIA contracts before use.
- Vendor code must retain license and upstream notices.

## Completion Criteria

- Each vendor has an explicit role.
- Integration paths are documented.
- High-risk vendor actions still require ARIA safety checks.
- Vendor-specific behavior does not leak into Brain planning logic.

## Next

[Phase 12: Platform Consolidation](phase-12-platform-consolidation.md)

