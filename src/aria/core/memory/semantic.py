"""Semantic memory implementation using Mem0 and artifact storage."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mem0 import Memory

from aria.config import get_settings
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from watchdog.events import FileSystemEvent

logger = get_logger(__name__)


class _ArtifactWatcher:
    """File watcher that invalidates cache on changes."""

    def __init__(self, root: Path, on_change: Callable[[], None]) -> None:
        """Initialize artifact watcher."""
        self._root = root
        self._on_change = on_change
        self._observer = None

    def start(self) -> None:
        """Start watching for file changes."""
        try:
            from watchdog.events import FileSystemEventHandler  # noqa: PLC0415
            from watchdog.observers import Observer  # noqa: PLC0415
        except (ImportError, ModuleNotFoundError):
            logger.debug("watchdog not available; artifact hot-reload disabled")
            return

        class Handler(FileSystemEventHandler):
            def __init__(self, callback: Callable[[], None]) -> None:
                """Initialize handler with callback."""
                super().__init__()
                self._callback = callback

            def on_any_event(self, event: FileSystemEvent) -> None:
                """Handle file system events."""
                if event.is_directory:
                    return
                self._callback()

        handler = Handler(self._on_change)
        observer = Observer()
        observer.schedule(handler, str(self._root), recursive=True)
        observer.daemon = True
        observer.start()
        self._observer = observer
        logger.info("Artifact watcher started", path=str(self._root))

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None


class SemanticMemory:
    """Long-term semantic memory for skills, policies, and knowledge."""

    def __init__(
        self,
        artifacts_dir: Path | None = None,
        mem0_client: Memory | None = None,
    ) -> None:
        """Initialize semantic memory with artifact storage."""
        self._mem0: Memory | None = mem0_client
        if artifacts_dir is None:
            artifacts_dir = self._default_artifacts_dir()
        self._artifacts_dir = artifacts_dir
        self._lock = threading.Lock()
        self._cache: dict[str, dict[str, Any]] = {"skills": {}, "policies": {}, "uirefs": {}}
        self._dirty = False

        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        (self._artifacts_dir / "skills").mkdir(exist_ok=True)
        (self._artifacts_dir / "policies").mkdir(exist_ok=True)
        (self._artifacts_dir / "uirefs").mkdir(exist_ok=True)

        if os.getenv("ARIA_ENV", "development") == "development":
            self._watcher = _ArtifactWatcher(self._artifacts_dir, self._invalidate_cache)
            self._watcher.start()
        else:
            self._watcher = None

    def _invalidate_cache(self) -> None:
        with self._lock:
            self._dirty = True

    def _update_cache(self, category: str, item_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._cache.setdefault(category, {})[item_id] = data

    def _refresh_cache_if_needed(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            self._cache = {"skills": {}, "policies": {}, "uirefs": {}}
            self._dirty = False

    def _artifact_path(self, category: str, item_id: str) -> Path:
        return self._artifacts_dir / category / f"{item_id}.json"

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    def _default_artifacts_dir(self) -> Path:
        try:
            eye_settings = get_settings().eye
            uiref_dir = Path(eye_settings.uiref.storage_dir)
        except (AttributeError, KeyError):
            return self._project_root() / "artifacts"
        else:
            return uiref_dir.parent

    def _build_mem0_config(self) -> dict[str, Any]:
        settings = get_settings().memory.mem0
        return {
            "vector_store": {
                "provider": settings.vector_store.provider,
                "config": {
                    **settings.vector_store.config.model_dump(),
                    "collection_name": "aria_semantic",
                },
            },
            "embedder": settings.embedder.model_dump(exclude_none=True),
            "llm": settings.llm.model_dump(exclude_none=True),
        }

    def _get_mem0(self) -> Memory:
        if self._mem0 is None:
            config = self._build_mem0_config()
            self._mem0 = Memory.from_config(config)
            logger.info("Semantic Mem0 client initialized")
        return self._mem0

    async def add_skill(self, skill_id: str, skill_def: dict[str, Any], description: str) -> None:
        """Store a reusable skill."""
        path = self._artifact_path("skills", skill_id)
        path.write_text(json.dumps(skill_def, indent=2), encoding="utf-8")
        self._update_cache("skills", skill_id, skill_def)

        mem0 = self._get_mem0()
        mem0.add(
            [{"role": "user", "content": f"Skill: {skill_id}\n{description}"}],
            user_id="system",
            metadata={"type": "skill", "skill_id": skill_id, "domain": skill_id.split(".")[0]},
        )

        logger.info("Skill stored", skill_id=skill_id)

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Get a skill definition by ID."""
        self._refresh_cache_if_needed()
        cache = self._cache["skills"]
        if skill_id in cache:
            return cache[skill_id]

        path = self._artifact_path("skills", skill_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        cache[skill_id] = data
        return data

    async def find_skills(
        self,
        query: str,
        domain: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Find relevant skills by semantic search."""
        mem0 = self._get_mem0()
        results = mem0.search(f"skill for: {query}", user_id="system", limit=limit)

        skills: list[dict[str, Any]] = []
        for item in results:
            if item.get("metadata", {}).get("type") != "skill":
                continue
            skill_id = item["metadata"]["skill_id"]
            if domain and not skill_id.startswith(domain):
                continue
            skill_def = await self.get_skill(skill_id)
            if skill_def:
                skills.append(
                    {
                        "skill_id": skill_id,
                        "definition": skill_def,
                        "score": item.get("score", 0),
                    },
                )
        return skills

    async def add_policy(
        self,
        policy_id: str,
        policy_def: dict[str, Any],
        description: str,
    ) -> None:
        """Store a policy definition."""
        path = self._artifact_path("policies", policy_id)
        path.write_text(json.dumps(policy_def, indent=2), encoding="utf-8")
        self._update_cache("policies", policy_id, policy_def)

        mem0 = self._get_mem0()
        mem0.add(
            [{"role": "user", "content": f"Policy: {policy_id}\n{description}"}],
            user_id="system",
            metadata={"type": "policy", "policy_id": policy_id},
        )

        logger.info("Policy stored", policy_id=policy_id)

    async def get_policy(self, policy_id: str) -> dict[str, Any] | None:
        """Get a policy definition by ID."""
        self._refresh_cache_if_needed()
        cache = self._cache["policies"]
        if policy_id in cache:
            return cache[policy_id]

        path = self._artifact_path("policies", policy_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        cache[policy_id] = data
        return data

    async def find_policies(self, context: str, limit: int = 3) -> list[dict[str, Any]]:
        """Find policies relevant to a context."""
        mem0 = self._get_mem0()
        results = mem0.search(f"policy for: {context}", user_id="system", limit=limit)

        policies: list[dict[str, Any]] = []
        for item in results:
            if item.get("metadata", {}).get("type") != "policy":
                continue
            policy_id = item["metadata"]["policy_id"]
            policy_def = await self.get_policy(policy_id)
            if policy_def:
                policies.append(
                    {
                        "policy_id": policy_id,
                        "definition": policy_def,
                        "score": item.get("score", 0),
                    },
                )
        return policies

    async def add_uiref(self, uiref_id: str, uiref_def: dict[str, Any], description: str) -> None:
        """Store a UI reference definition."""
        path = self._artifact_path("uirefs", uiref_id)
        path.write_text(json.dumps(uiref_def, indent=2), encoding="utf-8")
        self._update_cache("uirefs", uiref_id, uiref_def)

        mem0 = self._get_mem0()
        mem0.add(
            [{"role": "user", "content": f"UIRef: {uiref_id}\n{description}"}],
            user_id="system",
            metadata={"type": "uiref", "uiref_id": uiref_id},
        )

    async def get_uiref(self, uiref_id: str) -> dict[str, Any] | None:
        """Get a UI reference definition by ID."""
        self._refresh_cache_if_needed()
        cache = self._cache["uirefs"]
        if uiref_id in cache:
            return cache[uiref_id]

        path = self._artifact_path("uirefs", uiref_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        cache[uiref_id] = data
        return data

    async def add_knowledge(
        self,
        topic: str,
        content: str,
        domain: str,
        *,
        source: str = "manual",
    ) -> None:
        """Add domain knowledge to semantic memory."""
        mem0 = self._get_mem0()
        mem0.add(
            [{"role": "user", "content": f"Topic: {topic}\n{content}"}],
            user_id="system",
            metadata={"type": "knowledge", "domain": domain, "source": source, "topic": topic},
        )

    async def search_knowledge(
        self,
        query: str,
        domain: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search domain knowledge."""
        mem0 = self._get_mem0()
        results = mem0.search(query, user_id="system", limit=limit)

        if domain:
            results = [item for item in results if item.get("metadata", {}).get("domain") == domain]

        return results
