---
title: "Phase 10: Safety Module"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
priority: critical
public_scope: curated
---

# Phase 10: Safety Module

## Purpose

Phase 10 adds defense-in-depth safety for agent execution: domain policy, risk
detection, CAPTCHA handling, rate limiting, PII protection, and integrated
Safety Gate decisions.

## v0.2 Refresh

The current private workspace hardened safety further with policy-wall behavior,
trust checks, runtime domain validation, and stricter HITL routing. This public
refresh keeps the original module readable while presenting Safety as a core
runtime plane.

## Public Deliverables

- Domain allowlist and denylist concepts.
- Risk detector for sensitive capabilities.
- CAPTCHA policy that requires humans rather than bypassing controls.
- PII redaction rules for logs and examples.
- Rate limiting and abuse-prevention direction.
- Safety Gate integration with Brain and Hand.

## Non-Negotiable Rules

- No credential entry without explicit user involvement.
- No CAPTCHA bypass.
- No hidden submission, payment, upload, or system modification.
- No secrets or private user data in public traces.

## Completion Criteria

- High-risk capabilities can be blocked or escalated.
- Safety decisions are auditable.
- Safety failures fail closed.

## Next

[Phase 11: Vendor Integrations](phase-11-vendor-integrations.md)
