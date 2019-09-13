import os
from pathlib import Path
import shutil
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

    result = runner.invoke(cli, ["verify", "--help"])
    assert result.exit_code == 0


def test_command_line_copy(tempdirwithfiles):
    runner = CliRunner()
    user = os.getlogin() or os.getenv("USER")
    print(user)
    td = Path(tempdirwithfiles.name)
    td.mkdir()
    result = runner.invoke(cli, ["copy", user,
                                 str(tempdirwithfiles), str(td)])
    assert result.exit_code == 0

    # check if verify works
    result = runner.invoke(cli, ["verify", str(tempdirwithfiles), str(td)])
    print(result.output)
    assert result.exit_code == 0

    shutil.rmtree(td)