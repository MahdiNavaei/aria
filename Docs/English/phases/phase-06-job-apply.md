---
title: "Phase 06: Job Apply Plugin"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 06: Job Apply Plugin

## Purpose

Phase 06 introduces ARIA's first domain plugin: job search, job extraction,
profile matching, application preparation, and controlled application flows.

## v0.2 Refresh

The plugin remains a demonstration of the platform, not the platform itself.
The public refresh makes that boundary clearer: job apply is one domain built on
Brain, Eye, Hand, Memory, Safety, and Learning.

## Public Deliverables

- Job extraction concepts.
- Profile and job matching responsibilities.
- Application workflow boundaries.
- HITL requirement for submission and credentials.
- AIHawk integration direction for LinkedIn-specific workflows.

## Safety Rules

- No credential entry without HITL.
- No application submission without human approval.
- External website terms and rate limits must be respected.
- PII must be redacted from logs and examples.

## Completion Criteria

- Job apply logic is isolated as a plugin.
- The plugin consumes core capabilities instead of owning infrastructure.
- Sensitive actions route through Safety and HITL.

## Next

[Phase 07: Learning Loop](phase-07-learning.md)

