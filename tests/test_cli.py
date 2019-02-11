from click.testing import CliRunner

from lazo.__cli__ import cli


def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0


def test_venv():
    runner = CliRunner()
    result = runner.invoke(cli, '--env')
    assert result.exit_code == 0


    result = runner.invoke(cli, '--env', env={'DOCKER_REPOSITORY': 'aa'})
    assert result.exit_code == 0



def test_defaults():
    runner = CliRunner()
    result = runner.invoke(cli, '--defaults')
    assert result.exit_code == 0


    result = runner.invoke(cli, '--defaults', env={'DOCKER_REPOSITORY': 'aa'})
    assert result.exit_code == 0
