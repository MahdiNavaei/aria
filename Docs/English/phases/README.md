# ARIA Public Phase Index

This directory documents the curated public `v0.2` release path for ARIA.

The first public line, `v0.1.x`, exposed the initial foundation phases. The
`v0.2` line refreshes those foundations and documents the architecture through
Phase 12 while keeping private traces, generated artifacts, environment-specific
outputs, and experimental internals out of the public repository.

| Phase | Status | Focus |
|---|---:|---|
| [Phase 00](phase-00-foundation.md) | refreshed | Foundation, repository layout, config, Docker, logging |
| [Phase 01](phase-01-events-data.md) | refreshed | Event model, Kafka/Redpanda, Redis state store |
| [Phase 02](phase-02-memory.md) | refreshed | Working, episodic, semantic memory |
| [Phase 03](phase-03-brain.md) | refreshed | LangGraph Brain orchestration |
| [Phase 04](phase-04-eye.md) | refreshed | Perception, screenshots, VLM/OCR, UIRef |
| [Phase 05](phase-05-hand.md) | refreshed | Browser/desktop execution adapters |
| [Phase 06](phase-06-job-apply.md) | refreshed | Job apply domain plugin |
| [Phase 07](phase-07-learning.md) | refreshed | Learning loop, skill extraction, policy feedback |
| [Phase 08](phase-08-ui.md) | refreshed | Operator UI and HITL surfaces |
| [Phase 09](phase-09-testing.md) | refreshed | Test strategy, CI, integration readiness |
| [Phase 10](phase-10-safety.md) | refreshed | Safety module and guardrails |
| [Phase 11](phase-11-vendor-integrations.md) | public preview | Vendor integration boundaries |
| [Phase 12](phase-12-platform-consolidation.md) | public preview | Core completion, event abstraction, replay contracts |

## Release Strategy

The public repository is intentionally staged. Each release should be small
enough to review and strong enough to show a real engineering milestone.

- `v0.2`: foundation refresh plus Phase 11-12 public preview.
- `v0.3`: observability and telemetry.
- `v0.4`: artifacts, evidence packs, and replay hardening.
- `v0.5`: trust envelope and governance gates.

