import os
import time
import pytest
import subprocess

from astropy import units as u

from panoptes_utils.config.client import get_config
from panoptes_utils.config.client import set_config


@pytest.fixture(scope='module')
def host():
    return 'localhost'


@pytest.fixture(scope='module')
def port():
    return '6563'


@pytest.fixture(scope='module')
def config_server(host, port):
    cmd = os.path.join(os.getenv('PANDIR'),
                       'panoptes-utils',
                       'scripts',
                       'run_config_server.py'
                       )
    args = [cmd, '--host', host, '--port', port]

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
