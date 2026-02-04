---
title: "ADR-005: Artifact Store outside Event Bus (Refs-only Events)"
status: Accepted
date: "2026-01-31"
owners: Platform/Learning
---

# ADR-005: Artifact Store outside Event Bus (Refs-only Events)

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Platform/Learning

## Context

The system is event-sourced and Kafka/Redpanda is used for the trace. But we have two kinds of data:

**Events (trace):** Small, numerous, real-time; for join, replay, and observability; must be transferred quickly and have controllable retention.

**Artifacts and snapshots:** Larger and heavier: screenshots, DOM snapshots, detailed observation payloads, skill/policy/ui_ref/selector files. They need: versioning, review and diff (especially in GitHub), retention/garbage collection, random access, and caching.

If we keep this heavy data in Kafka: broker load and cost increase; retention becomes complex; replay and access to large files are inefficient; migration/versioning is painful.

## Decision

Kafka/Redpanda carries only lightweight events; heavy data is stored outside it.

The **Artifact Store** holds: skills, policies, ui_refs, selectors, observations/snapshots (refs to files), screenshots/DOM snapshots.

**Events contain only references:** artifact_ref, screenshot_ref, dom_snapshot_ref, observation_ref.

**Storage options:** MVP: filesystem + Git (PR- and review-friendly); Mid: object storage such as MinIO/S3; Full: object storage + metadata DB/index.

## Consequences

### Positive

- **Event bus stays light and healthy:** Messages are small, fast, and manageable.
- **Easy versioning and review:** skill/policy/ui_ref can live as YAML in the repo and be diffable/PR-able.
- **Reliable replay:** Snapshots with content-addressed refs (hash) are readable and dedupable.
- **Better retention:** Separate retention policies can be defined for events and snapshots.

### Negative / Costs

- **Two sources of truth:** Consistency between event refs and the artifact store must be guaranteed.
- **GC and lifecycle:** Garbage collection is needed for old snapshots and orphan artifacts.
- **Access control and privacy:** Snapshots may contain PII and need retention/masking and deletion workflows.
- **Tooling:** Need artifact index and viewer/loader for replay.

## Alternatives Considered

- **Store snapshots in Kafka:** ❌ Heavy load on broker and storage; ❌ high latency and cost; ❌ unsuitable for large files (png/html).
- **Store everything in one DB (Postgres blob):** ✅ Single place; ❌ blob storage in DB leads to cost and performance issues over time; ❌ versioning/diff worse than git/file/object-store.
- **Plain log files without event bus:** ✅ Simple; ❌ real-time consumers and scaling are hard; ❌ correlation and replay are more complex with multiple workers.

**Conclusion:** A separate Artifact Store with refs in events is the best trade-off.

## Notes / Follow-ups

- Naming convention and folder structure are specified in [docs/artifact-store.md](../artifact-store.md).
- Snapshot refs should preferably be content-addressed (sha256).
- A policy must be defined for: snapshot retention, PII deletion, artifact promotion (learned → validated → stable).
- learning.artifact events should always carry artifact_ref, not the full artifact payload.
