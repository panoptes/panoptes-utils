# This is in the root PANDIR directory so that pytest will recognize the
# options added below without having to also specify pocs/test, or a
# one of the tests in that directory, on the command line; i.e. pytest
# doesn't load pocs/tests/conftest.py until after it has searched for
# tests.
# In addition, there are fixtures defined here that are available to
# all tests, not just those in pocs/tests.

import copy
import os
import pytest
import subprocess
import time
import shutil

from panoptes.utils.database import PanDB
from panoptes.utils.logger import get_root_logger
from panoptes.utils.messaging import PanMessaging
from panoptes.utils.config.client import set_config
from panoptes.utils.config.server import config_server

_all_databases = ['file', 'memory']


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
        help="Tests cloud strorage functions." +
        "Requires $PANOPTES_CLOUD_KEY to be set to path of valid json service key")
    group.addoption(
        "--test-databases",
        nargs="+",
        default=['file'],
        help=("Test databases in the list. List items can include: " + db_names +
              ". Note that travis-ci will test all of them by default."))


def pytest_runtest_logstart(nodeid, location):
    """Signal the start of running a single test item.

    This hook will be called before pytest_runtest_setup(),
    pytest_runtest_call() and pytest_runtest_teardown() hooks.

    Args:
        nodeid (str) – full id of the item
        location – a triple of (filename, linenum, testname)
    """
    try:
        logger = get_root_logger()
        logger.critical('')
        logger.critical('##########' * 8)
        logger.critical('     START TEST {}', nodeid)
    except Exception:
        pass


def pytest_runtest_logfinish(nodeid, location):
    """Signal the complete finish of running a single test item.

    This hook will be called after pytest_runtest_setup(),
    pytest_runtest_call() and pytest_runtest_teardown() hooks.

    Args:
        nodeid (str) – full id of the item
        location – a triple of (filename, linenum, testname)
    """
    try:
        logger = get_root_logger()
        logger.critical('')
        logger.critical('       END TEST {}', nodeid)
        logger.critical('##########' * 8)
    except Exception:
        pass


def pytest_runtest_logreport(report):
    """Adds the failure info that pytest prints to stdout into the log."""
    if report.skipped or report.outcome != 'failed':
        return
    try:
        logger = get_root_logger()
        logger.critical('')
        logger.critical('  TEST {} FAILED during {}\n\n{}\n', report.nodeid, report.when,
                        report.longreprtext)
        cnt = 15
        if report.capstdout:
            logger.critical('{}Captured stdout during {}{}\n{}\n', '= ' * cnt, report.when,
                            ' =' * cnt, report.capstdout)
        if report.capstderr:
            logger.critical('{}Captured stderr during {}{}\n{}\n', '* ' * cnt, report.when,
                            ' *' * cnt, report.capstderr)
    except Exception:
        pass


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
                        'panoptes',
                        'tests',
                        'panoptes_utils_testing.yaml'
                        )


@pytest.fixture(scope='session', autouse=True)
def static_config_server(config_host, static_config_port, config_path, images_dir, db_name):

    logger = get_root_logger()
    logger.critical(f'Starting config_server for testing session')

    proc = config_server(
        host=config_host,
        port=static_config_port,
        config_file=config_path,
        ignore_local=True,
    )

    logger.info(f'config_server started with PID={proc.pid}')

    # Give server time to start
    time.sleep(1)

    # Adjust various config items for testing
    unit_name = 'Generic PANOPTES Unit'
    unit_id = 'PAN000'
    logger.info(f'Setting testing name and unit_id to {unit_id}')
    set_config('name', unit_name, port=static_config_port)
    set_config('pan_id', unit_id, port=static_config_port)

    logger.info(f'Setting testing database to {db_name}')
    set_config('db.name', db_name, port=static_config_port)

    fields_file = 'simulator.yaml'
    logger.info(f'Setting testing scheduler fields_file to {fields_file}')
    set_config('scheduler.fields_file', fields_file, port=static_config_port)

    # TODO(wtgee): determine if we need separate directories for each module.
    logger.info(f'Setting temporary image directory for testing')
    set_config('directories.images', images_dir, port=static_config_port)

    yield
    logger.critical(f'Killing config_server started with PID={proc.pid}')
    proc.terminate()


@pytest.fixture(scope='function')
def dynamic_config_server(config_host, config_port, config_path, images_dir, db_name):
    """If a test requires changing the configuration we use a function-scoped testing
    server. We only do this on tests that require it so we are not constantly starting and stopping
    the config server unless necessary.  To use this, each test that requires it must use the
    `dynamic_config_server` and `config_port` fixtures and must pass the `config_port` to all
    instances that are created (propogated through PanBase).
    """

    logger = get_root_logger()
    logger.critical(f'Starting config_server for testing function')

    proc = config_server(
        host=config_host,
        port=config_port,
        config_file=config_path,
        ignore_local=True,
    )

    logger.info(f'config_server started with PID={proc.pid}')

    # Give server time to start
    time.sleep(1)

    # Adjust various config items for testing
    unit_name = 'Generic PANOPTES Unit'
    unit_id = 'PAN000'
    logger.info(f'Setting testing name and unit_id to {unit_id}')
    set_config('name', unit_name, port=config_port)
    set_config('pan_id', unit_id, port=config_port)

    logger.info(f'Setting testing database to {db_name}')
    set_config('db.name', db_name, port=config_port)

    fields_file = 'simulator.yaml'
    logger.info(f'Setting testing scheduler fields_file to {fields_file}')
    set_config('scheduler.fields_file', fields_file, port=config_port)

    # TODO(wtgee): determine if we need separate directories for each module.
    logger.info(f'Setting temporary image directory for testing')
    set_config('directories.images', images_dir, port=config_port)

    yield
    logger.critical(f'Killing config_server started with PID={proc.pid}')
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
    return PanDB(
        db_type=db_type, db_name='panoptes_testing', logger=get_root_logger(), connect=True)


@pytest.fixture(scope='function')
def memory_db():
    PanDB.permanently_erase_database(
        'memory', 'panoptes_testing', really='Yes', dangerous='Totally')
    return PanDB(db_type='memory', db_name='panoptes_testing')


# -----------------------------------------------------------------------
# Messaging support fixtures. It is important that tests NOT use the same
# ports that the real pocs_shell et al use; when they use the same ports,
# then tests may cause errors in the real system (e.g. by sending a
# shutdown command).


@pytest.fixture(scope='module')
def messaging_ports():
    # Some code (e.g. POCS._setup_messaging) assumes that sub and pub ports
    # are sequential so these need to match that assumption for now.
    return dict(msg_ports=(43001, 43002), cmd_ports=(44001, 44002))


@pytest.fixture(scope='function')
def message_forwarder(messaging_ports):
    cmd = shutil.which('panoptes-messaging-hub')
    assert cmd is not None
    args = [cmd]
    # Note that the other programs using these port pairs consider
    # them to be pub and sub, in that order, but the forwarder sees things
    # in reverse: it subscribes to the port that others publish to,
    # and it publishes to the port that others subscribe to.
    for _, (sub, pub) in messaging_ports.items():
        args.append('--pair')
        args.append(str(sub))
        args.append(str(pub))

    logger = get_root_logger()
    logger.info('message_forwarder fixture starting: {}', args)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # It takes a while for the forwarder to start, so allow for that.
    # TODO(jamessynge): Come up with a way to speed up these fixtures.
    time.sleep(3)
    # If message forwarder doesn't start, tell us why.
    if proc.poll() is not None:
        outs, errs = proc.communicate(timeout=5)
        logger.info(f'outs: {outs!r}')
        logger.info(f'errs: {errs!r}')
        assert False

    yield messaging_ports
    # Make sure messager forwarder is still running at end.
    assert proc.poll() is None

    # Try to terminate, then communicate, then kill.
    try:
        proc.terminate()
        outs, errs = proc.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()

    # Make sure message forwarder was killed.
    assert proc.poll() is not None


@pytest.fixture(scope='function')
def msg_publisher(message_forwarder):
    port = message_forwarder['msg_ports'][0]
    publisher = PanMessaging.create_publisher(port)
    yield publisher
    publisher.close()


@pytest.fixture(scope='function')
def msg_subscriber(message_forwarder):
    port = message_forwarder['msg_ports'][1]
    subscriber = PanMessaging.create_subscriber(port)
    yield subscriber
    subscriber.close()


@pytest.fixture(scope='function')
def cmd_publisher(message_forwarder):
    port = message_forwarder['cmd_ports'][0]
    publisher = PanMessaging.create_publisher(port)
    yield publisher
    publisher.close()


@pytest.fixture(scope='function')
def cmd_subscriber(message_forwarder):
    port = message_forwarder['cmd_ports'][1]
    subscriber = PanMessaging.create_subscriber(port)
    yield subscriber
    subscriber.close()


@pytest.fixture(scope='function')
def save_environ():
    old_env = copy.deepcopy(os.environ)
    yield
    os.environ = old_env


@pytest.fixture(scope='session')
def data_dir():
    return os.path.join(os.getenv('PANDIR'), 'panoptes-utils', 'panoptes/utils', 'tests', 'data')


@pytest.fixture(scope='session')
def unsolved_fits_file(data_dir):
    return os.path.join(data_dir, 'unsolved.fits')


@pytest.fixture(scope='session')
def solved_fits_file(data_dir):
    return os.path.join(data_dir, 'solved.fits.fz')


@pytest.fixture(scope='session')
def tiny_fits_file(data_dir):
    return os.path.join(data_dir, 'tiny.fits')


@pytest.fixture(scope='session')
def noheader_fits_file(data_dir):
    return os.path.join(data_dir, 'noheader.fits')
