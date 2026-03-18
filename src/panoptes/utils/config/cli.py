"""Config server CLI - moved to panoptes.utils.cli.config.

This module is retained for import-compatibility only.
Use ``panoptes-utils config`` instead.
"""

from panoptes.utils.cli.config import app as config_app

__all__ = ["config_app"]
