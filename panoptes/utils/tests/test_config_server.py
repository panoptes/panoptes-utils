import os
import time
import pytest
import subprocess
import requests

from astropy import units as u

from panoptes.utils import serializers
from panoptes.utils.config.client import get_config
from panoptes.utils.config.client import set_config


@pytest.fixture(scope='module')
def host():
    return 'localhost'


@pytest.fixture(scope='module')
def port():
    return '6563'


@pytest.fixture(scope='function')
def config_server(host, port):
    cmd = os.path.join(os.getenv('PANDIR'),
                       'panoptes-utils',
                       'scripts',
                       'run_config_server.py'
                       )
    args = [cmd, '--host', host, '--port', port, '--no-save', '--ignore-local']

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(1)
    yield proc
    proc.terminate()


def test_config_client(config_server, host, port):
    # If None then server is still running.
    assert config_server.poll() is None

    assert isinstance(get_config(host=host, port=port), dict)

    assert set_config('location.horizon', 47 * u.degree, host=host,
                      port=port) == {'location.horizon': 47 * u.degree}

    # With parsing
    assert get_config('location.horizon', host=host, port=port) == 47 * u.degree

    # Without parsing
    assert get_config('location.horizon', host=host, port=port, parse=False) == '47.0 deg'


def test_config_reset(config_server, host, port):
    # If None then server is still running.
    assert config_server.poll() is None

    # Check we are at default.
    assert get_config('location.horizon', host=host, port=port) == 30 * u.degree

    # Set to new value.
    set_config_return = set_config('location.horizon', 47 * u.degree, host=host, port=port)
    assert set_config_return == {'location.horizon': 47 * u.degree}

    # Check we have changed.
    assert get_config('location.horizon', host=host, port=port) == 47 * u.degree

    # Reset config
    url = f'http://{host}:{port}/reset-config'
    response = requests.post(url,
                             data=serializers.to_json({'reset': True}),
                             headers={'Content-Type': 'application/json'}
                             )
    assert response.ok

    # Check we are at default again.
    assert get_config('location.horizon', host=host, port=port) == 30 * u.degree
