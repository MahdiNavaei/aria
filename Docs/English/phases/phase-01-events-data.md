---
title: "Phase 1: Event Model & Data Infrastructure"
version: v1
date: "2026-02-02"
status: completed
---

# Phase 1: Event Model and Data Infrastructure

## Overview

This phase implements the foundational data infrastructure for ARIA, establishing event-driven architecture with Kafka/Redpanda for event streaming and Redis for state management. This infrastructure enables full auditability, replay capability, and decoupled service communication.

## Components Implemented

### Event Model

The event model provides a structured way to record all system activities:

- **EventEnvelope**: Base structure for all events with correlation IDs
- **Event Types**: Categorized events (brain, hand, eye, human, learning, session)
- **Serialization**: JSON-based serialization for Kafka compatibility
- **Versioning**: Event schema versioning for backward compatibility

### Event Bus (Kafka/Redpanda)

- **AsyncEventBus**: Asynchronous event publisher and subscriber
- **Topic Management**: Automatic topic creation and configuration
- **Consumer Groups**: Support for multiple consumers with offset management
- **Error Handling**: Retry logic and dead letter queue support

### State Store (Redis)

- **Session State**: Per-session state management with TTL
- **Working Memory**: Circular buffer for current task context
- **Cache Layer**: General-purpose caching with expiration
- **Distributed Locks**: Coordination primitives for concurrent operations

## Architecture Decisions

- **Event Sourcing**: All actions are recorded as events for full auditability
- **Refs-only Events**: Large payloads stored in Artifact Store, events carry references
- **Content-Addressed Refs**: SHA-256 hashes for snapshot deduplication
- **At-least-once Delivery**: Consumer idempotency required

## Key Features

- **Replay Capability**: Complete execution traces can be replayed
- **Observability**: Structured events enable comprehensive monitoring
- **Decoupling**: Services communicate via events, not direct calls
- **Learning Pipeline**: Events feed into learning system for skill/policy extraction

## Integration Points

- **Brain**: Emits planning and execution events
- **Hand**: Emits capability execution events
- **Eye**: Emits perception and observation events
- **Learning**: Consumes events for artifact generation

## Testing

- **Unit Tests**: Event model validation and serialization
- **Integration Tests**: Kafka/Redis connectivity and operations
- **E2E Tests**: Full event flow from emission to consumption

## Next Steps

After completing this phase, the system has:
- ✅ Event-driven communication infrastructure
- ✅ State management capabilities
- ✅ Foundation for replay and observability

**Next Phase**: [Phase 2: Memory System](phase-02-memory.md)
