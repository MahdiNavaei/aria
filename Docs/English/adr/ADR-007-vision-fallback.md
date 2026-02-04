---
title: "ADR-007: Vision Fallback (Eye) Only on Failure / Ambiguity Path"
status: Accepted
date: "2026-01-31"
owners: Eye/Hand/Brain
---

# ADR-007: Vision Fallback (Eye) Only on Failure / Ambiguity Path

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Eye/Hand/Brain

## Context

This system has both DOM-based automation (web) and, in the future, desktop/GUI. On the web, DOM and the accessibility tree are usually available and, compared to vision: **faster**, **more deterministic**, **lower cost**, **more precisely loggable** (selector/role/text).

But vision (VLM) also has an important advantage: when DOM/selector fails or the UI has changed; when a modal/overlay is shown; when the environment has no DOM (desktop, remote desktop, canvas-heavy UIs).

If we put vision always on the main path: cost and latency increase; error-proneness rises on dense/fine-grained UIs; the system becomes less deterministic; debugging is harder. So we need a clear strategy for "when the eye is invoked."

## Decision

Eye (Perception/Vision) is defined as a **fallback** and is only activated in these cases:

**Recoverable failure:** element_not_found, stale_element, click_intercepted, unknown_layout_change — with the error marked as recoverable (from Hand).

**Ambiguity:** Multiple similar elements (low confidence DOM resolution); mismatch between expected state and observation; blockers that need visual recognition (overlay/modal).

**Non-DOM environments (future):** Desktop automation, canvas-heavy pages, remote UI. In that case policy/config can make vision more active on the main path.

**Key rules:**

- Normal path for web: **DOM-first**.
- Vision outputs a "proposal" (bbox + semantic_label + confidence).
- Resolve and retry still happen in Hand (Brain only decides fallback).

## Consequences

### Positive

- **Better performance on the happy path:** DOM-first is faster.
- **Lower cost:** Vision is only used when needed.
- **Higher determinism:** Usual system behavior is less stochastic.
- **Better debuggability:** The main path stays simple and traceable; vision is clearly visible in the failure trace.

### Negative / Costs

- Recovery logic complexity: we must define which errors are recoverable and when to call vision.
- Some sites may need vision earlier (e.g. UIs with vague or heavily dynamic DOM).
- Need metrics to measure vision trigger rate and whether policy is needed.

## Alternatives Considered

- **Vision-first (Eye always on main path):** ✅ DOM-independent; ❌ high cost and latency; ❌ more errors on complex/fine-grained UIs; ❌ less deterministic.
- **Always-on hybrid (DOM + Vision together):** ✅ More robustness; ❌ very high cost and complexity; ❌ need for constant fusion logic.
- **No vision at all:** ✅ Simple; ❌ many failures on UI change and blockers; ❌ not extensible to desktop.

**Conclusion:** Vision fallback is the best trade-off for web and MVP and leaves the path open for desktop.

## Notes / Follow-ups

- Error taxonomy and recoverable flag are documented in docs/failure-handling.md.
- eye.perception schema is defined in [docs/event-model.md](../event-model.md).
- Domain-specific policies can enable "vision more aggressive" (future config).
- Suggested metrics: vision_trigger_rate, success_after_vision, avg_latency_added_by_vision, human_intervention_rate.
