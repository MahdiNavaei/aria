---
title: "Phase 3: Brain with LangGraph Orchestration"
version: v1
date: "2026-02-02"
status: completed
---

# Phase 3: Brain (LangGraph Orchestration)

## Overview

The Brain is ARIA's core orchestration engine, responsible for planning, decision-making, and coordinating all other components. Built on LangGraph, it implements a state machine that manages the complete task execution lifecycle.

## Architecture

### State Graph

The Brain uses a LangGraph StateGraph with the following nodes:

- **Planner**: Decomposes user goals into executable steps
- **Executor**: Sends steps to Hand for execution
- **Observer**: Retrieves observations from Eye
- **HITL**: Manages human-in-the-loop interventions

### State Management

**AgentState** includes:
- Session and task information
- Execution plan with steps
- Current observations
- Memory context
- HITL requests and responses
- Error handling and retry state

### Flow Control

The graph uses conditional edges to route execution:
1. **Planning** → Create execution plan
2. **Observation** → Get current UI state
3. **Execution** → Execute capability via Hand
4. **HITL** → Request human intervention when needed
5. **Completion** → Task finished or failed

## Key Components

### LLM Client Abstraction

- **Provider Support**: Ollama (local) and OpenAI/Anthropic (cloud)
- **Role-based Models**: Different models for reasoning, coding, vision
- **Streaming Support**: Async streaming for real-time responses
- **Error Handling**: Retry logic and fallback mechanisms

### Planner Node

- **Goal Decomposition**: Breaks complex goals into atomic steps
- **Context Integration**: Uses episodic and semantic memory
- **Skill Matching**: Leverages learned skills when applicable
- **Policy Awareness**: Considers safety policies in planning

### Executor Node

- **Capability Routing**: Routes steps to appropriate Hand adapters
- **Result Processing**: Handles success, failure, and retry scenarios
- **Error Recovery**: Implements retry logic with exponential backoff
- **Event Emission**: Records all execution events

### Observer Node

- **Eye Integration**: Retrieves UI observations
- **State Detection**: Identifies special states (captcha, login, etc.)
- **HITL Triggering**: Requests human intervention when needed
- **Observation History**: Maintains context of UI changes

### HITL Node

- **Request Management**: Creates and tracks human intervention requests
- **Response Handling**: Processes human approvals, rejections, corrections
- **Timeout Management**: Handles cases where human doesn't respond
- **Learning Integration**: Feeds human feedback to learning system

## Integration

### With Event Bus

All Brain activities emit events:
- `brain.plan.created`: When a plan is generated
- `brain.step.started`: When a step begins execution
- `brain.step.completed`: When a step finishes

### With Memory

- **Context Building**: Retrieves relevant memories for planning
- **State Persistence**: Stores execution state for resumption
- **Learning Input**: Provides data for skill/policy extraction

### With Hand

- **Capability Execution**: Sends capability calls to Hand
- **Result Processing**: Handles execution results
- **Error Handling**: Manages failures and retries

### With Eye

- **Observation Requests**: Requests UI state from Eye
- **State Analysis**: Processes observations for decision-making
- **Fallback Triggers**: Activates vision fallback when needed

## Safety Integration

- **Pre-execution Checks**: Validates capabilities before execution
- **Risk Assessment**: Evaluates action risk levels
- **Policy Enforcement**: Applies safety policies
- **HITL Integration**: Requests human confirmation for high-risk actions

## Checkpointing

- **State Persistence**: Saves state at each node transition
- **Resume Capability**: Can resume from any checkpoint
- **Replay Support**: Enables deterministic replay of executions

## Performance Considerations

- **Async Operations**: All I/O operations are asynchronous
- **Parallel Execution**: Multiple steps can execute in parallel when safe
- **Resource Management**: Efficient LLM and adapter usage
- **Caching**: Caches frequently accessed data

## Testing

- **Unit Tests**: Individual node testing
- **Integration Tests**: Full graph execution tests
- **E2E Tests**: Complete workflow tests with real components

## Next Steps

After completing this phase, the system has:
- ✅ Complete orchestration engine
- ✅ Goal decomposition and planning
- ✅ Execution coordination
- ✅ Human-in-the-loop support

**Next Phase**: [Phase 4: Eye (Perception)](phase-04-eye.md)
