---
title: "Phase 00: Foundation"
version: v0.2-refresh
date: "2026-05-01"
status: refreshed
public_scope: curated
---

# Phase 00: Foundation

## Purpose

Phase 00 establishes the engineering baseline for ARIA: repository structure,
Python packaging, configuration, Docker services, logging, and the first
development workflow.

## v0.2 Refresh

The current private workspace evolved far beyond the original scaffold, but the
foundation remains the same: explicit layout, typed Python modules, config-first
runtime behavior, and reproducible local services.

The public refresh documents the foundation as a platform base rather than a
script collection.

## Public Deliverables

- Python package layout under `src/aria`.
- `pyproject.toml` packaging and development tooling.
- Docker Compose baseline for runtime services.
- Config files under `config/`.
- Documentation and ADR structure under `Docs/English`.

## Design Notes

- Keep runtime data out of version control.
- Keep configuration layered: YAML defaults, environment overrides, local `.env`.
- Treat Docker services as replaceable infrastructure, not business logic.
- Preserve a clean public tree without private run artifacts.

## Completion Criteria

- The repository can be cloned and inspected without generated artifacts.
- Python package discovery works from `src/`.
- Development dependencies and test tooling are declared.
- Runtime directories are either generated or explicitly documented.

## Next

[Phase 01: Events and Data Infrastructure](phase-01-events-data.md)

