# Contributing

Thank you for contributing to ARIA. Please follow these guidelines.

## Code Style

- Use Python 3.11+.
- Format and lint with Ruff.
- Type-check with mypy (strict).
- Add type hints and Google-style docstrings for all public functions.

```bash
ruff format src/ tests/
ruff check src/ tests/
mypy src/
```

## Commit Conventions

This project uses Conventional Commits with scoped types.

Examples:
- `feat(core): add base configuration loader`
- `fix(memory): handle empty embeddings`

Allowed types: feat, fix, docs, style, refactor, test, chore, ci
Allowed scopes: core, brain, eye, hand, memory, ui, api, config

## Pull Request Process

1. Create a feature branch.
2. Ensure tests and linting pass.
3. Update documentation as needed.
4. Keep PRs focused and small when possible.

## Testing Requirements

- Unit tests for new modules.
- Integration tests for adapters.

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Documentation Standards

- Code comments and docstrings must be in English.
- All documentation should be in English for consistency and accessibility.
