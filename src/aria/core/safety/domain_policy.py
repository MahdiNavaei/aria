"""Domain Policy Engine for ARIA Safety."""

from __future__ import annotations

import fnmatch
from enum import Enum
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

import yaml

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class DomainAction(str, Enum):
    """Action to take for a domain."""

    ALLOW = "allow"
    READ_ONLY = "read_only"
    BLOCK = "block"
    REQUIRE_HUMAN = "require_human"


class DomainCheckResult(NamedTuple):
    """Result of domain policy check."""

    allowed: bool
    action: DomainAction
    reason: str
    domain: str
    matched_rule: str | None


class DomainPolicy:
    """Domain policy engine for URL access control."""

    def __init__(
        self,
        allowlist_path: str = "config/domains/allowlist.yaml",
        denylist_path: str = "config/domains/denylist.yaml",
        default_action: DomainAction = DomainAction.BLOCK,
        mode: str = "allowlist",
    ) -> None:
        self.default_action = default_action
        self.mode = mode.lower()
        self._allowlist: dict[str, list[str]] = {}
        self._denylist: list[str] = []
        self._read_only: dict[str, list[str]] = {}

        self._load_policies(allowlist_path, denylist_path)

    def _load_policies(self, allowlist_path: str, denylist_path: str) -> None:
        """Load policy files."""
        allowlist_file = Path(allowlist_path)
        if allowlist_file.exists():
            with allowlist_file.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
                for domain_group, config in data.items():
                    if domain_group == "global_denylist":
                        self._denylist.extend(config or [])
                    elif isinstance(config, dict):
                        self._allowlist[domain_group] = list(config.get("allowed", []))
                        self._read_only[domain_group] = list(config.get("read_only", []))
            logger.info(
                "Domain policy loaded",
                allowlist_groups=len(self._allowlist),
                denylist_count=len(self._denylist),
            )
        else:
            logger.warning("Allowlist file not found", path=str(allowlist_file))

        denylist_file = Path(denylist_path)
        if denylist_file.exists():
            with denylist_file.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
                self._denylist.extend(data.get("domains", []))
        elif denylist_path:
            logger.warning("Denylist file not found", path=str(denylist_file))

        # De-duplicate denylist
        self._denylist = list(dict.fromkeys(self._denylist))

    def check(self, url: str, domain_context: str = "job_apply") -> DomainCheckResult:
        """Check if URL is allowed."""
        try:
            parsed = urlparse(url if "://" in url else f"https://{url}")
            host = parsed.netloc.lower()
            if not host and parsed.path:
                host = parsed.path.lower()

            if ":" in host:
                host = host.split(":")[0]

        except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
            return DomainCheckResult(
                allowed=False,
                action=DomainAction.BLOCK,
                reason=f"Invalid URL: {exc}",
                domain="",
                matched_rule=None,
            )

        if not host:
            return DomainCheckResult(
                allowed=False,
                action=DomainAction.BLOCK,
                reason="Invalid URL: missing host",
                domain="",
                matched_rule=None,
            )

        # Step 1: Check global denylist
        for pattern in self._denylist:
            if self._matches(host, pattern) or self._matches(url, pattern):
                logger.warning("URL blocked by denylist", url=url, pattern=pattern)
                return DomainCheckResult(
                    allowed=False,
                    action=DomainAction.BLOCK,
                    reason=f"Domain is in denylist (matched: {pattern})",
                    domain=host,
                    matched_rule=pattern,
                )

        # Step 2: Check read-only first (more restrictive)
        read_only_patterns = self._read_only.get(domain_context, [])
        for pattern in read_only_patterns:
            if self._matches(host, pattern):
                return DomainCheckResult(
                    allowed=True,
                    action=DomainAction.READ_ONLY,
                    reason=f"Domain is read-only for {domain_context}",
                    domain=host,
                    matched_rule=pattern,
                )

        # Step 3: Allowlist (if configured)
        if self.mode == "allowlist":
            allowed_patterns = self._allowlist.get(domain_context, [])
            for pattern in allowed_patterns:
                if self._matches(host, pattern):
                    return DomainCheckResult(
                        allowed=True,
                        action=DomainAction.ALLOW,
                        reason=f"Domain is in allowlist for {domain_context}",
                        domain=host,
                        matched_rule=pattern,
                    )

        default_action = self.default_action

        logger.info(
            "URL not in any list, applying default",
            url=url,
            default=default_action,
        )

        allowed = default_action in {
            DomainAction.ALLOW,
            DomainAction.READ_ONLY,
            DomainAction.REQUIRE_HUMAN,
        }
        return DomainCheckResult(
            allowed=allowed,
            action=default_action,
            reason=f"Domain not in allowlist, default action: {default_action}",
            domain=host,
            matched_rule=None,
        )

    def _matches(self, value: str, pattern: str) -> bool:
        """Check if value matches pattern (supports wildcards)."""
        return fnmatch.fnmatch(value.lower(), pattern.lower())

    def add_to_allowlist(self, domain: str, domain_context: str = "job_apply") -> None:
        """Dynamically add domain to allowlist."""
        self._allowlist.setdefault(domain_context, []).append(domain)
        logger.info("Domain added to allowlist", domain=domain, context=domain_context)

    def add_to_denylist(self, domain: str) -> None:
        """Dynamically add domain to denylist."""
        self._denylist.append(domain)
        logger.info("Domain added to denylist", domain=domain)


_domain_policy: DomainPolicy | None = None


def get_domain_policy() -> DomainPolicy:
    """Get domain policy singleton."""
    global _domain_policy
    if _domain_policy is None:
        from aria.config import get_settings

        settings = get_settings()
        _domain_policy = DomainPolicy(
            allowlist_path=settings.safety.domain_policy.allowlist_path,
            denylist_path=settings.safety.domain_policy.denylist_path,
            default_action=DomainAction(settings.safety.domain_policy.default_action),
            mode=settings.safety.domain_policy.mode,
        )
    return _domain_policy
