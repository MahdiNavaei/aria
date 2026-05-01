---
title: "Phase 08: UI and Dashboard"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 08: UI and Dashboard

## Purpose

Phase 08 adds the operator surface: live task status, browser view, activity
logs, HITL requests, bilingual text, and runtime controls.

## v0.2 Refresh

The original public UI is Streamlit-based. The private system later moved toward
a richer frontend control plane. This refresh keeps the public repo honest: the
legacy UI is available here, while future public releases may publish selected
control-plane slices separately.

## Public Deliverables

- Streamlit dashboard.
- Live browser/status panels.
- HITL approval panel.
- Activity log and task progress.
- Persian/English and RTL-oriented UI direction.

## Design Notes

- Operator UI should expose decisions, not hide them.
- HITL should be first-class, not an afterthought.
- Runtime controls must not bypass safety policy.

## Completion Criteria

- Users can inspect execution state.
- HITL requests are visible and actionable.
- UI communicates task progress and failure states.

## Next

[Phase 09: Testing and Integration](phase-09-testing.md)

