import os
import copy
import pytest
import time
import shutil
import tempfile

import logging
from _pytest.logging import caplog as _caplog
from contextlib import suppress

from panoptes.utils.logging import logger
from panoptes.utils.database import PanDB
from panoptes.utils.config.client import get_config
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

startup_message = ' STARTING NEW PYTEST RUN '
logger.add(log_file_path,
           enqueue=True,  # multiprocessing
           format=log_fmt,
           colorize=True,
           backtrace=True,
           diagnose=True,
           catch=True,
           # Start new log file for each testing run.
           rotation=lambda msg, _: startup_message in msg,
           level='TRACE')
logger.log('testing', '*' * 25 + startup_message + '*' * 25)


def pytest_addoption(parser):
    db_names = ",".join(_all_databases) + ' (or all for all databases)'
    group = parser.getgroup("PANOPTES pytest options")
    group.addoption(
        "--astrometry",
        action="store_true",
        default=False,
        help="If tests that require solving should be run")
    group.addoption(
        "--theskyx",
        action="store_true",
        default=False,
        help="If running tests alongside a running TheSkyX program.")
    group.addoption(
        "--test-databases",
        nargs="+",
        default=['file'],
        help=("Test databases in the list. List items can include: " + db_names +
              ". Note that travis-ci will test all of them by default."))


@pytest.fixture(scope='session')
def db_name():
    return 'panoptes_testing'


@pytest.fixture(scope='session')
def images_dir(tmpdir_factory):
    directory = tmpdir_factory.mktemp('images')
    return str(directory)


@pytest.fixture(scope='session')
def config_path():
    return os.path.expandvars('${PANDIR}/panoptes-utils/tests/panoptes_utils_testing.yaml')


@pytest.fixture(scope='session', autouse=True)
def static_config_server(config_path, images_dir, db_name):
    logger.log('testing', f'Starting static_config_server for testing session')

    proc = config_server(
        config_file=config_path,
        ignore_local=True,
        auto_save=False
    )

    logger.log('testing', f'static_config_server started with {proc.pid=}')

    # Give server time to start
    while get_config('name') is None:  # pragma: no cover
        logger.log('testing', f'Waiting for static_config_server {proc.pid=}, sleeping 1 second.')
        time.sleep(1)

    logger.log('testing', f'Startup config_server name=[{get_config("name")}]')

    # Adjust various config items for testing
    unit_id = 'PAN000'
    logger.log('testing', f'Setting testing name and unit_id to {unit_id}')
    set_config('pan_id', unit_id)

    logger.log('testing', f'Setting testing database to {db_name}')
    set_config('db.name', db_name)

    fields_file = 'simulator.yaml'
    logger.log('testing', f'Setting testing scheduler fields_file to {fields_file}')
    set_config('scheduler.fields_file', fields_file)

    logger.log('testing', f'Setting temporary image directory for testing')
    set_config('directories.images', images_dir)

    yield
    logger.log('testing', f'Killing static_config_server started with PID={proc.pid}')
    proc.terminate()


@pytest.fixture(scope='function', params=_all_databases)
def db_type(request):
    db_list = request.config.option.test_databases
    if request.param not in db_list and 'all' not in db_list:  # pragma: no cover
        pytest.skip(f"Skipping {request.param} DB, set --test-all-databases=True")

    PanDB.permanently_erase_database(
        request.param, 'panoptes_testing', really='Yes', dangerous='Totally')
    return request.param


@pytest.fixture(scope='function')
def db(db_type):
    return PanDB(db_type=db_type, db_name='panoptes_testing', connect=True)


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

    with tempfile.TemporaryDirectory() as tmpdirname:
        copy_file = shutil.copy2(cr2_path, tmpdirname)
        yield copy_file


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
