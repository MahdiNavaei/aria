# AIHawk Upstream

- **Repository**: https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
- **Version**: latest
- **Commit**: ae33178d7bafbbcccd6d71f55953cf1ab243423c
- **Date**: 2026-02-03

## Why Vendored

AIHawk provides LinkedIn automation, but needs:
1. Integration with ARIA's event system (Kafka)
2. HITL hooks for CAPTCHA/2FA
3. Integration with Brain planning
4. Custom form filling via Skyvern-style flow

## ARIA Customizations

- aria_extensions/event_hooks.py - Kafka event emission
- aria_extensions/hitl_bridge.py - HITL integration
- aria_extensions/profile_adapter.py - Use ARIA user profile
