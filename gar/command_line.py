import sys
import os
import logging
import click
from .core import copy
from .logger import setup_logger
from .lock import SimpleFileLock


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

    @staticmethod
    def Lock(group):
        yield from SimpleFileLock(f"gar.{group}.lock")


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


__epilog = "Examples:\n"\
           "\tgar copy groupname /path/to/src /path/to/dest"
__shorthelp = "Copy files and directories for a group"


@cli.command(name='copy', help="copy help",
             short_help=__shorthelp,
             epilog=__epilog)
@click.argument("src")
@click.argument("dst")
@click.option("--debug/-d", is_flag=True, show_default=True, default=False)
@pass_cli
def cli_copy(cli, src, dst, debug):
    """Archive copy
    Copies files and directories for a group from src to dst
    retaining owner, permissions, and attributes of files and
    directories.

    """
    cli.setLevel(debug) if not debug == cli.debug else None
    click.echo("{src}:{dst} debug{debug}".format(src=src, dst=dst))
    with cli.Lock("temp"):
        copy(src, dst)
