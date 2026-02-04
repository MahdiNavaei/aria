"""Safety configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DomainPolicyConfig(BaseModel):
    """Domain policy configuration."""

    mode: str = "allowlist"
    default_action: str = "block"
    allowlist_path: str = "config/domains/allowlist.yaml"
    denylist_path: str = "config/domains/denylist.yaml"


class RiskLevelsConfig(BaseModel):
    """Risk levels configuration."""

    high_risk_capabilities: list[str] = Field(
        default_factory=lambda: [
            "web.submit_application",
            "web.click_submit",
            "web.final_submit",
            "web.upload_file",
            "web.upload_resume",
            "web.upload_cover_letter",
            "web.login",
            "web.enter_credentials",
            "web.enter_password",
            "desktop.run_command",
            "desktop.delete_file",
            "desktop.modify_system",
            "web.click_payment",
            "web.enter_card_info",
        ],
    )
    medium_risk_capabilities: list[str] = Field(
        default_factory=lambda: [
            "web.fill_form",
            "web.fill",
            "web.type",
            "web.select",
            "web.click",
            "desktop.click",
            "desktop.type",
            "desktop.hotkey",
            "web.navigate",
        ],
    )
    low_risk_capabilities: list[str] = Field(
        default_factory=lambda: [
            "web.extract",
            "web.screenshot",
            "web.get_text",
            "web.scroll",
            "web.wait",
            "desktop.screenshot",
            "desktop.read_screen",
            "ml.match_job",
            "ml.extract_job_info",
            "ml.generate_cover_letter",
        ],
    )


class PIIConfig(BaseModel):
    """PII handling configuration."""

    detect: bool = True
    redact_in_logs: bool = True
    redact_in_events: bool = False
    entities: list[str] = Field(
        default_factory=lambda: [
            "EMAIL",
            "PHONE",
            "CREDIT_CARD",
            "IBAN",
            "NATIONAL_ID",
            "PASSWORD",
        ],
    )


class SafetyConfig(BaseModel):
    """Top-level safety configuration."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = True
    strict_mode: bool = False
    rate_limit_enabled: bool = True
    domain_policy: DomainPolicyConfig = Field(default_factory=DomainPolicyConfig)
    risk_levels: RiskLevelsConfig = Field(default_factory=RiskLevelsConfig)
    rate_limits: dict[str, str] = Field(
        default_factory=lambda: {
            "default": "100/minute",
            "submit": "10/hour",
            "apply": "50/day",
            "api_call": "1000/hour",
            "login": "5/minute",
        },
    )
    pii: PIIConfig = Field(default_factory=PIIConfig)
