---
title: "ADR-003: UIRef as Semantic Anchor with Multi-Locator Resolution"
status: Accepted
date: "2026-01-31"
owners: Hand/Learning
---

# ADR-003: UIRef as Semantic Anchor with Multi-Locator Resolution

**Status:** Accepted  
**Date:** 2026-01-31  
**Owners:** Hand/Learning

## Context

In real automation (especially web and modern UIs), relying on a single fixed locator (CSS/XPath) is naturally brittle:

- **UI is volatile:** Classes, DOM structure, test-ids, and button text change. A/B tests and small UI changes cause repeated failures.
- **One locator is not enough:** CSS may work in one version and not another; XPath is usually brittle; text can break with localization; role/aria may be incomplete.
- **Need for learnable fallbacks:** When a selector fails, the system must be able to use Vision (bbox on screenshot) and human correction (click/type) and turn it into a reusable asset.
- **Skills must be reusable:** If skills are written on raw selectors, reuse is hard. Skills should be built on a more stable semantic anchor.

## Decision

We define an abstraction called **UIRef** that represents "a meaningful element" (not a selector).

**UIRef has these key properties:**

- ui_ref_id: stable internal identifier
- semantic_label: semantic label (e.g. apply_button, submit_application, resume_upload)
- locators[]: set of locators with: locator_type (css/xpath/role/aria/text/vision_bbox/...), value, confidence, source (dom/vision/human/inferred)
- (optional) vision_bbox and dom_metadata
- (optional) page_signature to limit scope

**Key rules:**

- Brain only sees ui_ref_id and at most semantic_label, not selectors.
- UIRef resolution happens in Hand: Hand tries locators by confidence; if it fails and is allowed, the vision/human path is activated.
- Human correction and vision proposals can add new locators to the same UIRef (UIRef update).
- UIRefs and their locators are stored as artifacts in the Artifact Store; events only carry refs.

## Consequences

### Positive

- **Higher robustness against UI change:** Multiple locators and fallbacks reduce brittle failures.
- **Learning-native:** Human click and vision bbox directly become UIRef updates.
- **Real skill reuse:** Skills are written on semantic anchors, not fragile selectors.
- **Better explainability:** "Why this locator was chosen" can be explained (confidence/source).

### Negative / Costs

- Hand complexity: need for a resolve algorithm and locator ranking policy (confidence decay, success/failure stats).
- Lifecycle and drift: locators can become stale; need for cleanup/garbage collection and revalidation.
- Scope management: if page_signature/domain are not managed correctly, UIRef may be reused incorrectly.
- Storage/indexing: UIRefs must be searchable and versioned.

## Alternatives Considered

- **CSS/XPath selector only:** ✅ Simple and fast; ❌ very brittle and not learnable from human correction.
- **Vision-only automation:** ✅ DOM-independent; ❌ higher cost, slower, more error-prone on dense/text UIs; ❌ suboptimal when we have DOM on the web.
- **Classic record/replay (RPA macro):** ✅ Good for fully fixed flows; ❌ fails on dynamic UIs and multiple job boards; ❌ limited learning and generalization.

**Conclusion:** UIRef multi-locator gives the best balance of robustness, learning, and reuse.

## Notes / Follow-ups

- Exact UIRef and UILocator schema are documented in docs/ui_ref.md.
- Hand must have a resolve policy: sort by confidence; backoff/decay by failure_count; optional vision fallback.
- The learning engine is responsible for updating UIRefs and producing learning.artifact(ui_ref_update).
- Domain and page_signature are included in the strategy to avoid incorrect reuse.
