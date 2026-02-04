"""Application settings loader for ARIA."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from pydantic_settings import PydanticBaseSettingsSource

from aria.config.api import APIConfig
from aria.config.eye import EyeConfig
from aria.config.hand import HandConfig
from aria.config.job_apply import JobApplyConfig
from aria.config.kafka import KafkaConfig
from aria.config.learning import LearningConfig
from aria.config.llm import LLMConfig
from aria.config.memory import MemoryConfig
from aria.config.redis import RedisConfig
from aria.config.safety import SafetyConfig
from aria.config.ui import UIConfig
from aria.config.voice import VoiceConfig


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_settings() -> dict[str, Any]:
    root = _project_root()
    config_dir = root / "config"
    base = _load_yaml_file(config_dir / "default.yaml")
    memory = _load_yaml_file(config_dir / "memory.yaml")
    llm = _load_yaml_file(config_dir / "llm.yaml")
    eye = _load_yaml_file(config_dir / "eye.yaml")
    hand = _load_yaml_file(config_dir / "hand.yaml")
    job_apply = _load_yaml_file(config_dir / "job_apply.yaml")
    learning = _load_yaml_file(config_dir / "learning.yaml")
    ui = _load_yaml_file(config_dir / "ui.yaml")
    api = _load_yaml_file(config_dir / "api.yaml")
    voice = _load_yaml_file(config_dir / "voice.yaml")
    safety = _load_yaml_file(config_dir / "safety.yaml")
    base = _deep_merge(base, memory)
    base = _deep_merge(base, llm)
    base = _deep_merge(base, eye)
    base = _deep_merge(base, hand)
    base = _deep_merge(base, job_apply)
    base = _deep_merge(base, learning)
    base = _deep_merge(base, ui)
    base = _deep_merge(base, api)
    base = _deep_merge(base, voice)
    base = _deep_merge(base, safety)
    env_name = os.getenv("ARIA_ENV", "development")
    env_config = _load_yaml_file(config_dir / f"{env_name}.yaml")
    return _deep_merge(base, env_config)


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str, default: int) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def _env_overrides() -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915
    root = _project_root()
    env = _read_dotenv(root / ".env")
    env.update(os.environ)

    data: dict[str, Any] = {}

    if "ARIA_ENV" in env:
        data["env"] = env["ARIA_ENV"]
    if "ARIA_DEBUG" in env:
        data["debug"] = _parse_bool(env["ARIA_DEBUG"])

    if any(key.startswith("KAFKA_") for key in env):
        kafka: dict[str, Any] = {}
        if "KAFKA_BOOTSTRAP_SERVERS" in env:
            kafka["bootstrap_servers"] = [
                item.strip()
                for item in env["KAFKA_BOOTSTRAP_SERVERS"].split(",")
                if item.strip()
            ]
        if "KAFKA_CONSUMER_GROUP" in env:
            kafka["consumer_group"] = env["KAFKA_CONSUMER_GROUP"]
        if "KAFKA_AUTO_OFFSET_RESET" in env:
            kafka["auto_offset_reset"] = env["KAFKA_AUTO_OFFSET_RESET"]
        if kafka:
            data["kafka"] = kafka

    if any(key.startswith("REDIS_") for key in env):
        redis: dict[str, Any] = {}
        if "REDIS_HOST" in env:
            redis["host"] = env["REDIS_HOST"]
        if "REDIS_PORT" in env:
            redis["port"] = _parse_int(env["REDIS_PORT"], 6379)
        if "REDIS_DB" in env:
            redis["db"] = _parse_int(env["REDIS_DB"], 0)
        if env.get("REDIS_PASSWORD"):
            redis["password"] = env["REDIS_PASSWORD"]
        if redis:
            data["redis"] = redis

    if any(key.startswith(("LLM_", "OLLAMA_")) for key in env):
        llm: dict[str, Any] = {}
        if "LLM_PROVIDER" in env:
            llm["provider"] = env["LLM_PROVIDER"]
        if "OLLAMA_BASE_URL" in env:
            llm["base_url"] = env["OLLAMA_BASE_URL"]
        if "OLLAMA_MODEL_BRAIN" in env:
            llm["model_name"] = env["OLLAMA_MODEL_BRAIN"]

        api_key = env.get("LLM_API_KEY") or env.get("OPENAI_API_KEY") or env.get(
            "ANTHROPIC_API_KEY",
        )
        if api_key:
            llm["api_key"] = api_key

        roles: dict[str, dict[str, Any]] = {}
        role_env_map = {
            "brain": "OLLAMA_MODEL_BRAIN",
            "brain_persian": "OLLAMA_MODEL_BRAIN_PERSIAN",
            "eye": "OLLAMA_MODEL_EYE",
            "coder": "OLLAMA_MODEL_CODER",
            "audio": "OLLAMA_MODEL_AUDIO",
            "ml": "OLLAMA_MODEL_ML",
        }
        for role, env_key in role_env_map.items():
            if env.get(env_key):
                roles.setdefault(role, {})["model_name"] = env[env_key]
        if roles:
            llm["roles"] = roles

        if llm:
            data["llm"] = llm

    if any(key in env for key in ("UI_HOST", "UI_PORT", "UI_THEME")):
        ui: dict[str, Any] = {}
        if "UI_HOST" in env:
            ui["host"] = env["UI_HOST"]
        if "UI_PORT" in env:
            ui["port"] = _parse_int(env["UI_PORT"], 8501)
        if "UI_THEME" in env:
            ui["theme"] = env["UI_THEME"]
        if ui:
            data["ui"] = ui

    if any(
        key in env
        for key in (
            "API_HOST",
            "API_PORT",
            "API_RELOAD",
            "CORS_ORIGINS",
            "CORS_ENABLED",
            "WS_PING_INTERVAL",
            "WS_MAX_CONNECTIONS",
        )
    ):
        api: dict[str, Any] = {}
        if "API_HOST" in env:
            api["host"] = env["API_HOST"]
        if "API_PORT" in env:
            api["port"] = _parse_int(env["API_PORT"], 8000)
        if "API_RELOAD" in env:
            api["reload"] = _parse_bool(env["API_RELOAD"])

        cors: dict[str, Any] = {}
        if "CORS_ENABLED" in env:
            cors["enabled"] = _parse_bool(env["CORS_ENABLED"])
        if "CORS_ORIGINS" in env:
            cors["origins"] = [
                origin.strip()
                for origin in env["CORS_ORIGINS"].split(",")
                if origin.strip()
            ]
        if cors:
            api["cors"] = cors

        websocket: dict[str, Any] = {}
        if "WS_PING_INTERVAL" in env:
            websocket["ping_interval"] = _parse_int(env["WS_PING_INTERVAL"], 30)
        if "WS_MAX_CONNECTIONS" in env:
            websocket["max_connections"] = _parse_int(env["WS_MAX_CONNECTIONS"], 100)
        if websocket:
            api["websocket"] = websocket

        if api:
            data["api"] = api

    if "SCREENSHOT_DIR" in env or "SCREENSHOT_QUALITY" in env:
        eye: dict[str, Any] = {}
        screenshot: dict[str, Any] = {}
        if "SCREENSHOT_DIR" in env:
            screenshot["dir"] = env["SCREENSHOT_DIR"]
        if "SCREENSHOT_QUALITY" in env:
            screenshot["quality"] = _parse_int(env["SCREENSHOT_QUALITY"], 85)
        if screenshot:
            eye["screenshot"] = screenshot
        if eye:
            data["eye"] = eye

    if any(key.startswith(("BROWSER_", "PLAYWRIGHT_")) for key in env):
        hand: dict[str, Any] = {}
        browser: dict[str, Any] = {}
        if "BROWSER_HEADLESS" in env:
            browser["headless"] = _parse_bool(env["BROWSER_HEADLESS"])
        if "BROWSER_SLOW_MO" in env:
            browser["slow_mo"] = _parse_int(env["BROWSER_SLOW_MO"], 50)
        if "PLAYWRIGHT_TIMEOUT" in env:
            browser["timeout"] = _parse_int(env["PLAYWRIGHT_TIMEOUT"], 30000)
        if browser:
            hand["browser"] = browser
        if hand:
            data["hand"] = hand

    if any(
        key in env
        for key in (
            "LINKEDIN_EMAIL",
            "PROFILES_DIR",
            "JOBS_DIR",
            "APPLICATIONS_DIR",
        )
    ):
        job_apply: dict[str, Any] = {}
        if "LINKEDIN_EMAIL" in env:
            job_apply["linkedin"] = {"email": env["LINKEDIN_EMAIL"]}
        if "PROFILES_DIR" in env:
            job_apply["profiles_dir"] = env["PROFILES_DIR"]
        if "JOBS_DIR" in env:
            job_apply["jobs_dir"] = env["JOBS_DIR"]
        if "APPLICATIONS_DIR" in env:
            job_apply["applications_dir"] = env["APPLICATIONS_DIR"]
        if job_apply:
            data["job_apply"] = job_apply

    if any(
        key in env
        for key in (
            "LEARNING_ENABLED",
            "ARTIFACTS_DIR",
            "RECORDINGS_DIR",
            "KAFKA_CONSUMER_GROUP_LEARNING",
        )
    ):
        learning: dict[str, Any] = {}
        if "LEARNING_ENABLED" in env:
            learning["enabled"] = _parse_bool(env["LEARNING_ENABLED"])
        if "ARTIFACTS_DIR" in env:
            learning["artifacts_dir"] = env["ARTIFACTS_DIR"]
        if "RECORDINGS_DIR" in env:
            learning["recordings_dir"] = env["RECORDINGS_DIR"]
        if "KAFKA_CONSUMER_GROUP_LEARNING" in env:
            learning["consumer_group"] = env["KAFKA_CONSUMER_GROUP_LEARNING"]
        if learning:
            data["learning"] = learning

    if any(key in env for key in ("VOICE_ENABLED", "STT_MODEL", "STT_AUDIO_MODEL")):
        voice: dict[str, Any] = {}
        if "VOICE_ENABLED" in env:
            voice["enabled"] = _parse_bool(env["VOICE_ENABLED"])
        if "STT_MODEL" in env or "STT_AUDIO_MODEL" in env:
            stt: dict[str, Any] = {}
            if "STT_MODEL" in env:
                stt["primary"] = env["STT_MODEL"]
            if "STT_AUDIO_MODEL" in env:
                stt["audio_model"] = env["STT_AUDIO_MODEL"]
            if stt:
                voice["stt"] = stt
        if voice:
            data["voice"] = voice

    if any(
        key in env
        for key in (
            "SAFETY_ENABLED",
            "SAFETY_STRICT_MODE",
            "DOMAIN_ALLOWLIST_PATH",
            "DOMAIN_DENYLIST_PATH",
            "RATE_LIMIT_ENABLED",
            "RATE_LIMIT_DEFAULT",
            "RATE_LIMIT_SUBMIT",
            "RATE_LIMIT_APPLY",
            "RATE_LIMIT_API_CALL",
            "RATE_LIMIT_LOGIN",
            "PII_DETECTION_ENABLED",
            "PII_LOG_REDACTION",
            "PII_REDACT_IN_EVENTS",
        )
    ):
        safety: dict[str, Any] = {}
        if "SAFETY_ENABLED" in env:
            safety["enabled"] = _parse_bool(env["SAFETY_ENABLED"])
        if "SAFETY_STRICT_MODE" in env:
            safety["strict_mode"] = _parse_bool(env["SAFETY_STRICT_MODE"])
        if "RATE_LIMIT_ENABLED" in env:
            safety["rate_limit_enabled"] = _parse_bool(env["RATE_LIMIT_ENABLED"])

        domain_policy: dict[str, Any] = {}
        if "DOMAIN_ALLOWLIST_PATH" in env:
            domain_policy["allowlist_path"] = env["DOMAIN_ALLOWLIST_PATH"]
        if "DOMAIN_DENYLIST_PATH" in env:
            domain_policy["denylist_path"] = env["DOMAIN_DENYLIST_PATH"]
        if domain_policy:
            safety["domain_policy"] = domain_policy

        rate_limits: dict[str, Any] = {}
        if "RATE_LIMIT_DEFAULT" in env:
            rate_limits["default"] = env["RATE_LIMIT_DEFAULT"]
        if "RATE_LIMIT_SUBMIT" in env:
            rate_limits["submit"] = env["RATE_LIMIT_SUBMIT"]
        if "RATE_LIMIT_APPLY" in env:
            rate_limits["apply"] = env["RATE_LIMIT_APPLY"]
        if "RATE_LIMIT_API_CALL" in env:
            rate_limits["api_call"] = env["RATE_LIMIT_API_CALL"]
        if "RATE_LIMIT_LOGIN" in env:
            rate_limits["login"] = env["RATE_LIMIT_LOGIN"]
        if rate_limits:
            safety["rate_limits"] = rate_limits

        pii: dict[str, Any] = {}
        if "PII_DETECTION_ENABLED" in env:
            pii["detect"] = _parse_bool(env["PII_DETECTION_ENABLED"])
        if "PII_LOG_REDACTION" in env:
            pii["redact_in_logs"] = _parse_bool(env["PII_LOG_REDACTION"])
        if "PII_REDACT_IN_EVENTS" in env:
            pii["redact_in_events"] = _parse_bool(env["PII_REDACT_IN_EVENTS"])
        if pii:
            safety["pii"] = pii

        if safety:
            data["safety"] = safety

    return data


class ARIASettings(BaseSettings):
    """Main ARIA settings model."""

    env: str = Field(default="development")
    debug: bool = False
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    eye: EyeConfig = Field(default_factory=EyeConfig)
    hand: HandConfig = Field(default_factory=HandConfig)
    job_apply: JobApplyConfig = Field(default_factory=JobApplyConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)

    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],  # noqa: ARG003
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize the settings sources for ARIA configuration."""
        return (
            init_settings,
            _env_settings_source,
            _yaml_settings_source,
            file_secret_settings,
        )


def _yaml_settings_source(
    settings_cls: type[BaseSettings] | None = None,
) -> dict[str, Any]:
    _ = settings_cls
    return _load_yaml_settings()


def _env_settings_source(
    settings_cls: type[BaseSettings] | None = None,
) -> dict[str, Any]:
    _ = settings_cls
    return _env_overrides()


@lru_cache
def get_settings() -> ARIASettings:
    """Return cached ARIA settings."""
    return ARIASettings()
