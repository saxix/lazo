import sys
from functools import partial

import click


def secho(*args, fg="white", indent=0):
    prefix = " " * indent
    click.secho(prefix + " ".join(map(str, args)), fg=fg)


def fail(*args):
    secho(*args, fg="red")
    sys.exit(1)


echo = partial(secho, fg="white")
success = partial(secho, fg="green")
warn = partial(secho, fg="orange")
error = partial(secho, fg="red")
# click.echo(click.style('Hello World!', fg='green'))
