# This is in the root PANDIR directory so that pytest will recognize the
# options added below without having to also specify pocs/test, or a
# one of the tests in that directory, on the command line; i.e. pytest
# doesn't load pocs/tests/conftest.py until after it has searched for
# tests.
# In addition, there are fixtures defined here that are available to
# all tests, not just those in pocs/tests.

import os
import copy
import subprocess
import pytest
import time
import shutil
import tempfile

import logging
from _pytest.logging import caplog as _caplog
from contextlib import suppress

from panoptes.utils.logging import logger
from panoptes.utils.database import PanDB
from panoptes.utils.config.client import set_config
from panoptes.utils.config.server import config_server

# Doctest modules
import numpy as np
from matplotlib import pyplot as plt

_all_databases = ['file', 'memory']

logger.enable('panoptes')
logger.level("testing", no=15, icon="🤖", color="<YELLOW><black>")
log_file_path = os.path.join(
    os.getenv('PANLOG', '/var/panoptes/logs'),
    'panoptes-testing.log'
)
log_fmt = "<lvl>{level:.1s}</lvl> " \
          "<light-blue>{time:MM-DD HH:mm:ss.ss!UTC}</>" \
          "<blue>({time:HH:mm:ss.ss})</> " \
          "| <c>{name} {function}:{line}</c> | " \
          "<lvl>{message}</lvl>\n"
logger.add(log_file_path,
           enqueue=True,  # multiprocessing
           format=log_fmt,
           colorize=True,
           backtrace=True,
           diagnose=True,
           level='TRACE')


def pytest_addoption(parser):
    db_names = ",".join(_all_databases) + ' (or all for all databases)'
    group = parser.getgroup("PANOPTES pytest options")
    group.addoption(
        "--with-hardware",
        nargs='+',
        default=[],
        help=("A comma separated list of hardware to test."))
    group.addoption(
        "--without-hardware",
        nargs='+',
        default=[],
        help=("A comma separated list of hardware to NOT test. "))
    group.addoption(
        "--solve",
        action="store_true",
        default=False,
        help="If tests that require solving should be run")
    group.addoption(
        "--test-cloud-storage",
        action="store_true",
        default=False,
        dest="test_cloud_storage",
        help="Tests cloud storage functions." +
             "Requires $PANOPTES_CLOUD_KEY to be set to path of valid json service key")
    group.addoption(
        "--test-databases",
        nargs="+",
        default=['file'],
        help=("Test databases in the list. List items can include: " + db_names +
              ". Note that travis-ci will test all of them by default."))


@pytest.fixture(scope='session')
def config_host():
    return 'localhost'


@pytest.fixture(scope='session')
def static_config_port():
    """Used for the session-scoped config_server where no config values
    are expected to change during testing.
    """
    return '6563'


@pytest.fixture(scope='module')
def config_port():
    """Used for the function-scoped config_server when it is required to change
    config values during testing. See `dynamic_config_server` docs below.
    """
    return '4861'


@pytest.fixture(scope='session')
def db_name():
    return 'panoptes_testing'


@pytest.fixture(scope='session')
def images_dir(tmpdir_factory):
    directory = tmpdir_factory.mktemp('images')
    return str(directory)


@pytest.fixture(scope='session')
def config_path():
    return os.path.join(os.getenv('PANDIR'),
                        'panoptes-utils',
                        'tests',
                        'panoptes_utils_testing.yaml'
                        )


@pytest.fixture(scope='session', autouse=True)
def static_config_server(config_host, static_config_port, config_path, images_dir, db_name):
    print(f'Starting config_server for testing session')

    proc = config_server(
        host=config_host,
        port=static_config_port,
        config_file=config_path,
        ignore_local=True,
    )

    print(f'config_server started with PID={proc.pid}')

    # Give server time to start
    time.sleep(1)

    # Adjust various config items for testing
    unit_name = 'Generic PANOPTES Unit'
    unit_id = 'PAN000'
    print(f'Setting testing name and unit_id to {unit_id}')
    set_config('name', unit_name, port=static_config_port)
    set_config('pan_id', unit_id, port=static_config_port)

    print(f'Setting testing database to {db_name}')
    set_config('db.name', db_name, port=static_config_port)

    fields_file = 'simulator.yaml'
    print(f'Setting testing scheduler fields_file to {fields_file}')
    set_config('scheduler.fields_file', fields_file, port=static_config_port)

    # TODO(wtgee): determine if we need separate directories for each module.
    print(f'Setting temporary image directory for testing')
    set_config('directories.images', images_dir, port=static_config_port)

    yield
    print(f'Killing config_server started with PID={proc.pid}')
    proc.terminate()


@pytest.fixture(scope='function')
def dynamic_config_server(config_host, config_port, config_path, images_dir, db_name):
    """If a test requires changing the configuration we use a function-scoped testing
    server. We only do this on tests that require it so we are not constantly starting and stopping
    the config server unless necessary.  To use this, each test that requires it must use the
    `dynamic_config_server` and `config_port` fixtures and must pass the `config_port` to all
    instances that are created (propogated through PanBase).
    """

    print(f'Starting config_server for testing function')

    proc = config_server(
        host=config_host,
        port=config_port,
        config_file=config_path,
        ignore_local=True,
    )

    print(f'config_server started with PID={proc.pid}')

    # Give server time to start
    time.sleep(1)

    # Adjust various config items for testing
    unit_name = 'Generic PANOPTES Unit'
    unit_id = 'PAN000'
    print(f'Setting testing name and unit_id to {unit_id}')
    set_config('name', unit_name, port=config_port)
    set_config('pan_id', unit_id, port=config_port)

    print(f'Setting testing database to {db_name}')
    set_config('db.name', db_name, port=config_port)

    fields_file = 'simulator.yaml'
    print(f'Setting testing scheduler fields_file to {fields_file}')
    set_config('scheduler.fields_file', fields_file, port=config_port)

    # TODO(wtgee): determine if we need separate directories for each module.
    print(f'Setting temporary image directory for testing')
    set_config('directories.images', images_dir, port=config_port)

    yield
    print(f'Killing config_server started with PID={proc.pid}')
    proc.terminate()


@pytest.fixture
def temp_file():
    temp_file = 'temp'
    with open(temp_file, 'w') as f:
        f.write('')

    yield temp_file
    os.unlink(temp_file)


class FakeLogger:
    def __init__(self):
        self.messages = []
        pass

    def _add(self, name, *args):
        msg = [name]
        assert len(args) == 1
        assert isinstance(args[0], tuple)
        msg.append(args[0])
        self.messages.append(msg)

    def debug(self, *args):
        self._add('debug', args)

    def info(self, *args):
        self._add('info', args)

    def warning(self, *args):
        self._add('warning', args)

    def error(self, *args):
        self._add('error', args)

    def critical(self, *args):
        self._add('critical', args)


@pytest.fixture(scope='function')
def fake_logger():
    return FakeLogger()


@pytest.fixture(scope='function', params=_all_databases)
def db_type(request):
    db_list = request.config.option.test_databases
    if request.param not in db_list and 'all' not in db_list:
        pytest.skip("Skipping {} DB, set --test-all-databases=True".format(request.param))

    PanDB.permanently_erase_database(
        request.param, 'panoptes_testing', really='Yes', dangerous='Totally')
    return request.param


@pytest.fixture(scope='function')
def db(db_type):
    return PanDB(db_type=db_type, db_name='panoptes_testing', connect=True)


@pytest.fixture(scope='function')
def memory_db():
    PanDB.permanently_erase_database(
        'memory', 'panoptes_testing', really='Yes', dangerous='Totally')
    return PanDB(db_type='memory', db_name='panoptes_testing')


@pytest.fixture(scope='function')
def save_environ():
    old_env = copy.deepcopy(os.environ)
    yield
    os.environ = old_env


@pytest.fixture(scope='session')
def data_dir():
    return os.path.expandvars('/var/panoptes/panoptes-utils/tests/data')


@pytest.fixture(scope='function')
def unsolved_fits_file(data_dir):
    orig_file = os.path.join(data_dir, 'unsolved.fits')

    with tempfile.TemporaryDirectory() as tmpdirname:
        copy_file = shutil.copy2(orig_file, tmpdirname)
        yield copy_file


@pytest.fixture(scope='function')
def solved_fits_file(data_dir):
    orig_file = os.path.join(data_dir, 'solved.fits.fz')

    with tempfile.TemporaryDirectory() as tmpdirname:
        copy_file = shutil.copy2(orig_file, tmpdirname)
        yield copy_file


@pytest.fixture(scope='function')
def tiny_fits_file(data_dir):
    orig_file = os.path.join(data_dir, 'tiny.fits')

    with tempfile.TemporaryDirectory() as tmpdirname:
        copy_file = shutil.copy2(orig_file, tmpdirname)
        yield copy_file


@pytest.fixture(scope='function')
def noheader_fits_file(data_dir):
    orig_file = os.path.join(data_dir, 'noheader.fits')

    with tempfile.TemporaryDirectory() as tmpdirname:
        copy_file = shutil.copy2(orig_file, tmpdirname)
        yield copy_file


@pytest.fixture(scope='function')
def cr2_file(data_dir):
    cr2_path = os.path.join(data_dir, 'canon.cr2')

    if not os.path.exists(cr2_path):
        pytest.skip("No CR2 file found, skipping test.")

    return cr2_path


@pytest.fixture(autouse=True)
def add_doctest_dependencies(doctest_namespace):
    doctest_namespace['np'] = np
    doctest_namespace['plt'] = plt


@pytest.fixture
def caplog(_caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    logger.enable('panoptes')
    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    with suppress(ValueError):
        logger.remove(handler_id)
