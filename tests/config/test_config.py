from pathlib import Path

import pytest
from astropy import units as u

from panoptes.utils.config.helpers import load_config
from panoptes.utils.config.helpers import save_config
from panoptes.utils.serializers import to_yaml


def test_load_config(config_path):
    """Test basic loading"""
    conf = load_config(config_files=config_path)
    assert conf['name'] == 'Testing PANOPTES Unit'


def test_load_config_custom_file(tmp_path):
    """Test with a custom file"""
    temp_conf_text = dict(name='Temporary Name', location=dict(elevation='1234.56 m'))

    temp_conf_file = tmp_path / 'temp_conf.yaml'
    temp_conf_local_file = tmp_path / 'temp_conf_local.yaml'

    temp_conf_file.write_text(to_yaml(temp_conf_text))

    temp_conf_text['name'] = 'Local Name'
    temp_conf_local_file.write_text(to_yaml(temp_conf_text))

    # Ignore the local name
    temp_config = load_config(temp_conf_file.absolute(), load_local=False)
    assert len(temp_config) == 2
    assert temp_config['name'] == 'Temporary Name'
    assert temp_config['location']['elevation'] == 1234.56 * u.m
    assert isinstance(temp_config['location'], dict)

    # Load the local
    temp_config = load_config(temp_conf_local_file.absolute(), load_local=True)
    assert len(temp_config) == 2
    assert temp_config['name'] == 'Local Name'
    assert temp_config['location']['elevation'] == 1234.56 * u.m
    assert isinstance(temp_config['location'], dict)

    # Reload the local but don't parse, load_local is default.
    temp_config = load_config(temp_conf_file.absolute(), parse=False)
    assert len(temp_config) == 2
    assert temp_config['name'] == 'Local Name'
    assert temp_config['location']['elevation'] == '1234.56 m'
    assert isinstance(temp_config['location'], dict)


def test_save_config_custom_file(tmp_path):
    """Test saving with a custom file"""
    temp_conf_file = tmp_path / 'temp_conf.yaml'

    save_config(temp_conf_file, dict(foo=1, bar=2), overwrite=False)

    assert Path(tmp_path / 'temp_conf_local.yaml').exists()

    temp_config = load_config(temp_conf_file, load_local=True)
    assert temp_config['foo'] == 1

    temp_config = load_config(temp_conf_file, load_local=False)
    assert temp_config == dict()

    with pytest.raises(FileExistsError):
        save_config(temp_conf_file, dict(foo=2, bar=2), overwrite=False)

    save_config(temp_conf_file, dict(foo=2, bar=2), overwrite=True)
    temp_config = load_config(temp_conf_file)
    assert temp_config['foo'] == 2


def test_save_config_custom_local_file(tmp_path):
    """Test saving with a custom file"""
    temp_conf_file = tmp_path / 'temp_conf.yaml'
    temp_conf_local_file = tmp_path / 'temp_conf_local.yaml'

    # Save the local directly.
    assert temp_conf_local_file.exists() is False
    save_config(temp_conf_local_file, dict(foo=1, bar=2), overwrite=False)
    assert temp_conf_local_file.exists()

    temp_config = load_config(temp_conf_file, load_local=False)
    assert temp_config == dict()

    temp_config = load_config(temp_conf_file)
    assert temp_config['foo'] == 1
