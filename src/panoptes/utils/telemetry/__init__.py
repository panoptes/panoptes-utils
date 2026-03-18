"""Telemetry utilities for PANOPTES."""

from importlib import import_module
from typing import Any

__all__: list[str] = [
    "TelemetryClient",
    "TelemetryClientError",
    "TelemetryService",
    "create_app",
    "get_site_day_key",
    "telemetry_server",
    "utc_iso_z",
]

_CLIENT_ATTRS = {
    "TelemetryClient",
    "TelemetryClientError",
}

_SERVER_ATTRS = {
    "TelemetryService",
    "create_app",
    "get_site_day_key",
    "telemetry_server",
    "utc_iso_z",
}


def __getattr__(name: str) -> Any:
    """Lazily import telemetry client and server components on first access.

    This avoids importing optional telemetry dependencies (e.g. FastAPI/uvicorn)
    unless the corresponding symbols are actually used. If the underlying
    module cannot be imported, a clearer ImportError is raised suggesting
    installation of the telemetry extras.
    """
    if name in _CLIENT_ATTRS:
        try:
            module = import_module("panoptes.utils.telemetry.client")
        except ImportError as exc:
            msg = (
                "Telemetry client is not available because optional dependencies are missing. "
                'Install them with: pip install "panoptes-utils[telemetry]".'
            )
            raise ImportError(msg) from exc
        return getattr(module, name)

    if name in _SERVER_ATTRS:
        try:
            module = import_module("panoptes.utils.telemetry.server")
        except ImportError as exc:
            msg = (
                "Telemetry server is not available because optional dependencies are missing. "
                'Install them with: pip install "panoptes-utils[telemetry]".'
            )
            raise ImportError(msg) from exc
        return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return the list of available attributes for this module."""
    # Combine the default module attributes with our public API.
    return sorted(set(globals().keys()) | set(__all__))
