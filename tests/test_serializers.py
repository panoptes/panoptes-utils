import pytest
from astropy import units as u
from panoptes.utils import error
from panoptes.utils import serializers
from panoptes.utils.time import current_time


@pytest.fixture(scope='function')
def obj():
    return {
        "name": "Testing PANOPTES Unit",
        "pan_id": "PAN000",
        "location": {
            "name": "Mauna Loa Observatory",
            "latitude": 19.54 * u.degree,  # Astropy unit
            "longitude": "-155.58 deg",  # String unit
            "elevation": "3400.0 m",
            "horizon": 30 * u.degree,
            "flat_horizon": -6 * u.degree,
            "focus_horizon": -12 * u.degree,
            "observe_horizon": -18 * u.degree,
            "timezone": "US/Hawaii",
            "gmt_offset": -600,
        },
        "directories": {
            "base": "/panoptes-pocs",
            "images": "images",
            "data": "data",
            "resources": "resources/",
            "targets": "resources/targets",
            "mounts": "resources/mounts",
        },
        "db": {
            "name": "panoptes",
            "type": "file"
        },
        "empty": {},
        "current_time": current_time(),
        "bool": True,
        "exception": TypeError,
        "panoptes_exception": error.InvalidObservation
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


def test_bad_deserialization():
    with pytest.raises(error.InvalidDeserialization):
        serializers.from_json('foobar')


def test_bad_serialization():
    with pytest.raises(error.InvalidSerialization):
        serializers.to_json(pytest)


def test_quantity():
    json_str = serializers.to_json(dict(foo='42 deg', bar='foo deg'))
    assert json_str == '{"foo": "42 deg", "bar": "foo deg"}'
    json_obj = serializers.from_json(json_str)

    # Make sure we made a quantity when we could.
    assert json_obj['foo'] == 42 * u.deg
    # And not when we can't.
    assert json_obj['bar'] == 'foo deg'
