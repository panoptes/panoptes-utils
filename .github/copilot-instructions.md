# PANOPTES Utilities - GitHub Copilot Quick Reference

> **📖 IMPORTANT:** See [`AGENTS.md`](../AGENTS.md) for comprehensive guidelines, coding standards, module details, and release processes.

## Essential Commands

```bash
# Setup (first time)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras --group dev

# Development cycle
uv run pytest                    # Run all tests (2-5 min)
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv build                         # Build package

# Before every commit (CI will fail without these)
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/test_utils.py
```

## Code Standards Checklist

- ✅ Python 3.12+ with type hints
- ✅ Google-style docstrings
- ✅ Line length: 110 chars
- ✅ Use `from loguru import logger` + `logger.<level>(...)`, `pathlib.Path`
- ✅ Update `CHANGELOG.md` for all PRs

## Quick Navigation

```
src/panoptes/utils/
├── cli/           # Typer CLI commands
├── config/        # Flask server + client
├── images/        # astrometry.net, dcraw
├── serial/        # Serial device comm
├── time.py        # CountdownTimer, wait_for_events
└── serializers.py # JSON/YAML serialization
```

## Critical Info

**Config Server:** Port 6563 (check if in use)  
**Test Config:** `tests/testing.yaml`  
**Timing:** Never cancel - env setup (1-3 min), tests (2-5 min), deps (5-8 min)

## Need More Info?

| Topic | See |
|-------|-----|
| Release process | AGENTS.md → "Creating a Release" |
| Module guidelines | AGENTS.md → "Module Guidelines" |
| Testing strategy | AGENTS.md → "Testing Strategy" |
| Astronomy domain | AGENTS.md → "Astronomy Domain Knowledge" |
| All details | **[AGENTS.md](../AGENTS.md)** ← Read this first |
