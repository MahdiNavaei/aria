import yaml

from aria.core.safety.domain_policy import DomainAction, DomainPolicy


def test_domain_policy_allow_and_read_only(tmp_path) -> None:
    allowlist = {
        "job_apply": {
            "allowed": ["*.example.com"],
            "read_only": ["readonly.example.com"],
        },
        "global_denylist": ["blocked.example.com"],
    }
    denylist = {"domains": ["denied.example.com"]}

    allow_path = tmp_path / "allowlist.yaml"
    deny_path = tmp_path / "denylist.yaml"
    allow_path.write_text(yaml.safe_dump(allowlist), encoding="utf-8")
    deny_path.write_text(yaml.safe_dump(denylist), encoding="utf-8")

    policy = DomainPolicy(
        allowlist_path=str(allow_path),
        denylist_path=str(deny_path),
        default_action=DomainAction.BLOCK,
    )

    allowed = policy.check("https://jobs.example.com/role", "job_apply")
    assert allowed.allowed is True
    assert allowed.action == DomainAction.ALLOW

    read_only = policy.check("https://readonly.example.com/search", "job_apply")
    assert read_only.allowed is True
    assert read_only.action == DomainAction.READ_ONLY

    blocked = policy.check("https://blocked.example.com/", "job_apply")
    assert blocked.allowed is False
    assert blocked.action == DomainAction.BLOCK

    denied = policy.check("https://denied.example.com/", "job_apply")
    assert denied.allowed is False


def test_domain_policy_default_block(tmp_path) -> None:
    allow_path = tmp_path / "allowlist.yaml"
    deny_path = tmp_path / "denylist.yaml"
    allow_path.write_text(
        yaml.safe_dump({"job_apply": {"allowed": []}}),
        encoding="utf-8",
    )
    deny_path.write_text(yaml.safe_dump({"domains": []}), encoding="utf-8")

    policy = DomainPolicy(
        allowlist_path=str(allow_path),
        denylist_path=str(deny_path),
        default_action=DomainAction.BLOCK,
    )

    result = policy.check("https://unknown.example.org", "job_apply")
    assert result.allowed is False
    assert result.action == DomainAction.BLOCK
