# AI Agent Guidelines for PANOPTES Utilities

This document provides guidelines for AI coding agents working with the PANOPTES Utilities (panoptes-utils) codebase. It is designed to be tool-agnostic and applicable to any AI assistant working on this project.

## Project Overview

PANOPTES Utilities is a Python library providing astronomical utilities for the PANOPTES ecosystem. It includes CLI tools for image processing, a configuration server, and various utility modules for astronomical data processing. This library serves as the foundation for other PANOPTES projects like [POCS](https://github.com/panoptes/POCS).

**Key Characteristics:**
- **Language:** Python 3.12+ (type hints expected)
- **Architecture:** Modular utility library with CLI tools and services
- **Domain:** Astronomy, image processing, configuration management
- **Testing:** pytest with high coverage requirements
- **Build System:** UV (modern Python package and environment manager)
- **Code Style:** Ruff for linting and formatting

## Essential Reading

Before making changes, review these documents:

1. **README:** `README.md` - Installation and basic usage
2. **Contributing:** `CONTRIBUTING.md` - Development workflow reference
3. **Configuration:** `pyproject.toml` - Project dependencies and configuration
4. **Documentation:** `docs/` - Detailed documentation on modules

## Project Structure

```
panoptes-utils/
├── src/panoptes/utils/         # Main source code
│   ├── cli/                    # Command-line interfaces
│   │   └── main.py             # Main CLI entry point
│   ├── config/                 # Configuration server and client
│   │   ├── cli.py              # Config server CLI
│   │   ├── client.py           # Config client
│   │   └── server.py           # Config server implementation
│   ├── images/                 # Image processing utilities
│   ├── serial/                 # Serial device communication
│   ├── database/               # Database utilities
│   ├── time.py                 # Time utilities (CountdownTimer, etc.)
│   ├── serializers.py          # Data serialization
│   ├── horizon.py              # Horizon calculations
│   └── utils.py                # General utilities
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest configuration and fixtures
│   ├── testing.yaml            # Test configuration file
│   ├── config/                 # Config tests
│   ├── images/                 # Image processing tests
│   └── data/                   # Test data files
├── docs/                       # Sphinx documentation
├── examples/                   # Example notebooks and scripts
└── pyproject.toml              # Project configuration and dependencies
```

## Development Workflow

### 1. Understanding Changes

**Before making any changes:**
- Check if an issue exists for the change; reference it in commits/PRs
- Review relevant module documentation to understand affected components
- Review existing tests to understand expected behavior
- Check `pyproject.toml` for dependencies and project configuration

### 2. Code Standards

**Style and Formatting:**
- Use Ruff for linting and formatting (configured in `pyproject.toml`)
- Line length: 110 characters
- Quote style: double quotes
- Follow PEP 8 conventions

**Type Hints:**
- Required for all function signatures
- Use modern Python 3.12+ type syntax
- Import from `typing` when necessary

**Documentation:**
- Docstrings for all public classes and functions
- Use Google-style docstrings
- Include examples in docstrings when helpful

### 3. Testing Requirements

**All code changes must include tests:**
- Unit tests in `tests/` directory
- Test files named `test_*.py`
- Use pytest fixtures from `conftest.py`
- Maintain or improve code coverage
- Run tests locally before committing: `uv run pytest`

**Testing markers available:**
```python
@pytest.mark.plate_solve      # Tests requiring plate solving (astrometry.net)
@pytest.mark.slow             # Tests that take longer to run
```

### 4. Dependencies

**Adding Dependencies:**
- Add to `dependencies` in `pyproject.toml` for runtime requirements
- Add to `[project.optional-dependencies]` for optional features
- Use `uv sync --extra <package>` to install optional extras
- Add to `[dependency-groups]` for development dependencies (testing, lint, etc.)
- Consider which extras group the dependency belongs to:
  - `config`: Configuration server dependencies
  - `images`: Image processing dependencies
  - `testing`: Testing tools
  - `docs`: Documentation building

**Optional Dependencies:**
- `config`: Flask, gevent, scalpl for configuration server
- `images`: matplotlib, photutils, pillow for image processing
- `testing`: pytest, coverage, and testing tools
- `docs`: Sphinx and documentation tools

### 5. Making Changes

**File Editing Best Practices:**
1. Read entire files or large sections before editing
2. Preserve existing code style and patterns
3. Make minimal, focused changes
4. Validate changes by checking for errors after editing
5. Run relevant tests to confirm functionality

**Commit Messages:**
- Clear, descriptive commit messages
- Reference issue numbers when applicable
- Format: `Brief description (#issue-number)`

**CHANGELOG Updates:**
- **Always update `CHANGELOG.md`** when submitting a PR
- Add entry under the appropriate section (Added, Changed, Fixed, Removed)
- Include PR number reference (e.g., `#123`)
- Follow the existing format: `* Brief description of change. #PR-number`
- Place new entries at the top of the file under a new version heading if starting a new release

## Module Guidelines

### Configuration Module

**Location:** `src/panoptes/utils/config/`

The configuration system provides centralized configuration management through a client-server architecture.

**Components:**
- `server.py`: Flask-based configuration server
- `client.py`: Configuration client for accessing server
- `cli.py`: Command-line interface for starting server

**When modifying:**
- Understand client-server communication protocol
- Preserve backward compatibility with POCS and other clients
- Test with `tests/testing.yaml` configuration
- Ensure thread safety for concurrent access

**Starting the config server:**
```bash
panoptes-config-server run --config-file tests/testing.yaml
```

### CLI Module

**Location:** `src/panoptes/utils/cli/`

Command-line tools built with Typer.

**When modifying:**
- Use Typer decorators and type hints
- Provide clear help text and examples
- Test commands manually and with unit tests
- Follow existing command patterns

**Available commands:**
- `panoptes-utils image`: Image processing commands
- `panoptes-config-server`: Configuration server management

### Image Processing Module

**Location:** `src/panoptes/utils/images/`

Utilities for astronomical image processing, including plate solving, CR2 to FITS conversion, and image analysis.

**When modifying:**
- Understand dependencies on astrometry.net and dcraw
- Test with sample images in `tests/images/data/`
- Handle missing dependencies gracefully
- Validate FITS headers and metadata

**System dependencies required:**
- `astrometry.net` for plate solving
- `dcraw` for CR2 conversion
- `exiftool` for metadata extraction

### Time Utilities

**Location:** `src/panoptes/utils/time.py`

Time-related utilities including `CountdownTimer` and `wait_for_events`.

**When modifying:**
- Use `astropy.time` for astronomical time handling
- Ensure timezone awareness (prefer UTC)
- Test edge cases (timeouts, concurrent access)
- Maintain compatibility with POCS usage

### Serial Communication

**Location:** `src/panoptes/utils/serial/` and `src/panoptes/utils/rs232.py`

Serial device communication utilities.

**When modifying:**
- Handle connection errors gracefully
- Implement appropriate timeouts
- Test with simulator/mock devices
- Consider thread safety

## Configuration

**Configuration files:** `tests/testing.yaml` (for testing)

**Important configuration sections:**
- `name`: Observatory/system name
- `location`: Geographic coordinates
- `directories`: Data storage locations
- Custom sections for specific modules

### Config Server

The configuration server provides a REST API for centralized configuration management.

**Starting the config server locally:**
```bash
# For development
panoptes-config-server run --config-file tests/testing.yaml

# With custom host/port
panoptes-config-server --host 0.0.0.0 --port 8765 run --config-file tests/testing.yaml
```

**Notes:**
- Default port is 8765
- Server provides REST API for configuration access
- Used by POCS and other PANOPTES components

**When modifying configuration:**
- Maintain backward compatibility when possible
- Update example configs in `tests/`
- Document new configuration options
- Validate configuration structure
- Restart config server after modifying config files

## Common Tasks

### Adding a New CLI Command

1. Add command to `src/panoptes/utils/cli/main.py` or create new module
2. Use Typer decorators for command definition
3. Add help text, examples, and type hints
4. Write tests for the command
5. Update documentation in `docs/cli.rst`

### Adding a New Utility Function

1. Choose appropriate module (`time.py`, `utils.py`, etc.)
2. Implement function with type hints
3. Write comprehensive docstring
4. Add unit tests
5. Consider if it should be public API
6. Update module documentation if needed

### Adding Image Processing Features

1. Implement in `src/panoptes/utils/images/`
2. Handle optional dependencies gracefully
3. Test with sample images
4. Validate FITS headers and metadata
5. Update CLI if user-facing

### Creating a Release

**This process should be followed to create a new release of panoptes-utils.**

**Prerequisites:**
- Ensure you have write access to the repository
- Ensure all CI tests are passing on `develop` branch
- Determine the new version number (see Version Numbering below)

**Version Numbering:**
- Use semantic versioning: `vX.Y.Z`
- Get the current version: `git describe --tags --abbrev=0`
- Increment appropriately:
  - **X (Major):** Breaking changes
  - **Y (Minor):** New features, backward compatible
  - **Z (Patch):** Bug fixes, backward compatible

**Release Process:**

1. **Ensure `develop` is clean:**
   ```bash
   git checkout develop
   git pull origin develop
   git status  # Should show "nothing to commit, working tree clean"
   ```

2. **Determine version number:**
   ```bash
   # Get current version
   CURRENT_VERSION=$(git describe --tags --abbrev=0)
   echo "Current version: $CURRENT_VERSION"
   
   # Set new version (example: v0.8.10 -> v0.8.11)
   NEW_VERSION="v0.8.11"  # Update as appropriate
   echo "New version: $NEW_VERSION"
   ```

3. **Create release branch:**
   ```bash
   git checkout -b release-${NEW_VERSION} origin/develop
   ```

4. **Update `CHANGELOG.md`:**
   - Add release header with version and date: `## X.Y.Z - YYYY-MM-DD`
   - Ensure all changes are documented under appropriate sections (Added, Changed, Fixed, Removed)
   - Move any "Unreleased" changes under the new version
   - Verify all PR numbers are referenced
   - Example:
     ```markdown
     ## 0.8.11 - 2026-02-13
     
     ### Added
     - New feature description. #123
     
     ### Fixed
     - Bug fix description. #124
     ```

5. **Commit changelog updates:**
   ```bash
   git add CHANGELOG.md
   git commit -m "Update CHANGELOG for ${NEW_VERSION}"
   ```

6. **Merge release branch into `main`:**
   ```bash
   git checkout main
   git pull origin main
   git merge --no-ff release-${NEW_VERSION} -m "Merge release-${NEW_VERSION}"
   ```

7. **Resolve conflicts if necessary:**
   - If conflicts occur, resolve them carefully
   - Ensure `CHANGELOG.md` and `pyproject.toml` are correct
   - Commit resolved conflicts:
     ```bash
     git add .
     git commit -m "Resolve merge conflicts for ${NEW_VERSION}"
     ```

8. **Test and build on `main`:**
   ```bash
   # Ensure environment is up to date
   uv sync --all-extras --group dev
   
   # Run all tests (allow 5-10 minutes)
   uv run pytest
   
   # Check code style
   uv run ruff check .
   uv run ruff format --check .
   
   # Build the package
   uv build
   ```

9. **Verify distribution files:**
   ```bash
   # Check the built distribution files
   uv run --with twine twine check dist/*
   
   # Should show: "Checking dist/panoptes_utils-X.Y.Z.tar.gz: PASSED"
   # and "Checking dist/panoptes_utils-X.Y.Z-py3-none-any.whl: PASSED"
   ```

10. **Tag `main` with new version:**
    ```bash
    git tag -a ${NEW_VERSION} -m "Release ${NEW_VERSION}"
    ```

11. **Push `main` and tags to origin:**
    ```bash
    git push origin main
    git push origin ${NEW_VERSION}
    ```

12. **Merge release branch into `develop`:**
    ```bash
    git checkout develop
    git pull origin develop
    git merge --no-ff release-${NEW_VERSION} -m "Merge release-${NEW_VERSION} into develop"
    ```

13. **Tag `develop` with next development version:**
    ```bash
    # Set next development version (example: v0.2.50 -> v0.2.51.dev0)
    NEXT_DEV_VERSION="v0.2.51.dev0"
    git tag -a ${NEXT_DEV_VERSION} -m "Start development for ${NEXT_DEV_VERSION}"
    ```

14. **Push `develop` and tags to origin:**
    ```bash
    git push origin develop
    git push origin ${NEXT_DEV_VERSION}
    ```

15. **Clean up release branch:**
    ```bash
    git branch -d release-${NEW_VERSION}
    ```

**Post-Release:**
- Verify the new tag appears on GitHub releases page
- Monitor CI/CD for any issues
- Confirm the GitHub Actions workflow (`.github/workflows/create-release.yml`) has successfully built and published the release to PyPI (triggered on tag push)
- Announce release on forum/communications channels

**Common Issues:**
- **Merge conflicts:** Most common in `CHANGELOG.md`. Keep both sets of changes and organize chronologically.
- **Test failures:** Fix on the release branch before merging to `main`.
- **Twine check failures:** Usually due to missing or malformed metadata in `pyproject.toml`.

**Automation Notes for AI Agents:**
- Parse version from `git describe --tags --abbrev=0`
- Calculate next version based on changelog entries or commit messages
- Extract date automatically: `date +%Y-%m-%d`
- Validate version format matches `vX.Y.Z` pattern
- Ensure CHANGELOG has proper section headers before merging
- Verify all tests pass before tagging

## Error Handling

**Best Practices:**
- Use specific exception types from `panoptes.utils.error`
- Provide informative error messages
- Log errors appropriately (use `loguru`)
- Clean up resources in error cases
- Consider graceful degradation for optional features
- Don't silently catch exceptions

## Logging

**The project uses `loguru` for logging:**

```python
from loguru import logger

logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug details")
```

**Guidelines:**
- Import `logger` from `loguru`
- Log important operations and state changes
- Include context in log messages
- Use appropriate log levels
- Don't log sensitive information
- Consider log volume (avoid spam)

## Testing Strategy

### Test Organization

```
tests/
├── test_*.py              # Main test files
├── conftest.py            # Pytest configuration and fixtures
├── testing.yaml           # Test configuration
├── config/                # Config module tests
├── images/                # Image processing tests
│   └── data/              # Sample images for testing
└── data/                  # Test data files
```

### Writing Tests

**Good test characteristics:**
- Isolated (don't depend on other tests)
- Repeatable (same result every time)
- Fast (use mocks for slow operations)
- Clear (obvious what's being tested)
- Comprehensive (test edge cases)

**Use fixtures:**
```python
def test_config_client(config_host, config_port):
    """Test config client connection."""
    # Use fixtures from conftest.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_time.py

# Run specific test
uv run pytest tests/test_time.py::test_countdown_timer

# Run with markers
uv run pytest -m "not plate_solve"

# Run with coverage (default)
uv run pytest
```

## Documentation

### Docstring Format (Google Style)

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief one-line description.
    
    Longer description if needed. Explain what the function does,
    why it exists, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When this happens
        RuntimeError: When that happens
        
    Examples:
        >>> function_name("test", 42)
        True
    """
```

### Documentation Updates

When making changes, update:
- **`CHANGELOG.md`** for all PRs (required)
- Inline code comments for complex logic
- Docstrings for API changes
- Sphinx docs in `docs/` for major features
- README for installation/usage changes
- Examples for new features

## Security Considerations

- Validate external input (file paths, coordinates, etc.)
- Handle credentials securely (never commit secrets)
- Sanitize user-provided configuration
- Validate file operations (path traversal)
- Consider dependency vulnerabilities
- Sanitize shell commands if used

## Performance Considerations

- Utilities may be called frequently by POCS
- Avoid blocking operations where possible
- Use appropriate timeout values
- Consider memory usage for image processing
- Optimize hot paths
- Cache expensive computations when appropriate

## Common Pitfalls

1. **System Dependencies:** Not all systems have astrometry.net, dcraw installed
2. **Config Server Availability:** Code should handle missing config server gracefully
3. **Optional Dependencies:** Features using optional deps should fail gracefully
4. **File Paths:** Use `pathlib.Path`, handle both absolute and relative paths
5. **Time Zones:** Use UTC for all astronomical calculations
6. **Astropy Units:** Use units consistently (especially angles)
7. **Thread Safety:** Consider concurrent access to shared resources

## Astronomy Domain Knowledge

**Key concepts to understand:**
- **Alt/Az vs. RA/Dec:** Different coordinate systems
- **Sidereal Time:** Astronomical time standard
- **Field of View:** Area of sky visible to camera
- **Plate Solving:** Determining image coordinates from stars
- **FITS Format:** Flexible Image Transport System for astronomical images
- **WCS:** World Coordinate System for image coordinates

**Useful libraries:**
- `astropy`: Astronomical calculations, units, and FITS handling
- `astroplan`: Observation planning utilities
- `photutils`: Photometry and image analysis
- `sep`: Source extraction and photometry

## Getting Help

- **Documentation:** https://panoptes-utils.readthedocs.io
- **POCS Documentation:** https://pocs.readthedocs.io
- **Forum:** https://forum.projectpanoptes.org
- **Issues:** https://github.com/panoptes/panoptes-utils/issues
- **Code of Conduct:** `CODE_OF_CONDUCT.md`

## AI Agent-Specific Tips

### Context Gathering

1. **Start broad, then narrow:**
   - Read README and module documentation first
   - Understand component relationships
   - Then dive into specific files

2. **Search effectively:**
   - Use semantic search for concepts
   - Use grep for specific strings/patterns
   - Check test files for usage examples

3. **Understand before changing:**
   - Read the full function/class
   - Check call sites to understand usage
   - Review related tests

### Making Changes

1. **Validate assumptions:**
   - Check current behavior with tests
   - Verify understanding of requirements
   - Consider edge cases

2. **Incremental approach:**
   - Make small, testable changes
   - Run tests frequently
   - Fix errors as they appear

3. **Preserve intent:**
   - Maintain existing patterns
   - Don't over-engineer solutions
   - Keep changes focused

### Communication

1. **Be specific:**
   - Reference exact file paths
   - Quote relevant code sections
   - Explain reasoning for changes

2. **Show your work:**
   - Explain what you searched for
   - Describe what you found
   - Outline your approach

3. **Ask when uncertain:**
   - Clarify requirements if ambiguous
   - Confirm understanding of domain concepts
   - Request feedback on approach

## Quick Reference

### Common Commands

```bash
# Create development environment
uv sync --all-extras --group dev

# Install optional extras
uv sync --extra config --extra images

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_utils.py

# Check code style
uv run ruff check .

# Format code
uv run ruff format .

# Check formatting
uv run ruff format --check .

# Build package
uv build

# Start config server
panoptes-config-server run --config-file tests/testing.yaml

# View CLI help
panoptes-utils --help
panoptes-utils image --help
```

### File Locations

- Time utilities: `src/panoptes/utils/time.py`
- Config server: `src/panoptes/utils/config/server.py`
- Config client: `src/panoptes/utils/config/client.py`
- CLI: `src/panoptes/utils/cli/main.py`
- Image processing: `src/panoptes/utils/images/`
- Tests: `tests/`
- Test config: `tests/testing.yaml`

### Important Conventions

- Use `logger` from `loguru` for logging
- Use `pathlib.Path` for file paths
- Use `astropy.units` for physical quantities
- Use type hints on all functions
- Write tests for all new code
- Update documentation for API changes

---

**Remember:** PANOPTES Utilities is a foundational library used by POCS and other PANOPTES projects. Changes here can affect multiple downstream projects, so maintain backward compatibility and thorough testing.
