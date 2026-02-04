"""LangGraph assembly for ARIA Brain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver

from aria.core.brain.nodes.executor import ExecutorNode
from aria.core.brain.nodes.hitl import HITLNode
from aria.core.brain.nodes.observer import ObserverNode
from aria.core.brain.nodes.planner import PlannerNode
from aria.core.brain.state import AgentState, TaskStatus, create_initial_state
from aria.utils.logging import get_logger

logger = get_logger(__name__)


def should_continue(state: AgentState) -> str:  # noqa: PLR0911
    """Determine next node based on current state."""
    status = state["task_status"]

    if status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
        return "end"

    if status == TaskStatus.WAITING_HUMAN:
        return "hitl"

    if state.get("hitl_request"):
        return "hitl"

    if state.get("plan") is None:
        return "planner"

    plan = state["plan"]
    if plan and plan.is_complete:
        return "end"

    if state.get("current_observation") is None:
        return "observer"

    return "executor"


def create_brain_graph(checkpointer: BaseCheckpointSaver | None = None) -> Any:  # noqa: ANN401
    """Create the ARIA Brain graph."""
    planner = PlannerNode()
    executor = ExecutorNode()
    observer = ObserverNode()
    hitl = HITLNode()

    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("executor", executor)
    graph.add_node("observer", observer)
    graph.add_node("hitl", hitl)

    graph.set_entry_point("planner")

    graph.add_conditional_edges(
        "planner",
        should_continue,
        {"observer": "observer", "end": END},
    )

    graph.add_conditional_edges(
        "observer",
        should_continue,
        {"executor": "executor", "hitl": "hitl", "end": END},
    )

    graph.add_conditional_edges(
        "executor",
        should_continue,
        {
            "observer": "observer",
            "hitl": "hitl",
            "planner": "planner",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "hitl",
        should_continue,
        {"observer": "observer", "executor": "executor", "end": END},
    )

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


class Brain:
    """ARIA Brain orchestration engine."""

    def __init__(self, checkpointer: BaseCheckpointSaver | None = None) -> None:
        """Initialize Brain with optional checkpointer."""
        self.graph = create_brain_graph(checkpointer)

    async def run(
        self,
        goal: str,
        domain: str,
        session_id: str,
        user_id: str = "default",
    ) -> AgentState:
        """Run brain graph with initial goal."""
        initial_state = create_initial_state(
            session_id=session_id,
            user_id=user_id,
            goal=goal,
            domain=domain,
        )

        logger.info("Brain starting", goal=goal, domain=domain, session_id=session_id)

        config = {"configurable": {"thread_id": session_id}}
        final_state = None

        async for state in self.graph.astream(
            initial_state,
            config,
            stream_mode="values",
        ):
            final_state = state
            plan = state.get("plan")
            current_step = plan.current_step_index if plan else 0
            logger.debug(
                "State update",
                status=state.get("task_status"),
                step=current_step,
            )

        logger.info(
            "Brain completed",
            session_id=session_id,
            status=final_state.get("task_status") if final_state else "unknown",
        )

        return final_state

    async def resume(self, session_id: str) -> AgentState:
        """Resume brain graph from checkpoint."""
        config = {"configurable": {"thread_id": session_id}}
        final_state = None
        async for state in self.graph.astream(None, config, stream_mode="values"):
            final_state = state
        return final_state


_brain: Brain | None = None


async def get_brain() -> Brain:
    """Get singleton Brain instance."""
    global _brain  # noqa: PLW0603
    if _brain is None:
        _brain = Brain()
    return _brain
