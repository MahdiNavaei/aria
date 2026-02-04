# Vendored Projects

These are forked/customized third-party projects.

## Projects

| Project | Upstream | Version | Purpose |
|---------|----------|---------|---------|
| browser-use | github.com/browser-use/browser-use | 0.5.2 | Browser automation |
| skyvern | github.com/Skyvern-AI/skyvern | v1.0.9 | Form filling with vision |
| aihawk | github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk | latest | LinkedIn automation |
| openadapt | github.com/OpenAdaptAI/OpenAdapt | latest | Desktop learn-by-demo |

## Customization Pattern

Each project has an `aria_extensions/` folder with our custom code:
- HITL hooks
- Kafka event emission
- Custom adapters

## Updating

To update from upstream:
1. Check UPSTREAM_VERSION.md for current version
2. Fetch upstream changes
3. Merge carefully, preserving aria_extensions/
4. Update UPSTREAM_VERSION.md
