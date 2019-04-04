import os
import time
import pytest
import subprocess

from astropy import units as u

from panoptes_utils.config.client import get_config
from panoptes_utils.config.client import set_config


@pytest.fixture(scope='module')
def host():
    return 'config-server'


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
    # Give the server a second to start
    time.sleep(1)
    yield proc
    proc.terminate()


def test_config_client(config_server, port):
    # If None then server is still running.
    assert config_server.poll() is None

    loc = get_config(key='location', port=port)
    assert loc['horizon'] == 30 * u.degree

    assert set_config('location.horizon', 47, port=port) == 47

    assert get_config('location.horizon', parse=False) == 47
