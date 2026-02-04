"""ARIA extensions for browser-use."""

from .event_emitter import BrowserEventEmitter
from .hitl_hooks import HITLHooks

__all__ = ["BrowserEventEmitter", "HITLHooks"]
