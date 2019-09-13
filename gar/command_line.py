import sys
import os
import logging
from pathlib import Path
import click
from .core import copy, gcopy, verify
from .logger import setup_logger, logfilepath
from .lock import SimpleFileLock
from .utils import getgid


class Cli(object):
    def __init__(self, debug=False):
        # get root logger
        self.logger = logging.getLogger("gar")
        # set default debug
        self.debug = debug
        if debug:
            self.logger.setLevel(logging.DEBUG)
        fh = setup_logger()
        self.logger.addHandler(fh)

    def setDegug(self, debug):
        if debug:
            self.logger.setLevel(logging.DEBUG)


pass_cli = click.make_pass_decorator(Cli, ensure=True)


@click.group()
@click.option("--debug/-d", is_flag=True, show_default=True, default=False)
@click.pass_context
def cli(ctx, debug):
    "Write description here"
    ctx.obj = Cli(debug=debug)


def isvalidgroup(group):
    import grp
    groups = [g.gr_name for g in grp.getgrall()]
    if group not in groups:
        raise click.ClickException(f"Group '{group}' doesn't exist?")
    return group


__epilog = "Examples:\n\n"\
           "gar copy groupname /path/to/src /path/to/dest"
__shorthelp = "Copy files and directories for a group"


@cli.command(name='copy', short_help=__shorthelp,
             epilog=__epilog)
@click.argument("group", type=isvalidgroup)
@click.argument("src", type=click.Path(exists=True))
@click.argument("dst", type=click.Path(exists=True))
@click.option("--debug/-d", is_flag=True, show_default=True, default=False)
@pass_cli
def cli_copy(cli_class, group, src, dst, debug):
    """Archive copy
    Copies files and directories for a group from src to dst
    retaining owner, permissions, and attributes of files and
    directories.

    """
    if Path(src).resolve() == Path(dst).resolve():
        raise click.ClickException(f"src: {src} and dst: {dst} are same?")
    cli_class.setLevel(debug) if not debug == cli_class.debug else None
    lockfile = f"gar.{getgid(group)}.lock"
    #if (lockpath / lockfile).exists():
    #    raise click.ClickException("Another process for group: {group} running?")
    # ensure lock file doesn't exist.
    with SimpleFileLock(lockfile):
        gcopy(group, src, dst, logger=cli_class.logger)
    click.echo(f"See log file for errors {logfilepath/'gar.log'}")

@cli.command(name="verify")
@click.argument("src", type=click.Path(exists=True))
@click.argument("dst", type=click.Path(exists=True))
def cli_verify(src, dst):
    """ Verifies integrity of an archive by comparing
    src to dst.
    """
    if Path(src).resolve() == Path(dst).resolve():
        raise click.ClickException(f"src: {src} and dst: {dst} are same?")
    compare = verify(src, dst)
    for k in compare:
        for v in compare[k]:
            print(k, v, sep=": ", file=sys.stdout)

if __name__ == "__main__":
    cli()
