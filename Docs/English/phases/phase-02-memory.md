---
title: "Phase 02: Memory System"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 02: Memory System

## Purpose

Phase 02 introduces ARIA's memory model: working memory for active execution,
episodic memory for previous runs, and semantic memory for reusable knowledge.

## v0.2 Refresh

Later private phases expanded memory into learning, policy feedback, and trace
comparison. This public refresh keeps the scope readable while making the
long-term memory direction explicit.

## Public Deliverables

- Working memory interface for active task context.
- Episodic memory concepts for execution history.
- Semantic memory backed by vector search.
- Mem0/Qdrant-oriented configuration.

## Design Notes

- Working memory should be bounded and task-scoped.
- Episodic records should be traceable to execution ids.
- Semantic memory should store reusable knowledge, not raw private logs.
- Learning promotion must be gated by evidence and confidence.

## Completion Criteria

- Memory tiers are documented separately.
- Runtime state does not silently become long-term memory.
- Private user data is not committed to the repository.

## Next

[Phase 03: Brain Orchestration](phase-03-brain.md)

