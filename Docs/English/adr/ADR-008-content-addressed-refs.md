---
title: "ADR-008: Content-Addressed Snapshot References (SHA-256 Refs)"
status: Accepted
date: "2026-01-31"
owners: Platform/Replay
---

# ADR-008: Content-Addressed Snapshot References (SHA-256 Refs)

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Platform/Replay

## Context

For replay, debugging, and learning we store snapshots such as: **screenshot**, **DOM snapshot**, **observation payload**. This data: has significant volume; may be duplicate (similar pages/refresh); must have integrity (tamper-resistant to a degree); must be referrable from the event trace.

If snapshots are named only by timestamp or UUID: dedup is hard; caching is hard; we have no guarantee that "this ref really is that content"; replay may run with wrong or swapped data.

## Decision

Snapshots are stored using a **content-addressed** approach:

- The ref identifier is generated from **sha256(content)**.
- Events only carry the ref: shot_sha256_<first16>, dom_sha256_<first16>, obs_sha256_<first16>.

**Key rules:**

- If two snapshots have the same content, the ref is the same → natural dedup.
- The loader can verify integrity by re-hashing.
- The hash → path mapping is managed in the artifact store.

## Consequences

### Positive

- **Dedup and lower storage:** Duplicate pages/DOMs are not stored again.
- **Integrity and replay trust:** The ref represents the content; replay is more deterministic.
- **Simple caching:** Ref is stable, cache hit rate is high.
- **Easier debugging:** With a stable ref, the snapshot can be found quickly.

### Negative / Costs

- Hash computation cost: hashes must be computed for files (screenshot/DOM).
- GC and lifecycle: garbage collection is needed (hashes that are no longer referenced).
- PII/Privacy: content may still be sensitive; hashing does not replace retention policy.
- Collision concern (practically negligible): SHA-256 collision is very unlikely, but the design should assume "practically safe" not absolute.

## Alternatives Considered

- **Timestamp-based naming:** ✅ Simple; ❌ dedup hard; ❌ weak integrity; ❌ weaker cache and replay.
- **UUID-only references:** ✅ Simple and unique; ❌ no relation to content; ❌ dedup and integrity are lost.
- **Store snapshots in DB:** ✅ Single place; ❌ cost and performance issues for large blobs; ❌ dedup and caching harder.

**Conclusion:** Content-addressed refs are the best trade-off for replay and storage.

## Notes / Follow-ups

- Ref format and storage path are specified in [docs/artifact-store.md](../artifact-store.md).
- A light index is needed: hash → file path, content type (png/html/json).
- Garbage collection: based on referenced refs in the event log or metadata DB; define a retention window for snapshots.
- For security/privacy, docs/security-and-privacy.md must specify which snapshots are stored and how they are deleted.
