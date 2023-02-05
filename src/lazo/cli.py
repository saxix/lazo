#!/usr/bin/env python
import os
import sys
import warnings

import click
from urllib3.exceptions import InsecureRequestWarning

from . import __version__
from .exceptions import ExBadParameter
from .params import (
    _global_options,
    _rancher_options,
    all_envs,
    make_option,
    options,
)

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
warnings.simplefilter("ignore", InsecureRequestWarning)


class MyCLI(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        self.debug = False
        super().__init__(name, commands, **attrs)


def display(value):
    if value is None:
        return ""
    return str(value)


PROTECTED = ["RANCHER_AUTH"]


@click.group(
    context_settings=CONTEXT_SETTINGS,
    cls=MyCLI,
    invoke_without_command=True,
    no_args_is_help=True,
)
@click.version_option(__version__)
@make_option("--env", is_flag=True, is_eager=True)
@options(_global_options, _rancher_options)
@click.pass_context
def cli(ctx, env, base_url, insecure, auth, use_names, debug, **kwargs):
    if env:
        click.echo(f"{'Env':<20} Value")
        for i, opt in sorted(all_envs.items()):
            value = os.environ.get(i, "--not set--")
            click.echo(f"{i:<20} {value:<30}")
        sys.exit(0)

    if not base_url:
        raise ExBadParameter(
            "Invalid url. Should be something like 'https://rancher.example.com:9000/v3/'"
        )
    from .clients import RancherClient

    ctx.obj = {
        "client": RancherClient(
            base_url, auth=auth, verify=not insecure, use_names=use_names, debug=debug
        )
    }
