import pytest
import requests

from astropy import units as u

from panoptes.utils import serializers
from panoptes.utils.config.client import get_config
from panoptes.utils.config.client import set_config


def test_config_client(dynamic_config_server, config_port):
    assert isinstance(get_config(port=config_port), dict)

    assert set_config('location.horizon', 47 * u.degree,
                      port=config_port) == {'location.horizon': 47 * u.degree}

    # With parsing
    assert get_config('location.horizon', port=config_port) == 47 * u.degree

    # Without parsing
    assert get_config('location.horizon', port=config_port, parse=False) == '47.0 deg'


def test_config_client_bad(dynamic_config_server, config_port, caplog):
    # Bad host will return `None` but also throw error
    assert set_config('foo', 42, host='foobaz') is None
    assert caplog.records[-1].levelname == "INFO"
    assert caplog.records[-1].message.startswith("Problem with set_config")

    # Bad host will return `None` but also throw error
    assert get_config('foo', host='foobaz') is None
    assert caplog.records[-1].levelname == "INFO"
    assert caplog.records[-1].message.startswith("Problem with get_config")


def test_config_reset(dynamic_config_server, config_port, config_host):
    # Check we are at default.
    assert get_config('location.horizon', port=config_port) == 30 * u.degree

    # Set to new value.
    set_config_return = set_config('location.horizon', 47 * u.degree, port=config_port)
    assert set_config_return == {'location.horizon': 47 * u.degree}

    # Check we have changed.
    assert get_config('location.horizon', port=config_port) == 47 * u.degree

    # Reset config
    url = f'http://{config_host}:{config_port}/reset-config'
    response = requests.post(url,
                             data=serializers.to_json({'reset': True}),
                             headers={'Content-Type': 'application/json'}
                             )
    assert response.ok

    # Check we are at default again.
    assert get_config('location.horizon', port=config_port) == 30 * u.degree
