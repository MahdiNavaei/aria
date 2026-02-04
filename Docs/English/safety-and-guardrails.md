---
title: "Safety & Guardrails"
version: v1
date: "2026-01-31"
---

# Safety & Guardrails

**Version:** v1 (2026-01-31)

## 1) Purpose

This project is an execution agent that can perform real actions on web/systems. The purpose of this document is to define guardrails that:

- Prevent unwanted/irreversible actions
- Make system behavior auditable and controllable
- Reduce security and privacy (PII) risks
- Improve project quality and trustworthiness for personal use and public display (GitHub)

## 2) Safety Posture (Default Stance)

The system defaults to a conservative stance:

- On ambiguity: **pause / request human confirmation**
- On high-risk actions: **require_human** or **confirmation_required**
- When facing blockers like captcha: **no attempt to bypass** and refer to human

## 3) High-Risk Capability Classification

### 3.1 High-Risk Actions (Require Human by default)

This category does not execute without human confirmation by default:

- submit_application / final_submit
- upload_file (resume, cover letter, documents)
- login / enter_credentials
- send_message / send_email (if added later)
- Any capability that creates "external effect" (irreversible side-effect)

**Why:** These can cause user harm, information leakage, or spam.

### 3.2 Medium-Risk Actions (Require confirmation depending on context)

- Typing in forms (name/email/number)
- Selecting legal consent checkboxes
- Clicking links that exit the site or suspicious redirects

**Rule:** If data is sensitive or destination is outside allowlist → escalate to human.

### 3.3 Low-Risk Actions (Auto)

browse, scroll, open page; search/filter; extract job cards; read-only actions.

## 4) Domain Control: Allowlist / Denylist

### 4.1 Allowlist Default

For MVP job-apply, it's better to work only on specific domains, e.g.: boards.greenhouse.io, jobs.lever.co, *.workday.com (if desired, but more complex).

**Rule:** If domain is outside allowlist: only read-only allowed; or requires human confirmation to continue.

### 4.2 Denylist (Hard Block)

Payment/banking pages; software installation or executable download pages; pages suspected of phishing (heuristics or user-defined).

**Rule:** block and generate agent.error(code=domain_blocked).

## 5) Captcha & Anti-bot Policy

### 5.1 Principle

The system's goal is not to bypass or circumvent captcha.

### 5.2 Handling

When hand.observation reports: **blocker_type=captcha** or **anti_bot_challenge**:

- **Action:** policy: require_human; system pauses; continues after human.action
- **learning:** generate persistent policy captcha_requires_human and (if needed) ui_ref updates

## 6) Idempotency & Anti-Spam Controls

### 6.1 Submit Dedup

To prevent multiple submits: submit_application must be idempotent at session/trace level. **Heuristics:** If a successful submit is recorded in the same trace_id: do not execute again; or require human confirmation.

### 6.2 Rate Limits

Limit number of applications per time period (configurable); limit retries for one step (e.g., max retries = 3).

## 7) Human Confirmation Gates

### 7.1 Two-step Confirmation (Recommended)

For high-risk: Brain says: "about to submit/upload" → Human confirms (human.action type confirm) → Hand executes.

### 7.2 What to show user

Before confirmation, UI should show: domain and exact address; summary of information to be sent (without displaying full PII); number of times action was taken previously.

## 8) Data Safety & Privacy

### 8.1 PII Minimization

Events should not contain: full resume text; passwords/tokens; full content of sensitive forms. **Events should only contain:** refs, minimal metadata, hashed identifiers (if needed).

### 8.2 Snapshot Policy

Snapshots may contain PII. **Defaults:** screenshot/dom only stored when: failure occurred or replay/golden trace needed; short-term retention; session cleanup capability.

### 8.3 Redaction Guidelines (High-Level)

Mask email/number/name in observation payloads (if stored); do not store file upload content anywhere in the system.

## 9) Tooling Safety (Sandboxing)

### 9.1 Adapter Isolation

Execution tools (browser/desktop/cursor) should preferably run in sandbox: container / VM / restricted user.

### 9.2 Third-party Tool Risk

If external tools/skill packages are used: only from trusted source; pin versions; check supply-chain.

## 10) Fail-safe Defaults

### 10.1 On ambiguity

If confidence is low or multiple choices possible: stop; request human assist; full log in agent.error or hand.execution.

### 10.2 On repeated failures

After max retries: abort or human handoff; generate agent.error(code=max_retries_exceeded).

## 11) Auditability & Logging

### 11.1 What must be auditable

Why a policy triggered; why high-risk execution was blocked; what human confirmed/corrected; final execution result.

### 11.2 Event coverage

hand.execution for each capability; human.action for each human intervention; agent.error for stop/block decisions; learning.artifact for each knowledge change.

## 12) Security & Threat Surfaces (Summary)

credential leakage; PII exposure in snapshots; malicious pages / phishing; uncontrolled side effects (submit spam); supply chain risk in third-party tools.

**Mitigations:** allowlist + high-risk gates + minimization + sandbox + audit events.

## 13) Configuration Surface (What's configurable)

allowlist/denylist domains; high-risk capability list; max retries; rate limits (apply/day); snapshot retention window; "vision fallback aggressiveness".

## 14) Acceptance Criteria (MVP)

For MVP to be deliverable:

- submit/upload/login should not execute without human confirmation (default)
- captcha always referred to human
- allowlist active
- logs without raw PII (refs-only)
- dedup submit within session active
