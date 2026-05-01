---
title: "Phase 03: Brain Orchestration"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 03: Brain Orchestration

## Purpose

Phase 03 builds the Brain: the orchestration layer that turns a user goal into
structured plans, executable steps, observations, recovery decisions, and HITL
requests.

## v0.2 Refresh

The private system hardened Brain behavior around typed state, planner/executor
boundaries, trace ids, step ids, HITL resume behavior, and safer reasoning
contracts. The public refresh documents that direction without publishing the
full private orchestration stack.

## Public Deliverables

- LangGraph-style state-machine architecture.
- Planner, Executor, Observer, and HITL node responsibilities.
- Explicit separation between planning and tool execution.
- State and execution-history concepts used by later replay work.

## Runtime Boundaries

- Planner produces structured steps.
- Executor routes capability calls through Hand.
- Observer records evidence and state changes.
- HITL gates sensitive or ambiguous operations.

## Completion Criteria

- Brain does not directly own browser or desktop internals.
- Plans have step ids that can be referenced by events and traces.
- Failures can route to retry, re-plan, HITL, or stop.

## Next

[Phase 04: Eye Perception](phase-04-eye.md)
