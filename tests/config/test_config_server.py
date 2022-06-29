import pytest
import requests
from astropy import units as u

from panoptes.utils import serializers
from panoptes.utils.config.client import get_config
from panoptes.utils.config.client import set_config


@pytest.fixture(scope='module')
def config_host():
    return 'localhost'


@pytest.fixture(scope='module')
def config_port():
    return 8765


def test_config_client():
    assert isinstance(get_config(), dict)

    assert get_config('location.horizon') == 30 * u.degree
    assert set_config('location.horizon', 47 * u.degree) == {'location.horizon': 47 * u.degree}
    assert get_config('location.horizon') == 47 * u.degree

    # Without parsing the result contains the double-quotes since that's what the raw
    # response has.
    assert get_config('location.horizon', parse=False) == '"47.0 deg"'

    assert set_config('location.horizon', 42 * u.degree, parse=False) == {
        'location.horizon': '42.0 deg'}


def test_config_client_bad(caplog):
    # Bad host will return `None` but also throw error
    assert set_config('foo', 42, host='foobaz') is None
    assert caplog.records[-1].levelname == "WARNING"
    assert caplog.records[-1].message.startswith("Problem with set_config")

    # Bad host will return `None` but also throw error
    assert get_config('foo', host='foobaz') is None
    found_log = False
    for rec in caplog.records[-5:]:
        if rec.levelname == 'DEBUG' and rec.message.startswith('Bad connection to config-server'):
            found_log = True

    assert found_log


def test_config_reset(config_host, config_port):
    # Reset config via url
    url = f'http://{config_host}:{config_port}/reset-config'

    def reset_conf():
        response = requests.post(url,
                                 data=serializers.to_json({'reset': True}),
                                 headers={'Content-Type': 'application/json'}
                                 )
        assert response.ok

    reset_conf()

    # Check we are at default value.
    assert get_config('location.horizon') == 30 * u.degree

    # Set to new value.
    set_config_return = set_config('location.horizon', 3 * u.degree)
    assert set_config_return == {'location.horizon': 3 * u.degree}

    # Check we have changed.
    assert get_config('location.horizon') == 3 * u.degree

    reset_conf()

    # Check we are at default again.
    assert get_config('location.horizon') == 30 * u.degree
