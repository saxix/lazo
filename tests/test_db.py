from click.testing import CliRunner

from lazo.commands.rancher import rancher


def test_rancher():
    runner = CliRunner()
    result = runner.invoke(rancher)
    assert result.exit_code == 0

