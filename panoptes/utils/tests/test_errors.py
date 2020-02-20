import pytest

from panoptes.utils import error


def test_error(capsys):
    with pytest.raises(error.PanError) as e_info:
        raise error.PanError(msg='Testing message')

    assert str(e_info.value) == 'PanError: Testing message'

    with pytest.raises(error.PanError) as e_info:
        raise error.PanError()

    assert str(e_info.value) == 'PanError'

    with pytest.raises(SystemExit) as e_info:
        raise error.PanError(msg="Testing exit", exit=True)
    assert e_info.type == SystemExit
    assert capsys.readouterr().out.strip() == 'TERMINATING: Testing exit'

    with pytest.raises(SystemExit) as e_info:
        raise error.PanError(exit=True)
    assert e_info.type == SystemExit
    assert capsys.readouterr().out.strip() == 'TERMINATING: No reason specified'
