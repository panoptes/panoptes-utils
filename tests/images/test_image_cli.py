from typer.testing import CliRunner

from panoptes.utils.cli.image import fits_app

runner = CliRunner()


def test_solve_cli(unsolved_fits_file):
    print(f'Testing {unsolved_fits_file}')
    result = runner.invoke(fits_app, [str(unsolved_fits_file)])
    print(result)
    assert result.exit_code == 0
    assert 'Plate-solved file available at' in result.stdout
