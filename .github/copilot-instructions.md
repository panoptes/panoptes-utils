# PANOPTES Utilities

PANOPTES Utilities is a Python library providing astronomical utilities for the PANOPTES ecosystem. It includes CLI tools for image processing, a configuration server, and various utility modules for astronomical data processing.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Prerequisites and System Setup
- Ensure Python 3.12+ is available:
  ```bash
  python3 --version  # Must be 3.12+
  ```
- Install Hatch build system:
  ```bash
  pipx install hatch  # Takes ~21 seconds
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
  hatch env create  # Takes 2-5 minutes - NEVER CANCEL. Set timeout to 10+ minutes.
  ```
  **KNOWN ISSUE**: Environment creation FAILS with PyPI timeout errors in GitHub Actions and similar restricted environments due to network connectivity limitations. This is a known limitation of the build system in environments with restricted internet access.

- Install optional extras (if environment creation succeeds):
  ```bash
  hatch run pip install -e ".[config,images,testing]"  # Takes 1-3 minutes - NEVER CANCEL
  ```
  **NOTE**: This command will also fail in environments with PyPI connectivity issues.

- Build the package:
  ```bash
  hatch build  # Takes 30-60 seconds - NEVER CANCEL. Set timeout to 5+ minutes.
  ```
  **NOTE**: Build will fail if dependencies cannot be downloaded from PyPI.

### Testing
- Run all tests (with coverage):
  ```bash
  hatch run pytest  # Takes 2-5 minutes - NEVER CANCEL. Set timeout to 10+ minutes.
  ```
  **NOTE**: Requires successful environment setup. Will fail in environments with PyPI connectivity issues.
  
- Run specific test file:
  ```bash
  hatch run pytest tests/test_utils.py  # Takes 10-30 seconds
  ```
- Run specific test:
  ```bash
  hatch run pytest tests/test_time.py::test_countdown_timer  # Takes 5-10 seconds
  ```

### Linting and Formatting
- Run linting (Ruff):
  ```bash
  hatch run lint  # Takes 5-15 seconds
  ```
  **NOTE**: Requires Ruff to be installed in the Hatch environment.
  
- Fix linting issues automatically:
  ```bash
  hatch run lint-fix  # Takes 5-15 seconds
  ```
- Format code:
  ```bash
  hatch run fmt  # Takes 5-15 seconds
  ```
- Check formatting without changes:
  ```bash
  hatch run fmt-check  # Takes 5-15 seconds
  ```

**WORKAROUND for network issues**: If Hatch commands fail due to network issues, install tools directly:
```bash
# Install ruff directly (may also fail in restricted environments)
pip install --user ruff
# Then run directly
ruff check .
ruff format .
```

### CLI Tools
- Main CLI help:
  ```bash
  hatch run panoptes-utils --help
  ```
- Image processing CLI:
  ```bash
  hatch run panoptes-utils image --help
  ```
- Config server:
  ```bash
  hatch run panoptes-config-server run --config-file tests/testing.yaml
  ```

## Validation
- **CRITICAL**: Always run `hatch run lint` and `hatch run fmt-check` before committing changes or the CI (.github/workflows/pythontest.yaml) will fail.
  **NOTE**: These commands may fail in environments with PyPI connectivity issues.
- **Alternative validation**: If Hatch commands fail, use direct tool commands (if tools can be installed):
  ```bash
  ruff check .  # Lint check
  ruff format --check .  # Format check
  ```
- Always run at least one test to ensure changes don't break functionality:
  ```bash
  hatch run pytest tests/test_utils.py  # Requires working environment
  ```
- **Manual Testing Scenarios**: After making changes to CLI tools, validate by running:
  ```bash
  hatch run panoptes-utils --help  # Should show help without errors
  hatch run panoptes-config-server --help  # Should show config server help
  ```
  **NOTE**: These require successful package installation.

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
1. Check code style: `hatch run lint`
2. Format code: `hatch run fmt`
3. Run tests: `hatch run pytest`
4. Build package: `hatch build`

### Environment Variables
- `PANOPTES_CONFIG_HOST` - Config server host (default: localhost)
- `PANOPTES_CONFIG_PORT` - Config server port (default: 8765)
- `PANOPTES_CONFIG_FILE` - Config file path (default: tests/testing.yaml)

## Known Issues and Limitations
- **CRITICAL LIMITATION**: PyPI connectivity issues prevent most development commands from working in GitHub Actions and restricted network environments:
  - `hatch env create` FAILS with timeout errors
  - `hatch run pytest` FAILS - cannot install dependencies  
  - `hatch run lint` FAILS - cannot install Ruff
  - `hatch build` FAILS - cannot download build dependencies
  - `pip install` commands FAIL with PyPI timeouts
- **Root Cause**: This appears to be a network connectivity issue where PyPI (pypi.org) is unreachable from the execution environment
- **Impact**: Most Hatch-based development workflows are unusable in CI/CD environments with restricted internet access
- **Workaround**: Development must be done in environments with full internet access to PyPI
- **System Dependencies**: Some astrometry.net data packages may not be available on all systems
- **Port Conflicts**: Config server uses port 8765 - ensure no other services are running on this port

## Troubleshooting
- **PRIMARY ISSUE - Network Connectivity**: If ANY Hatch or pip command fails with timeout errors:
  ```
  TimeoutError: The read operation timed out
  ReadTimeoutError: HTTPSConnectionPool(host='pypi.org', port=443): Read timed out
  ```
  This indicates PyPI is unreachable. Test with: `ping pypi.org`
  **Resolution**: Must work in environment with unrestricted internet access
  
- **Environment Creation Fails**: `hatch env create` fails due to network issues
  **Workaround**: Document this limitation and work in local development environment
  
- **Lint/Test Commands Fail**: All `hatch run` commands fail if environment creation failed
  **Resolution**: Fix network connectivity or work in pre-configured environment
  
- **Config Server Errors**: If tests fail with config server errors, ensure no other services are running on port 8765
- **Image Processing Test Failures**: Verify system dependencies (astrometry.net, dcraw, exiftool) are installed

## Timing Expectations
- **NEVER CANCEL**: All build and test commands should be allowed to complete
- Environment creation: 2-5 minutes (can fail due to network issues)
- Full test suite: 2-5 minutes
- Build process: 30-60 seconds
- System dependency installation: 5-8 minutes
- Linting/formatting: 5-15 seconds each