import os
import pytest

from panoptes.utils.logger import get_root_logger


def test_root_logger(caplog, tmp_path):
    logger = get_root_logger(log_dir=str(tmp_path))
    logger.debug('Hi')
    assert os.listdir(tmp_path)[0].startswith('panoptes_')
    assert caplog.records[-1].message == 'Hi'
    assert caplog.records[-1].levelname == 'DEBUG'

    os.environ['PANLOG'] = str(tmp_path)
    logger = get_root_logger(log_file='foo.log')
    logger.info('Bye', extra=dict(foo='bar'))
    assert len(os.listdir(tmp_path)) == 2
    assert os.listdir(tmp_path)[-1] == 'foo.log'
    assert caplog.records[-1].message == 'Bye'
    assert caplog.records[-1].levelname == 'INFO'
