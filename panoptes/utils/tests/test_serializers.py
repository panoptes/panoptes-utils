import pytest

from astropy import units as u

from panoptes.utils import current_time
from panoptes.utils import serializers


@pytest.fixture(scope='function')
def obj():
    return {
        "name": "Generic PANOPTES Unit",
        "pan_id": "PAN000",
        "location": {
            "name": "Mauna Loa Observatory",
            "latitude": 19.54 * u.degree,       # Astropy unit
            "longitude": "-155.58 deg",         # String unit
            "elevation": "3400.0 m",
            "horizon": 30 * u.degree,
            "flat_horizon": -6 * u.degree,
            "focus_horizon": -12 * u.degree,
            "observe_horizon": -18 * u.degree,
            "timezone": "US/Hawaii",
            "gmt_offset": -600,
        },
        "directories": {
            "base": "/var/panoptes",
            "images": "images",
            "data": "data",
            "resources": "POCS/resources/",
            "targets": "POCS/resources/targets",
            "mounts": "POCS/resources/mounts",
        },
        "db": {
            "name": "panoptes",
            "type": "file"
        },
        "empty": {},
        "current_time": current_time(),
        "bool": True,

    }


def test_roundtrip_json(obj):
    config_str = serializers.to_json(obj)
    config = serializers.from_json(config_str)
    assert config['name'] == obj['name']
    assert config['location']['latitude'] == obj['location']['latitude']


def test_roundtrip_yaml(obj):
    config_str = serializers.to_yaml(obj)
    config = serializers.from_yaml(config_str)
    assert config['name'] == obj['name']
    assert config['location']['latitude'] == obj['location']['latitude']
