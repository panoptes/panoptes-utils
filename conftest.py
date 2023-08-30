import copy
import logging
import os
import shutil
import tempfile
from contextlib import suppress
from pathlib import Path

# Doctest modules
import numpy as np
import pytest
from _pytest.logging import caplog as _caplog  # noqa
from loguru import logger
from matplotlib import pyplot as plt

from panoptes.utils.config.server import config_server
from panoptes.utils.database import PanDB

_all_databases = ['file', 'memory']

logger.enable('panoptes')
logger.level("testing", no=15, icon="🤖", color="<YELLOW><black>")
log_fmt = "<lvl>{level:.1s}</lvl> " \
          "<light-blue>{time:MM-DD HH:mm:ss.ss!UTC}</>" \
          "<blue>({time:HH:mm:ss.ss})</> " \
          "| <c>{name} {function}:{line}</c> | " \
          "<lvl>{message}</lvl>"

# Put the log file in the tmp dir.
log_file_path = os.path.realpath('logs/panoptes-testing.log')
startup_message = f' STARTING NEW PYTEST RUN - LOGS: {log_file_path} '
logger.add(log_file_path,
           enqueue=True,  # multiprocessing
           format=log_fmt,
           colorize=True,
           # TODO decide on these options
           backtrace=True,
           diagnose=True,
           catch=True,
           # Start new log file for each testing run.
           rotation=lambda msg, _: startup_message in msg,
           level='TRACE')
logger.log('testing', '*' * 25 + startup_message + '*' * 25)


def pytest_configure(config):
    """Set up the testing."""
    logger.info('Setting up the config server.')
    config_file = 'tests/testing.yaml'

    host = 'localhost'
    port = '8765'

    os.environ['PANOPTES_CONFIG_HOST'] = host
    os.environ['PANOPTES_CONFIG_PORT'] = port

    config_server(config_file, host='localhost', port=8765, load_local=False, save_local=False)
    logger.success('Config server set up')

    config.addinivalue_line('markers', 'plate_solve: Tests that require astrometry.net')


def pytest_addoption(parser):
    db_names = ",".join(_all_databases) + ' (or all for all databases)'
    group = parser.getgroup("PANOPTES pytest options")
    group.addoption(
        "--test-solve",
        action="store_true",
        default=False,
        help="If tests that require solving should be run")
    group.addoption(
        "--test-databases",
        nargs="+",
        default=['file'],
        help=("Test databases in the list. List items can include: " + db_names +
              ". Note that travis-ci will test all of them by default."))


def pytest_collection_modifyitems(config, items):
    if config.getoption('--test-solve'):
        return
    skip_solve = pytest.mark.skip(reason='No plate solving requested')
    for item in items:
        if 'plate_solve' in item.keywords:
            item.add_marker(skip_solve)


@pytest.fixture(scope='session')
def config_path():
    return os.getenv('PANOPTES_CONFIG_FILE', 'tests/testing.yaml')


@pytest.fixture(scope='function', params=_all_databases)
def db_type(request):
    db_list = request.config.option.test_databases
    if request.param not in db_list and 'all' not in db_list:  # pragma: no cover
        pytest.skip(f"Skipping {request.param} DB, set --test-all-databases=True")

    PanDB.permanently_erase_database(request.param,
                                     'panoptes_testing',
                                     storage_dir='testing',
                                     really='Yes',
                                     dangerous='Totally')
    return request.param


@pytest.fixture(scope='function')
def db(db_type):
    return PanDB(db_type=db_type, db_name='panoptes_testing', storage_dir='testing', connect=True)


@pytest.fixture(scope='function')
def save_environ():
    old_env = copy.deepcopy(os.environ)
    yield
    os.environ = old_env


@pytest.fixture(scope='session')
def data_dir():
    return os.path.expandvars('tests/data')


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
    cr2_path = Path(data_dir) / 'canon.cr2'

    if cr2_path.exists() is False:
        pytest.skip("No CR2 file found, skipping test.")

    # The file is fetched in conftest.py but may be a 404-not found text message.
    # Try to read as text. If we fail it is because the file is a CR2 (i.e. bytes
    # and not text).
    try:
        _ = cr2_path.read_text()
        pytest.skip("CR2 file found but it is not a CR2 file, skipping test.")
    except UnicodeDecodeError:
        pass

    with tempfile.TemporaryDirectory() as tmpdirname:
        copy_file = shutil.copy2(cr2_path, tmpdirname)
        yield copy_file


@pytest.fixture(autouse=True)
def add_doctest_dependencies(doctest_namespace):
    doctest_namespace['np'] = np
    doctest_namespace['plt'] = plt


@pytest.fixture
def caplog(_caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    logger.enable('panoptes')
    handler_id = logger.add(PropagateHandler(), format="{message}")
    yield _caplog
    with suppress(ValueError):
        logger.remove(handler_id)
