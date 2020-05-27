import pytest

from panoptes.utils import error


def test_error(capsys, caplog):
    with pytest.raises(error.PanError) as e_info:
        raise error.PanError(msg='Testing message')

    assert str(e_info.value) == 'PanError: Testing message'

    with pytest.raises(error.PanError) as e_info:
        raise error.PanError()

    assert str(e_info.value) == 'PanError'

    with pytest.raises(SystemExit) as e_info:
        raise error.PanError(msg="Testing exit", exit=True)
    assert e_info.type == SystemExit
    assert caplog.records[-1].message == 'TERMINATING: Testing exit'

    with pytest.raises(SystemExit) as e_info:
        raise error.PanError(exit=True)
    assert e_info.type == SystemExit
    assert caplog.records[-1].message == 'TERMINATING: No reason specified'
