# ARIA Documentation

This is the curated public documentation set for ARIA `v0.2`.

The public docs are intentionally smaller than the private workspace. They are
organized to explain the architecture, show the release timeline, and keep the
published repository reviewable.

## Start Here

| Document | Purpose |
|---|---|
| [Architecture Overview](architecture.md) | Main Brain/Eye/Hand/Memory architecture |
| [Project Structure](project-structure.md) | Repository layout and module responsibilities |
| [Event Model](event-model.md) | Event sourcing and runtime event concepts |
| [Safety and Guardrails](safety-and-guardrails.md) | Safety policy, HITL, PII, domain controls |
| [Testing Strategy](testing-strategy.md) | Public test strategy and verification approach |
| [Model Setup](MODELS.md) | LLM/VLM setup notes |
| [Public Phase Index](phases/README.md) | v0.2 phase timeline through Phase 12 |

## v0.2 Public Phase Docs

| Phase | Focus |
|---|---|
| [Phase 00](phases/phase-00-foundation.md) | Foundation and repository baseline |
| [Phase 01](phases/phase-01-events-data.md) | Event and data infrastructure |
| [Phase 02](phases/phase-02-memory.md) | Memory system |
| [Phase 03](phases/phase-03-brain.md) | Brain orchestration |
| [Phase 04](phases/phase-04-eye.md) | Eye perception |
| [Phase 05](phases/phase-05-hand.md) | Hand execution |
| [Phase 06](phases/phase-06-job-apply.md) | Job apply plugin |
| [Phase 07](phases/phase-07-learning.md) | Learning loop |
| [Phase 08](phases/phase-08-ui.md) | UI and dashboard |
| [Phase 09](phases/phase-09-testing.md) | Testing and integration |
| [Phase 10](phases/phase-10-safety.md) | Safety module |
| [Phase 11](phases/phase-11-vendor-integrations.md) | Vendor integrations |
| [Phase 12](phases/phase-12-platform-consolidation.md) | Platform consolidation and replay contracts |

## Architecture Decision Records

| ADR | Topic |
|---|---|
| [ADR-001](adr/ADR-001-event-sourcing.md) | Event sourcing |
| [ADR-002](adr/ADR-002-brain-hand-capability-contract.md) | Brain/Hand capability contract |
| [ADR-003](adr/ADR-003-uiref-multi-locator.md) | UIRef multi-locator strategy |
| [ADR-004](adr/ADR-004-skills-vs-policies.md) | Skills vs policies |
| [ADR-005](adr/ADR-005-artifact-store-refs-only.md) | Artifact refs in events |
| [ADR-006](adr/ADR-006-hitl-first-class.md) | HITL as first-class runtime concept |
| [ADR-007](adr/ADR-007-vision-fallback.md) | Vision fallback strategy |
| [ADR-008](adr/ADR-008-content-addressed-refs.md) | Content-addressed references |
| [ADR-009](adr/ADR-009-safety-gates.md) | Safety gates |
| [ADR-010](adr/ADR-010-metrics-and-success-criteria.md) | Metrics and success criteria |

## Public/Private Boundary

The public docs describe the architecture and curated implementation slices.
Private generated artifacts, real execution traces, production evidence packs,
large experiments, and environment-specific runtime outputs are intentionally
not published.
