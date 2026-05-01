---
title: "Phase 01: Events and Data Infrastructure"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 01: Events and Data Infrastructure

## Purpose

Phase 01 defines the data backbone for ARIA: event envelopes, event topics,
state storage, and durable communication between runtime components.

## v0.2 Refresh

The current system treats events as an audit and coordination plane. The public
refresh keeps the original Kafka/Redpanda and Redis intent while aligning the
documentation with later trace, replay, and governance work.

## Public Deliverables

- Kafka-compatible event bus through Redpanda.
- Redis-backed state storage.
- Event envelope concepts for correlation and audit.
- Topic naming conventions for Brain, Hand, Eye, Human, and Learning events.

## Runtime Boundaries

- Events carry facts and references, not private binary artifacts.
- State store is responsible for fast runtime state, not permanent evidence.
- Event schemas should be versioned before compatibility-sensitive changes.

## Completion Criteria

- Event producers and consumers use explicit topic names.
- Events include enough ids to reconstruct execution flow.
- State persistence is separated from event publication.

## Next

[Phase 02: Memory System](phase-02-memory.md)
