import pytest
import requests

from astropy import units as u

from panoptes.utils import serializers
from panoptes.utils.config.client import get_config
from panoptes.utils.config.client import set_config


def test_config_client():
    assert isinstance(get_config(), dict)

    assert set_config('location.horizon', 47 * u.degree) == {'location.horizon': 47 * u.degree}

    # With parsing
    assert get_config('location.horizon') == 47 * u.degree

    # Without parsing
    assert get_config('location.horizon', parse=False) == '47.0 deg'


def test_config_client_bad(caplog):
    # Bad host will return `None` but also throw error
    assert set_config('foo', 42, host='foobaz') is None
    assert caplog.records[-1].levelname == "WARNING"
    assert caplog.records[-1].message.startswith("Problem with set_config")

    # Bad host will return `None` but also throw error
    assert get_config('foo', host='foobaz') is None
    assert caplog.records[-1].levelname == "WARNING"
    assert caplog.records[-1].message.startswith("Problem with get_config")


def test_config_reset():
    # Check we are at value from above.
    assert get_config('location.horizon') == 47 * u.degree

    # Set to new value.
    set_config_return = set_config('location.horizon', 3 * u.degree)
    assert set_config_return == {'location.horizon': 3 * u.degree}

    # Check we have changed.
    assert get_config('location.horizon') == 3 * u.degree

    # Reset config
    config_host = 'localhost'
    config_port = 6563
    url = f'http://{config_host}:{config_port}/reset-config'
    response = requests.post(url,
                             data=serializers.to_json({'reset': True}),
                             headers={'Content-Type': 'application/json'}
                             )
    assert response.ok

    # Check we are at default again.
    assert get_config('location.horizon') == 30 * u.degree
