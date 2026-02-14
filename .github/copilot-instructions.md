# PANOPTES Utilities

PANOPTES Utilities is a Python library providing astronomical utilities for the PANOPTES ecosystem. It includes CLI tools for image processing, a configuration server, and various utility modules for astronomical data processing.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Prerequisites and System Setup
- Ensure Python 3.12+ is available:
  ```bash
  python3 --version  # Must be 3.12+
  ```
- Install UV build system:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh  # Takes ~5 seconds
  # or
  pipx install uv  # Takes ~10 seconds
  ```
- Install required system dependencies:
  ```bash
  sudo apt-get update && sudo apt-get install --no-install-recommends --yes \
    libffi-dev libssl-dev \
    astrometry.net astrometry-data-tycho2 \
    dcraw exiftool libcfitsio-dev libcfitsio-bin \
    libfreetype6-dev libpng-dev libjpeg-dev libffi-dev fonts-freefont-ttf
  # Takes 5-8 minutes - NEVER CANCEL
  ```

### Environment Setup and Build
- Create development environment:
  ```bash
  uv sync --all-extras --group dev  # Takes 1-3 minutes. Set timeout to 5+ minutes.
  ```
  
- Install specific extras or groups as needed:
  ```bash
  uv sync --extra config --extra images --group testing  # Install specific features
  ```

- Build the package:
  ```bash
  uv build  # Takes 10-30 seconds. Set timeout to 2+ minutes.
  ```

### Testing
- Run all tests (with coverage):
  ```bash
  uv run pytest  # Takes 2-5 minutes - NEVER CANCEL. Set timeout to 10+ minutes.
  ```
  
- Run specific test file:
  ```bash
  uv run pytest tests/test_utils.py  # Takes 10-30 seconds
  ```
- Run specific test:
  ```bash
  uv run pytest tests/test_time.py::test_countdown_timer  # Takes 5-10 seconds
  ```

### Linting and Formatting
- Run linting (Ruff):
  ```bash
  uv run ruff check .  # Takes 5-15 seconds
  ```
  
- Fix linting issues automatically:
  ```bash
  uv run ruff check --fix .  # Takes 5-15 seconds
  ```
- Format code:
  ```bash
  uv run ruff format .  # Takes 5-15 seconds
  ```
- Check formatting without changes:
  ```bash
  uv run ruff format --check .  # Takes 5-15 seconds
  ```

### CLI Tools
- Main CLI help:
  ```bash
  uv run panoptes-utils --help
  ```
- Image processing CLI:
  ```bash
  uv run panoptes-utils image --help
  ```
- Config server:
  ```bash
  uv run panoptes-config-server run --config-file tests/testing.yaml
  ```

## Validation
- **CRITICAL**: Always run `uv run ruff check .` and `uv run ruff format --check .` before committing changes or the CI (.github/workflows/pythontest.yaml) will fail.
- Always run at least one test to ensure changes don't break functionality:
  ```bash
  uv run pytest tests/test_utils.py
  ```
- **Manual Testing Scenarios**: After making changes to CLI tools, validate by running:
  ```bash
  uv run panoptes-utils --help  # Should show help without errors
  uv run panoptes-config-server --help  # Should show config server help
  ```

## Project Structure and Navigation

### Key Directories
- `src/panoptes/utils/` - Main source code
- `src/panoptes/utils/cli/` - Command-line interface code
- `src/panoptes/utils/config/` - Configuration server code
- `src/panoptes/utils/images/` - Image processing utilities
- `tests/` - Test suite
- `examples/` - Example notebooks and scripts
- `docs/` - Documentation

### Important Files
- `pyproject.toml` - Project configuration, dependencies, and build settings
- `conftest.py` - Pytest configuration and fixtures
- `tests/testing.yaml` - Test configuration file
- `.github/workflows/pythontest.yaml` - CI/CD pipeline

### Key Modules
- `time.py` - Time utilities including CountdownTimer and wait_for_events
- `config/` - Configuration management and server
- `cli/` - Command-line interfaces
- `images/` - Image processing and astronomy utilities
- `serializers.py` - Data serialization utilities

## Common Commands Reference

### Repository Root Listing
```bash
ls -la
```
Output includes:
- `.github/` - GitHub Actions and configuration
- `src/panoptes/` - Source code
- `tests/` - Test suite
- `pyproject.toml` - Project configuration
- `README.md` - Project documentation
- `conftest.py` - Test configuration

### Development Workflow
1. Check code style: `uv run ruff check .`
2. Format code: `uv run ruff format .`
3. Run tests: `uv run pytest`
4. Build package: `uv build`

### Environment Variables
- `PANOPTES_CONFIG_HOST` - Config server host (default: localhost)
- `PANOPTES_CONFIG_PORT` - Config server port (default: 8765)
- `PANOPTES_CONFIG_FILE` - Config file path (default: tests/testing.yaml)

## Known Issues and Limitations
- **System Dependencies**: Some astrometry.net data packages may not be available on all systems
- **Port Conflicts**: Config server uses port 8765 - ensure no other services are running on this port

## Troubleshooting
- **Config Server Errors**: If tests fail with config server errors, ensure no other services are running on port 8765
- **Image Processing Test Failures**: Verify system dependencies (astrometry.net, dcraw, exiftool) are installed
  
- **Config Server Errors**: If tests fail with config server errors, ensure no other services are running on port 8765
- **Image Processing Test Failures**: Verify system dependencies (astrometry.net, dcraw, exiftool) are installed

## Timing Expectations
- **NEVER CANCEL**: All build and test commands should be allowed to complete
- Environment creation: 2-5 minutes (can fail due to network issues)
- Full test suite: 2-5 minutes
- Build process: 30-60 seconds
- System dependency installation: 5-8 minutes
- Linting/formatting: 5-15 seconds each