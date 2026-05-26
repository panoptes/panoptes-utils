"""Pydantic models for PANOPTES configuration.

These models represent the configuration sections that are shared across
all PANOPTES components. Hardware-specific sections (mount, cameras, etc.)
are defined in POCS.

Usage::

    from panoptes.utils.config.helpers import load_config
    from panoptes.utils.config.models import PANOPTESBaseConfig

    config = load_config('path/to/config.yaml', model=PANOPTESBaseConfig)
    print(config.location.latitude)   # <Quantity 19.54 deg>
    print(config.name)                # 'My PANOPTES Unit'
"""

from typing import Any

from astropy import units as u
from astropy.units import Quantity
from pydantic import BaseModel, ConfigDict, field_validator


def _parse_quantity(value: Any) -> Quantity:
    """Convert a string or pass-through a Quantity."""
    if isinstance(value, Quantity):
        return value
    if isinstance(value, str):
        return u.Quantity(value)
    raise ValueError(f"Cannot parse {value!r} as an astropy Quantity")


class LocationConfig(BaseModel):
    """Geographic location of the observatory.

    All angle and distance fields accept either an already-parsed
    ``astropy.units.Quantity`` (as returned by ``load_config``) or a
    plain string in the form ``"<value> <unit>"`` (e.g. ``"19.54 deg"``).

    Examples:
        >>> from astropy import units as u
        >>> loc = LocationConfig(
        ...     latitude="19.54 deg",
        ...     longitude="-155.58 deg",
        ...     elevation="3400.0 m",
        ...     timezone="US/Hawaii",
        ... )
        >>> loc.latitude
        <Quantity 19.54 deg>
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    latitude: Quantity
    longitude: Quantity
    elevation: Quantity
    horizon: Quantity = 30 * u.deg
    flat_horizon: Quantity = -6 * u.deg
    focus_horizon: Quantity = -12 * u.deg
    observe_horizon: Quantity = -18 * u.deg
    timezone: str = "UTC"
    gmt_offset: int = 0

    @field_validator(
        "latitude", "longitude", "horizon", "flat_horizon", "focus_horizon", "observe_horizon", mode="before"
    )
    @classmethod
    def parse_angle(cls, v: Any) -> Quantity:
        """Accept string or Quantity for angle fields."""
        return _parse_quantity(v)

    @field_validator("elevation", mode="before")
    @classmethod
    def parse_distance(cls, v: Any) -> Quantity:
        """Accept string or Quantity for distance fields."""
        return _parse_quantity(v)


class DirectoriesConfig(BaseModel):
    """Filesystem directories used by PANOPTES.

    The ``base`` directory is the root; all other relative paths are
    resolved against it by ``parse_config_directories``.

    Examples:
        >>> dirs = DirectoriesConfig(base="/home/panoptes")
        >>> dirs.images
        'images'
    """

    base: str = "."
    images: str = "images"
    data: str = "data"
    resources: str = "resources"
    targets: str = "resources/targets"
    mounts: str = "resources/mounts"

    @field_validator("base", mode="before")
    @classmethod
    def coerce_path(cls, v: Any) -> str:
        """Accept Path objects as well as strings."""
        return str(v)


class DatabaseConfig(BaseModel):
    """Configuration for the local database (PanDB / telemetry).

    Examples:
        >>> db = DatabaseConfig(name="panoptes", type="file")
        >>> db.type
        'file'
    """

    name: str = "panoptes"
    type: str = "file"


class PANOPTESBaseConfig(BaseModel):
    """Top-level configuration shared by all PANOPTES components.

    This model covers the sections defined in ``panoptes-utils``.
    Hardware-specific sections (``mount``, ``cameras``, etc.) are
    handled by ``POCSConfig`` in the POCS repository.

    Extra fields are allowed so that the full config dict (including
    POCS-specific keys) can be passed without error.

    Examples:
        >>> from panoptes.utils.config.helpers import load_config
        >>> from panoptes.utils.config.models import PANOPTESBaseConfig
        >>> cfg = load_config('tests/testing.yaml', model=PANOPTESBaseConfig)
        >>> cfg.pan_id
        'PAN000'
        >>> cfg.location.timezone
        'US/Hawaii'
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = ""
    pan_id: str = "PAN000"
    location: LocationConfig | None = None
    directories: DirectoriesConfig = DirectoriesConfig()
    db: DatabaseConfig = DatabaseConfig()

    @field_validator("location", mode="before")
    @classmethod
    def parse_location(cls, v: Any) -> LocationConfig | None:
        if v is None:
            return None
        if isinstance(v, LocationConfig):
            return v
        return LocationConfig(**v)

    @field_validator("directories", mode="before")
    @classmethod
    def parse_directories(cls, v: Any) -> DirectoriesConfig:
        if isinstance(v, DirectoriesConfig):
            return v
        return DirectoriesConfig(**v)

    @field_validator("db", mode="before")
    @classmethod
    def parse_db(cls, v: Any) -> DatabaseConfig:
        if isinstance(v, DatabaseConfig):
            return v
        return DatabaseConfig(**v)

    @property
    def earth_location(self):
        """Return an ``astropy.coordinates.EarthLocation`` for the site.

        Returns:
            astropy.coordinates.EarthLocation | None: The site location, or
                None if no location is configured.
        """
        if self.location is None:
            return None
        from astropy.coordinates import EarthLocation

        return EarthLocation(
            lat=self.location.latitude,
            lon=self.location.longitude,
            height=self.location.elevation,
        )
