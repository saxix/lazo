from click.testing import CliRunner

from lazo.cli import cli
from lazo.rancher import info


def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0


def test_venv():
    runner = CliRunner()
    result = runner.invoke(cli, "--env")
    assert result.exit_code == 0

    result = runner.invoke(cli, "--env", env={"DOCKER_REPOSITORY": "aa"})
    assert result.exit_code == 0


def test_info(mocked_responses):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-b", "https://rancher/v3", "info", "-p", "test"],
        env={"RANCHER_CLUSTER": "local"},
    )
    assert result.exit_code == 0, result.output
