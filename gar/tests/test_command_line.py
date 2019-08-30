import os
import tempfile
from click.testing import CliRunner
from gar.command_line import cli
# from gar.logger import logfilepath
# from gar.utils import hash_cp_stat


def test_command_line_invoke():
    """ Tests invocation of command gar,
    gar copy and gar move with --help.
    TODO: do an assert on output too
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--help", "--debug"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--help", "-d"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["copy", "--help"])
    assert result.exit_code == 0

    # result = runner.invoke(cli, ["move","--help"])
    # assert result.exit_code == 0
