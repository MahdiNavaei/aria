"""ARIA Learning System."""

from __future__ import annotations

from aria.core.learning.engine import LearningEngine, get_learning_engine
from aria.core.learning.policy_learner import Policy, PolicyLearner
from aria.core.learning.skill_extractor import Skill, SkillExtractor
from aria.core.learning.uiref_refiner import UIRefRefiner
from aria.models.events import EventType
from aria.utils.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "LearningEngine",
    "Policy",
    "PolicyLearner",
    "Skill",
    "SkillExtractor",
    "UIRefRefiner",
    "get_learning_engine",
    "setup_learning",
]


async def setup_learning() -> LearningEngine:
    """Set up and start the learning system."""
    engine = get_learning_engine()

    skill_extractor = SkillExtractor()
    policy_learner = PolicyLearner()
    uiref_refiner = UIRefRefiner()

    for event_type in (
        EventType.HAND_EXECUTION_STARTED,
        EventType.HAND_EXECUTION_COMPLETED,
        EventType.HAND_EXECUTION_FAILED,
        EventType.BRAIN_PLAN_CREATED,
        EventType.BRAIN_STEP_COMPLETED,
        EventType.SESSION_ENDED,
    ):
        engine.register_handler(event_type, skill_extractor.on_execution_event)

    for event_type in (
        EventType.HUMAN_FEEDBACK_RECEIVED,
        EventType.HUMAN_CORRECTION_RECEIVED,
    ):
        engine.register_handler(event_type, policy_learner.on_human_feedback)

    for event_type in (
        EventType.HAND_EXECUTION_COMPLETED,
        EventType.HAND_EXECUTION_FAILED,
    ):
        engine.register_handler(event_type, uiref_refiner.on_execution_result)

    await engine.start()

    logger.info("Learning system initialized")
    return engine
