from panoptes.utils.serializers import to_yaml
from panoptes.utils import config


def test_load_config():
    """Test basic loading"""
    conf = config.load_config()
    assert conf['name'] == 'Generic PANOPTES unit'


def test_load_config_custom_file(tmp_path):
    """Test with a custom file"""
    temp_conf_text = to_yaml(dict(name='Temporary Name', location=dict(elevation=1234.56)))

    temp_conf_file = tmp_path / 'temp_conf.yaml'
    temp_conf_file.write_text(temp_conf_text)

    temp_config = config.load_config(str(temp_conf_file.absolute()))
    assert len(temp_config) == 2
    assert temp_config['name'] == 'Temporary Name'
    assert isinstance(temp_config['location'], dict)
