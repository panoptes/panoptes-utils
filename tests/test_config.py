import os
from panoptes.utils.serializers import to_yaml
from panoptes.utils import config


def test_load_config(config_path):
    """Test basic loading"""
    conf = config.load_config(config_files=config_path)
    assert conf['name'] == 'Testing PANOPTES Unit'


def test_load_config_custom_file(tmp_path):
    """Test with a custom file"""
    temp_conf_text = dict(name='Temporary Name', location=dict(elevation=1234.56))

    temp_conf_file = tmp_path / 'temp_conf.yaml'
    temp_conf_local_file = tmp_path / 'temp_conf_local.yaml'

    temp_conf_file.write_text(to_yaml(temp_conf_text))

    temp_conf_text['name'] = 'Local Name'
    temp_conf_local_file.write_text(to_yaml(temp_conf_text))

    temp_config = config.load_config(str(temp_conf_file.absolute()), ignore_local=True)
    assert len(temp_config) == 2
    assert temp_config['name'] == 'Temporary Name'
    assert isinstance(temp_config['location'], dict)

    temp_config = config.load_config(str(temp_conf_local_file.absolute()), ignore_local=False)
    assert len(temp_config) == 2
    assert temp_config['name'] == 'Local Name'
    assert isinstance(temp_config['location'], dict)


def test_save_config_custom_file(tmp_path):
    """Test saving with a custom file"""
    temp_conf_file = tmp_path / 'temp_conf.yaml'

    config.save_config(str(temp_conf_file), dict(foo=1, bar=2), overwrite=False)

    temp_local = str(temp_conf_file).replace('.yaml', '_local.yaml')
    assert os.path.exists(temp_local)

    temp_config = config.load_config(str(temp_conf_file), ignore_local=True)
    assert temp_config == dict()

    temp_config = config.load_config(str(temp_conf_file), ignore_local=False)
    assert temp_config['foo'] == 1
