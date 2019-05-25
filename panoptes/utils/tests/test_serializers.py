import pytest

from astropy import units as u

from panoptes_utils import serializers


@pytest.fixture(scope='function')
def obj():
    return {
        "name": "Generic PANOPTES Unit",
        "pan_id": "PAN000",
        "location": {
            "name": "Mauna Loa Observatory",
            "latitude": 19.54 * u.degree,
            "longitude": -155.58 * u.degree,
            "elevation": 3400.0,
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
        }
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
