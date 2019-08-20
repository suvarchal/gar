import click
from .copy import copy


@click.command()
@click.argument("src")
@click.argument("dst")
def cli_copy(src, dst):
    """ Copies files and directories """
    click.echo("{src}:{dst}".format(src=src, dst=dst))
    copy(src, dst)
    # print(copy.__doc__)
