---
title: "Phase 10: Safety Module"
version: v1
date: "2026-02-04"
status: completed
priority: critical
---

# Phase 10: Safety Module

## Overview

The Safety Module provides defense-in-depth security for ARIA, ensuring that the agent operates safely and responsibly. It implements multiple layers of protection including domain policies, risk assessment, captcha handling, rate limiting, and PII protection.

## Architecture

### Safety Gate

The Safety Gate is the central integration point that combines all safety checks:

- **Pre-execution Checks**: Validates actions before execution
- **Post-execution Validation**: Checks results after execution
- **Decision Making**: Determines if actions should proceed
- **HITL Integration**: Requests human intervention when needed

### Defense Layers

#### 1. Domain Policy Engine

- **Allowlist/Denylist**: Controls which URLs can be accessed
- **Read-only Domains**: Restricts interaction on certain domains
- **Wildcard Matching**: Supports pattern-based domain matching
- **Dynamic Updates**: Policies can be updated at runtime

#### 2. Risk Detector

- **Risk Classification**: Categorizes capabilities by risk level
- **Context Awareness**: Adjusts risk based on context
- **Factor Analysis**: Considers multiple risk factors
- **Action Recommendations**: Suggests appropriate safety measures

#### 3. Captcha Handler

- **Detection**: Identifies various captcha types
- **Human-Required Policy**: Always requests human intervention
- **Never Bypass**: Strict policy against captcha bypassing
- **HITL Integration**: Seamless human intervention flow

#### 4. Rate Limiter

- **Distributed Limiting**: Redis-backed rate limiting
- **Per-Action Limits**: Different limits for different actions
- **Sliding Window**: Smooth rate limiting algorithm
- **Abuse Prevention**: Prevents bot-like behavior

#### 5. PII Handler

- **Detection**: Identifies sensitive personal information
- **Redaction**: Masks PII in logs and outputs
- **Multi-Language**: Supports English and Persian PII patterns
- **Log Protection**: Prevents PII leakage in logs

## Safety Policies

### High-Risk Actions

Actions that require human confirmation:
- Application submission
- File uploads
- Login/credential entry
- System modifications
- Financial transactions

### Domain Restrictions

- **Allowlist Mode**: Only specified domains allowed
- **Denylist Mode**: Specific domains blocked
- **Read-only Mode**: View-only access to certain domains
- **Default Action**: Behavior for unlisted domains

### Rate Limits

- **Default**: 100 requests per minute
- **Submit**: 10 submissions per hour
- **Apply**: 50 applications per day
- **API**: 1000 API calls per hour

## Integration Points

### With Brain

- **Planner**: Checks URLs in plans
- **Executor**: Validates capabilities before execution
- **HITL Node**: Handles safety-related human requests

### With Hand

- **Pre-execution**: Safety checks before capability execution
- **Post-execution**: Validation of execution results
- **Error Handling**: Safety-related error responses

### With Event System

- **Event Emission**: Records all safety decisions
- **Audit Trail**: Complete safety audit log
- **Learning Input**: Safety events feed into learning

## Safety Metrics

- **Block Rate**: Percentage of requests blocked
- **False Positive Rate**: Incorrect blocks
- **HITL Trigger Rate**: Frequency of human intervention
- **PII Detection Rate**: Effectiveness of PII detection

## Configuration

### Safety Settings

- **Enabled/Disabled**: Toggle safety checks
- **Strict Mode**: Enhanced safety in production
- **Policy Files**: YAML-based policy configuration
- **Environment Variables**: Runtime configuration

### Domain Policies

- **Allowlist**: List of allowed domains per context
- **Denylist**: List of blocked domains
- **Read-only**: Domains with restricted access
- **Patterns**: Wildcard domain matching

## Ethical Considerations

### Captcha Policy

- **Never Bypass**: Strict policy against captcha bypassing
- **Human Required**: Always requests human intervention
- **Ethical Compliance**: Respects security measures

### PII Protection

- **Privacy First**: Protects user privacy
- **Log Redaction**: Prevents PII in logs
- **Data Minimization**: Only collects necessary data

## Testing

- **Unit Tests**: Individual safety component tests
- **Integration Tests**: Safety gate integration tests
- **E2E Tests**: Full safety flow tests
- **Penetration Tests**: Security validation tests

## Production Readiness

- **Comprehensive Coverage**: All safety aspects covered
- **Performance**: Minimal impact on execution speed
- **Reliability**: Resilient to failures
- **Auditability**: Complete safety audit trail

## Next Steps

After completing this phase, the system has:
- ✅ Complete safety infrastructure
- ✅ Multi-layer protection
- ✅ Human-in-the-loop safety
- ✅ Production-ready security

**Next Phase**: [Phase 11: Vendor Integrations](phase-11-vendor-integrations.md)
