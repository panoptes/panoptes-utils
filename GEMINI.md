# Gemini CLI Guidelines for PANOPTES Utilities

This document provides specific instructions for the Gemini CLI agent. For all general project guidelines, development workflows, and technical standards, refer to the primary agent documentation.

## Primary Guidelines

**Default to `AGENTS.md`:** All architectural patterns, coding standards, testing requirements, and module-specific instructions defined in [AGENTS.md](AGENTS.md) are foundational mandates and take absolute precedence.

## Gemini-Specific Instructions

### Environment & Tooling
- **UV Executable:** Always use the `uv` executable for environment management, dependency installation, and running commands (e.g., `uv run pytest`, `uv lock`).
- **Shell Commands:** When using `run_shell_command`, ensure that commands are compatible with the `uv` environment.

### Workflow Integration
- **Research Phase:** Use `grep_search` and `glob` to align with the patterns described in `AGENTS.md` before proposing changes.
- **Validation:** Always run tests using `uv run pytest` after any modification. Note the specific testing markers and plot-blocking doctests mentioned in `AGENTS.md`.
- **Changelog:** Rigorously follow the `CHANGELOG.md` update requirements specified in the "Making Changes" section of `AGENTS.md`.

### Utility Awareness
- **Search Before Implementation:** Always check `panoptes.utils` for existing functionality. Specifically, use `panoptes.utils.serializers` for any data transmission or persistence tasks to ensure astronomical types (Quantities, Times) are handled correctly and consistently.

## Quick Links
- [AGENTS.md](AGENTS.md) - Full project guidelines.
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow.
- [pyproject.toml](pyproject.toml) - Dependencies and tool configuration.
