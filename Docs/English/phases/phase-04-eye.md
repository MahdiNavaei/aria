---
title: "Phase 04: Eye Perception"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 04: Eye Perception

## Purpose

Phase 04 gives ARIA a perception layer: screenshots, VLM/OCR analysis, UI state
recognition, and UIRef extraction.

## v0.2 Refresh

The current architecture treats Eye as an evidence producer, not an executor.
Eye observes interface state and produces structured perception outputs that
Brain and Hand can consume.

## Public Deliverables

- Screenshot capture concepts for browser and desktop surfaces.
- VLM/OCR analysis path.
- UIRef model for semantic UI anchors.
- Recognition of CAPTCHA, login, empty states, blocked states, and page changes.

## Design Notes

- Eye should be invoked when DOM selectors are insufficient or state is unclear.
- Perception output should be structured and auditable.
- UIRefs should support fallback locators, not a single brittle selector.

## Completion Criteria

- Perception can be represented without raw private screenshots.
- UI state recognition is separated from action execution.
- Eye output is safe to reference from later traces.

## Next

[Phase 05: Hand Execution](phase-05-hand.md)

